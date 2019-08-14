from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import datetime

import requests
import time
import pymongo
from bs4 import BeautifulSoup

# ------------------하이퍼 파라미터---------------------------
local = '강남'  # 검색 지역 단어
driver_path = 'C:/Users/gny32/OneDrive/바탕 화면/chromedriver'  # 크롬드라이버 위치
key = ''  # 구글 API KEY
server_ip = '118.220.3.71'  # 몽고 DB 서버 IP address


# --------------------지오 코딩------------------------------
def get_r_info(keyword, m):
    global key
    try:
        headers = {'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'}
        base_url = "https://maps.googleapis.com/maps/api/geocode/xml?"
        url = base_url + 'address=' + keyword + '&key=' + key
        print(url)
        resp = requests.get(url, headers=headers)
        html = BeautifulSoup(resp.content, 'lxml')
        place_id = html.select('place_id')
        lat = html.select('location > lat')
        lng = html.select('location > lng')
        addr = html.select('result > formatted_address')
        print('<', keyword, '>')
        ans = 0
        # r_lat = round(float(m['lat']), 2)
        # r_lng = round(float(m['lng']), 2)
        # print(len(lat))
        # print(range(0, len(lat)))
        # for i in range(0, len(lat)):
            # print(r_lat," ",round(lat[i], 2)," ",r_lng," ",round(lng[i], 2))
            # if round(lat[i], 2) == r_lat and round(lng[i], 2) == r_lng:
            #     ans = i
            #     break

        print(ans)
        print('place_id :', place_id[ans].get_text())
        print('address :', addr[ans].get_text())
        print('lat :', float(lat[ans].get_text()))
        print('lng :', float(lng[ans].get_text()))
    except:
        return 'None', 'None', 'None', 'None'
    return place_id[ans].get_text(), addr[ans].get_text(), float(lat[ans].get_text()), float(lng[ans].get_text())


# -------------------몽고 디비 관련 함수 ---------------------
def data_format(place_id, keyword, addr, lat, lng, name, comment, rate, date,location):
    return {
        'place_id': place_id,
        'r_name': keyword,
        'r_addr': addr,
        'r_lat': lat,
        'r_lng': lng,
        'name': name,
        'comment': comment,
        'rate': rate,
        'date': date,
        'location': location
    }


# --------------------다이닝 코드 크롤링----------------------
# keyword : 크롤링할 지역 값, last : 그 전 마지막 날짜
def dining_code_crawling(keyword, last):
    global driver_path, server_ip
    conn = pymongo.MongoClient(server_ip, 27017)
    db = conn.crawling

    driver = webdriver.Chrome(driver_path)
    driver.implicitly_wait(3)
    driver.get('https://www.diningcode.com/list.php?query=' + keyword)
    last_li = 0
    while True:
        driver.execute_script('getMoreList()')
        time.sleep(1)
        lis = driver.find_element_by_id('div_list').find_elements_by_tag_name('li')
        curr_li = len(lis)
        if curr_li == last_li:
            break
        last_li = curr_li
    r_ids = []

    for li in lis:
        if 'partner' in li.find_element_by_tag_name('a').get_attribute('href'):
            continue
        r_ids.append(li.find_element_by_tag_name('a').get_attribute('href'))
    j_map = driver.execute_script('return jMap')
    print(j_map)
    for r_id in r_ids:
        try:
            driver.get(r_id)
        except:
            continue
        try:
            r_name = driver.find_element_by_class_name('tit-point').text
            place_id, addr, lat, lng = get_r_info(r_name, None)
            if place_id == 'None':
                continue
        except:
            continue
        while True:
            try:
                if '평가' in driver.find_element_by_id('div_more_review').text:
                    break
                driver.find_element_by_id('div_more_review').click()
                time.sleep(1)
            except:
                break
        try:
            reviews = driver.find_element_by_id('div_review_back').find_elements_by_class_name('latter-graph')
        except:
            continue
        for review in reviews:
            name = review.find_element_by_class_name('person-grade').find_element_by_tag_name('strong').text
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
            comment = review.find_element_by_class_name('review_contents').text
            star = review.find_element_by_class_name('star').find_element_by_tag_name('i').get_attribute('style')
            rate = int(star[7:-2]) / 20
            if datetime.datetime.strptime(date, "%Y-%m-%d").date() > last:
                db.dining_code.insert_one(data_format(place_id, r_name, addr, lat, lng, name, comment, rate, date, keyword))

<<<<<<< HEAD

if __name__=='__main__':
    dining_code_crawling('영통구 이의동', datetime.datetime.now().replace(year=1950, month=1, day=1).date())
=======
if __name__=='__main__':
    dining_code_crawling('', datetime.now().replace(year=1950, month=1, day=1).date())
>>>>>>> 3da96042024c2355bcfc990a7de2ea5fd204b124
