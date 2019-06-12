from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException
import requests
import time
from datetime import datetime, timedelta
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
        return 'None','None', 'None', 'None'
    return place_id[ans].get_text(), addr[ans].get_text(), float(lat[ans].get_text()), float(lng[ans].get_text())


# -------------------몽고 디비 관련 함수 ---------------------
def data_format(place_id,keyword, addr, lat, lng, name, comment, rate, date,location):
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
        'location' : location
    }


# --------------------망고플레이트 크롤링----------------------
# keyword : 크롤링할 지역 값, last : 그 전 마지막 날짜
def mango_plate_crawling(keyword, last):
    global driver_path, server_ip
    conn = pymongo.MongoClient(server_ip, 27017)
    db = conn.crawling

    driver = webdriver.Chrome(driver_path)
    driver.implicitly_wait(3)
    curr_page = 1
    driver.get('https://www.mangoplate.com/search/' + keyword + '?page=' + str(curr_page))  # 첫 팝업창 끄기
    while True:
        driver.get(
            'https://www.mangoplate.com/search/' + keyword + '?page=' + str(curr_page))  # 지역 키워드 검색 ex : 강남, 수원역...
        r_ids = []
        r_divs = driver.find_elements_by_class_name('only-desktop_not')
        for i in range(len(r_divs) // 2):
            div_id = r_divs[i].get_attribute('href')
            r_ids.append(div_id)
        for r_id in r_ids:
            driver.get(r_id)
            r_name = driver.find_element_by_class_name('restaurant_name').text
            place_id, addr, lat, lng = get_r_info(r_name)
            i=0
            while True:
                print(str(i))
                i+=1
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
                except: # 2 일 전으로 되있는 경우
                    if '일' in date:
                        now = datetime.now()
                        differ = int(date.split('일')[0])
                        now -= timedelta(days=differ)
                        date = now.date()
                comment = review.find_element_by_class_name('RestaurantReviewItem__ReviewContent').text
                rate_text = review.find_element_by_class_name('RestaurantReviewItem__RatingText').text
                if rate_text == '맛있다':
                    rate = 5.0
                elif rate_text == '괜찮다':
                    rate = 3.0
                elif rate_text == '별로':
                    rate = 1.0
                else: #에러났을경우 그냥 보통 점수로 계산
                    rate = 2.5
                print(date > last)
                if date > last:
                    date = date.strftime('%Y-%m-%d'.encode('unicode-escape').decode()).encode().decode('unicode-escape')
                    db.mango_plate.insert_one(data_format(place_id, r_name, addr, lat, lng, name, comment, rate, date, keyword))
        curr_page += 1
        if curr_page == 2:
            break


if __name__=='__main__':
    mango_plate_crawling('', datetime.now().replace(year=1950,month=1,day=1).date())