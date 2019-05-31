from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import datetime
import requests
import time
import pymongo
import pymysql
from bs4 import BeautifulSoup
from restaurant_crawling import restaurant_common

# ------------------하이퍼 파라미터---------------------------
local = '강남'  # 검색 지역 단어
driver_path = 'C:/Users/gny32/OneDrive/바탕 화면/chromedriver'  # 크롬드라이버 위치
key = 'AIzaSyDGUj-frLFa_pp5Jer5IKWUfRv1tQ-mrJI'  # 구글 API KEY
server_ip = '118.220.3.71'  # 몽고 DB 서버 IP address


# --------------------다이닝 코드 크롤링----------------------
# keyword : place_id, last : 그 전 마지막 날짜
def dining_code_crawling(place_id, last):
    global driver_path, server_ip
    conn = pymongo.MongoClient(server_ip, 27017)
    db = conn.crawling
    r_name, r_addr, r_lat, r_lng = restaurant_common.get_r_info(place_id)
    driver = webdriver.Chrome(driver_path)
    driver.implicitly_wait(3)
    driver.get('https://www.diningcode.com/list.php?query=' + r_name+'&rn=1')
    lis = driver.find_element_by_id('div_list')
    a_href = lis.find_elements_by_tag_name('a')

    jMap = driver.execute_script('return jMap')
    count = 0
    for m in jMap:
        lat = round(float(m['lat']), 3)
        lng = round(float(m['lng']), 3)
        print(str(lat)+' '+str(lng)+' '+str(round(r_lat, 3))+' '+str(round(r_lng, 3)))
        if round(r_lat, 3) == lat and round(r_lng, 3) == lng:
            break
        count += 1
    li = a_href[count+2]

    # for i, a in zip(range(0, len(a_href)), a_href):
    #   print(str(i)+': '+a.get_attribute('href'))

    print(li.get_attribute('href'))

    driver.get(li.get_attribute('href'))

    time.sleep(2)
    menu_info = driver.find_element_by_class_name('menu-info')
    menu_info.find_element_by_class_name('more-btn').click()
    menu_list = menu_info.find_element_by_class_name('list') #메뉴 저장
    menu_li = menu_list.find_elements_by_tag_name('li')
    menu = ''
    for l in menu_li:
        menu += str(l.find_element_by_class_name('l-txt').text)+" "+str(l.find_element_by_class_name('r-txt').text)+'\n'
    print(menu)
    find =False
    while True:
        try:
            driver.find_element_by_id('div_more_review').click()
        except:
            break
    try:
        reviews = driver.find_element_by_id('div_review').find_elements_by_class_name('latter-graph')
        find = True
    except:
        return
    for review in reviews:
        name = review.find_element_by_class_name('person-grade').find_element_by_class_name('btxt').find_element_by_tag_name('strong').text
        comment = review.find_element_by_class_name('review_contents').text
        star = review.find_element_by_class_name('star').find_element_by_tag_name('i').get_attribute('style')
        rate = int(star[7:-2]) / 20
        date = review.find_element_by_class_name('date').text
        if '전' in date:
            now = datetime.datetime.now()
            if '일' in date:
                differ = int(date.split('일')[0])
                now -= datetime.timedelta(days=differ)
            date = now.strftime('%Y-%m-%d'.encode('unicode-escape').decode()).encode().decode('unicode-escape')
        if '년' in date:
            date = datetime.datetime.strptime(date, '%Y년 %m월 %d일')
            date = date.strftime('%Y-%m-%d')
        if '월' in date:
            now = datetime.datetime.now()
            date = datetime.datetime.strptime(date, '%m월 %d일')
            date = str(now.year) + '-' + date.strftime('%m-%d')

        restaurant_common.update_text(place_id, menu)
        if datetime.datetime.strptime(date, "%Y-%m-%d").date() > last:
            db.rest_dining_code.insert_one(restaurant_common.data_format(place_id, r_name, r_addr, r_lat, r_lng, name, comment, rate, date, place_id))
    if find:
        driver.close()

# -----------Test------------
if __name__ =="__main__":
    place_id1 = 'ChIJa3UOgEpaezURFl9HM1drLDs'
    last1 = restaurant_common.find_last_crawling_date(place_id1)
    print(last1)
    if last1 < datetime.datetime.now().date():
        dining_code_crawling(place_id1, last1)