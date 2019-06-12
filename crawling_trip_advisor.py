from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import requests
import re
import time
import pymongo
from bs4 import BeautifulSoup

# ------------------하이퍼 파라미터---------------------------
local = '강남'  # 검색 지역 단어
driver_path = 'C:/Users/gny32/OneDrive/바탕 화면/chromedriver'  # 크롬드라이버 위치
key = 'AIzaSyDGUj-frLFa_pp5Jer5IKWUfRv1tQ-mrJI'  # 구글 API KEY
server_ip = '118.220.3.71'  # 몽고 DB 서버 IP address


# --------------------지오 코딩------------------------------
def get_r_info(keyword):
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

        for i in range(0, len(addr)):
            if addr[i].find(keyword):
                print(addr[i])
                ans = i
                break

        print('place_id :', place_id[ans].get_text())
        print('address :', addr[ans].get_text())
        print('lat :', float(lat[ans].get_text()))
        print('lng :', float(lng[ans].get_text()))
    except:
        return 'None', 'None', 'None', 'None'
    return place_id[ans].get_text(), addr[ans].get_text(), float(lat[ans].get_text()), float(lng[ans].get_text())


# -------------------몽고 디비 관련 함수 ---------------------
def data_format(place_id, keyword, addr, lat, lng, name, comment, rate, date, location):
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


# --------------------트립어드바이저 코드 크롤링----------------------
# keyword : 크롤링할 지역 값, last : 그 전 마지막 날짜
def trip_advisor_crawling(keyword, last):
    global driver_path, server_ip
    conn = pymongo.MongoClient(server_ip, 27017)
    db = conn.crawling

    driver = webdriver.Chrome(driver_path)
    def load_chrome():
        driver.implicitly_wait(3)
        driver.get('https://www.tripadvisor.co.kr/Search?ssrc=e&q=' + keyword)
        time.sleep(1)  # 검색 및 기다리기
        driver.find_element_by_id('GEO_SCOPED_SEARCH_INPUT').clear()
        time.sleep(1)  # 검색 및 기다리기
        driver.find_element_by_id('GEO_SCOPED_SEARCH_INPUT').send_keys('대한민국, 아시아')
        time.sleep(2)  # 검색 및 기다리기
        driver.find_element_by_id('SEARCH_BUTTON').click()
        time.sleep(2)  # 검색 및 기다리기
    load_chrome()
    rests = []
    p = re.compile('/Restaurant_Review.+html')
    i= 0
    while True:
        try:
            finds = driver.find_elements_by_class_name('result-card')
        except:
            break
        for find in finds:
            try:
                find.find_element_by_class_name('ad')  # 광고 관련 항목 제외시키기
            except:  # ad 클래스를 가지고 있지 않다면, 광고가 아니므로 예외로 들어온다
                script = find.find_element_by_class_name('result-title').get_attribute('onclick')
                result = p.findall(script)
                rests.append('https://www.tripadvisor.co.kr/' + result[0])
        print(rests)
        try: #다음 버튼이 없을 경우
            next_button = driver.find_element_by_class_name('next')
            if 'disabled' in next_button.get_attribute('class'):
                break
            next_button.click()
        except: #코드 수정 ( 없는데이터라고 뜰경우 다시 3번 검색 시도)
            i = i + 1
            if i <= 3:
                load_chrome()
                continue
            else:
                break
    for rest in rests:  # 수집한 식당 URL 하나하나 들어가기
        driver.get(rest)
        r_name = driver.find_element_by_class_name('ui_header').text
        id, addr, lat, lng = get_r_info(r_name)
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
                    db.trips.insert_one(data_format(id, r_name, addr, lat, lng, name, comment, rate, date, keyword))
            try:  # 리뷰의 다음 페이지가 있다면 다음 버튼 눌러주기
                next_button = driver.find_element_by_id('REVIEWS').find_element_by_class_name('next')
                if 'disabled' in next_button.get_attribute('class'):
                    break
                next_button.click()
            except:
                break


# -----------TEST----------------------------
if __name__ == '__main__':
    trip_advisor_crawling(local,datetime.now().replace(year=1950, month=1, day=1).date())
