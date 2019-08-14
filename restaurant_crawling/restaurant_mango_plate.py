from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException
import requests
import time
from datetime import datetime, timedelta
import pymongo
from bs4 import BeautifulSoup
import json
from restaurant_crawling import restaurant_common

# ------------------하이퍼 파라미터---------------------------
local = '강남'  # 검색 지역 단어
driver_path = 'C:/Users/gny32/OneDrive/바탕 화면/chromedriver'  # 크롬드라이버 위치
server_ip = '118.220.3.71'  # 몽고 DB 서버 IP address


# --------------------Location 정보 받아오기------------------------------
def get_location(keyword, r_lat, r_lng):
    global key
    curr_page = 1
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
    while True:
        base_url = 'https://www.mangoplate.com/search/' + keyword + '?page=' + str(curr_page)
        resp = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(resp.content, 'lxml')
        search_first_result_json = soup.find('script', id='search_first_result_json').string
        if search_first_result_json is None:
            break
        t = str(search_first_result_json).strip().replace('&quot;','"')
        t2 = json.loads(t)
        count = -1
        if t2 == []:
            break

        for a,i in zip(t2, range(0,len(t2))):
            m_lat = round(float(a['restaurant']['latitude']), 2)
            m_lng = round(float(a['restaurant']['longitude']), 2)
            print(str(r_lat)+" "+str(m_lat)+" "+str(r_lat)+" "+str(r_lng))
            if round(r_lat, 2) == m_lat and round(r_lng, 2) == m_lng:
                count = i
                break
        print(count)
        if count == -1:
            curr_page += 1
            continue
        else:
            break
    return count


# --------------------망고플레이트 크롤링----------------------
# keyword : 크롤링할 지역 값, last : 그 전 마지막 날짜
def mango_plate_crawling(place_id, last):
    global driver_path, server_ip
    conn = pymongo.MongoClient(server_ip, 27017)
    db = conn.crawling
    r_name, r_addr, r_lat, r_lng = restaurant_common.get_r_info(place_id)
    count = get_location(r_name, r_lat, r_lng)
    if count == -1:
        return
    driver = webdriver.Chrome(driver_path)
    driver.implicitly_wait(3)

    driver.get('https://www.mangoplate.com/search/' + r_name)  # 첫 팝업창 끄기
    driver.get('https://www.mangoplate.com/search/' + r_name)  # 첫 팝업창 끄기
    time.sleep(3)

    r_divs = driver.find_elements_by_class_name('only-desktop_not') # 식당
    driver.get(r_divs[count].get_attribute('href'))
    time.sleep(1)
    r_name = driver.find_element_by_class_name('restaurant_name').text
    i = 0
    while True:
        print(str(i))
        i += 1
        try:
            driver.find_element_by_class_name('RestaurantReviewList__MoreReviewButton').click()  # 리뷰 더보기 계속 누르기
            time.sleep(2)
        except:
            break
    reviews = driver.find_elements_by_class_name('RestaurantReviewList__ReviewItem')
    for review in reviews:
        name = review.find_element_by_class_name('RestaurantReviewItem__UserNickName').text
        date = review.find_element_by_class_name('RestaurantReviewItem__ReviewDate').text
        try:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        except:  # 2 일 전으로 되있는 경우
            if '일' in date:
                now = datetime.now()
                differ = int(date.split('일')[0])
                now -= timedelta(days=differ)
                date = now.date()
            else:
                date = datetime.now().date()
        comment = review.find_element_by_class_name('RestaurantReviewItem__ReviewContent').text
        rate_text = review.find_element_by_class_name('RestaurantReviewItem__RatingText').text
        if rate_text == '맛있다':
            rate = 5.0
        elif rate_text == '괜찮다':
            rate = 3.0
        elif rate_text == '별로':
            rate = 1.0
        else:  # 에러났을경우 그냥 보통 점수로 계산
            rate = 2.5
        if date > last:
            date = date.strftime('%Y-%m-%d'.encode('unicode-escape').decode()).encode().decode('unicode-escape')
            db.rest_mango_plate.insert_one(restaurant_common.data_format(place_id, r_name, r_addr, r_lat, r_lng, name, comment, rate, date, place_id))
    driver.close()
    return

# -----------Test-------------
if __name__ =="__main__":
    place_id1='ChIJL4SLNNCYfDURoDGLm1cbBRM'
    #last 코드 필요
    mango_plate_crawling(place_id=place_id1, last=datetime.now().replace(year=1900,month=1,day=1).date())