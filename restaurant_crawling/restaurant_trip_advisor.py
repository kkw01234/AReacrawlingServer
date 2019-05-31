from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import requests
import re
import time
import pymongo
import traceback
from bs4 import BeautifulSoup
import json
from restaurant_crawling import restaurant_common
# ------------------하이퍼 파라미터---------------------------
local = '강남'  # 검색 지역 단어
driver_path = 'C:/Users/gny32/OneDrive/바탕 화면/chromedriver'  # 크롬드라이버 위치
key = 'AIzaSyDGUj-frLFa_pp5Jer5IKWUfRv1tQ-mrJI'  # 구글 API KEY
server_ip = '118.220.3.71'  # 몽고 DB 서버 IP address



# --------------------트립어드바이저 코드 크롤링----------------------
# keyword : 크롤링할 지역 값, last : 그 전 마지막 날짜
def trip_advisor_crawling(place_id, last):
    global driver_path, server_ip
    conn = pymongo.MongoClient(server_ip, 27017)
    db = conn.crawling
    rest_name, rest_addr, rest_lat, rest_lng = restaurant_common.get_r_info(place_id)
    driver = webdriver.Chrome(driver_path)
    def load_chrome():
        driver.implicitly_wait(3)
        driver.get('https://www.tripadvisor.co.kr/Search?ssrc=e&q=' + rest_name)
        time.sleep(1)  # 검색 및 기다리기
        driver.find_element_by_id('GEO_SCOPED_SEARCH_INPUT').clear()
        time.sleep(2)  # 검색 및 기다리기
        driver.find_element_by_id('GEO_SCOPED_SEARCH_INPUT').send_keys('대한민국, 아시아')
        time.sleep(2)  # 검색 및 기다리기
        driver.find_element_by_id('SEARCH_BUTTON').click()
        time.sleep(2)  # 검색 및 기다리기
    load_chrome()
    rests = []
    p = re.compile('/Restaurant_Review.+html')
    i = 0
    count = 0
    while True:
        print(count)
        try:
            finds = driver.find_elements_by_class_name('result-card')
        except:
            break
        ss = 0
        for find in finds:
            ss += 1
            try:
                find.find_element_by_class_name('ad')  # 광고 관련 항목 제외시키기
            except:  # ad 클래스를 가지고 있지 않다면, 광고가 아니므로 예외로 들어온다
                script = find.find_element_by_class_name('result-title').get_attribute('onclick')
                result = p.findall(script)
                print('why!!!'+str(ss))
                rests.append('https://www.tripadvisor.co.kr/' + result[0])
        if count > 2:
            break
        try: #다음 버튼이 없을 경우
            next_button = driver.find_element_by_class_name('next')
            if 'disabled' in next_button.get_attribute('class'):
                break
            count += 1
            next_button.click()
        except: #코드 수정 ( 없는데이터라고 뜰경우 다시 3번 검색 시도)
            print("???????????")
            i = i + 1
            if i <= 3:
                load_chrome()
                continue
            else:
                break

    find = False
    for rest in rests:  # 수집한 식당 URL 하나하나 들어가기
        driver.get(rest)
        print(rest)
        p = re.compile('d[0-9]*\\-')
        rest2 = p.findall(rest)
        test = driver.execute_script('return window.__WEB_CONTEXT__')
        print(rest2[0][1:-1])
        try:
            r_lat = float(test['pageManifest']['redux']['api']['responses']['/data/1.0/location/'+rest2[0][1:-1]]['data']['latitude'])
            r_lng = float(test['pageManifest']['redux']['api']['responses']['/data/1.0/location/'+rest2[0][1:-1]]['data']['longitude'])
            print(str(round(r_lat, 2)) + " " + str(round(rest_lat, 2)) + " " + str(round(rest_lng, 2)) + " " + str(round(r_lng, 2)))
        except:
            traceback.print_exc()
            continue
        if round(r_lat, 2) == round(rest_lat, 2) and round(rest_lng, 2) == round(r_lng, 2):
            print('find')
            find = True
            r_name = driver.find_element_by_class_name('ui_header').text
            while True:  # 리뷰들의 페이지를 모두 탐색하기 위한 반복문
                time.sleep(2)
                try:
                    driver.find_element_by_class_name('ulBlueLinks').click()  # 댓글 더보기 눌러주기
                except:  # 없는 경우엔 그냥 무시
                    pass
                time.sleep(2)
                reviews = driver.find_elements_by_class_name('review-container')
                print(len(reviews))
                for review in reviews:  # 현재 리뷰 페이지에 존재하는 리뷰들 양식에 맞게 크롤링하기
                    info = review.find_element_by_class_name('info_text')
                    name = info.find_element_by_tag_name('div').text
                    date = review.find_element_by_class_name('ratingDate').get_attribute('title')
                    try:
                        date = datetime.strptime(date, '%Y년 %m월 %d일')
                        date = date.strftime('%Y-%m-%d')
                    except: # 날짜가 등록되있지 않은 경우가 있음 (크롤링한 날짜로 설정)
                        date = datetime.today().strftime('%Y-%m-%d')

                    comment = review.find_element_by_class_name('noQuotes').text + ' '
                    comment += review.find_element_by_class_name('partial_entry').text
                    rate = float(review.find_element_by_class_name('ui_bubble_rating').get_attribute('class')[-2:-1])

                    print('name :', name)
                    print('date :', date)
                    print('comment :', comment)
                    print('rate :', rate)
                    if datetime.strptime(date, "%Y-%m-%d").date() > last:
                        db.rest_trip_advisor.insert_one(restaurant_common.data_format(id, rest_name, rest_addr, rest_lat, rest_lng, name, comment, rate, date, place_id))
                try:  # 리뷰의 다음 페이지가 있다면 다음 버튼 눌러주기
                    next_button = driver.find_element_by_id('REVIEWS').find_element_by_class_name('next')
                    if 'disabled' in next_button.get_attribute('class'):
                        break
                    next_button.click()
                except:
                    break
        if find:
            driver.close()
            break


# -----------TEST----------------------------
if __name__ == '__main__':
    trip_advisor_crawling('ChIJ7bKnOIiifDURVkqxTJFicrY', None)
