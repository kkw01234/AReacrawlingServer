from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import requests
import time
import pymongo
from bs4 import BeautifulSoup
import datetime

# ------------------하이퍼 파라미터---------------------------
id = 'sohwakhang_studio'  # 인스타그램 아이디
password = 'rjsdnrkkw4809!!'  # 인스타그램 패스워드
 # 검색 단어
driver_path = 'C:/Users/gny32/OneDrive/바탕 화면/chromedriver'  # 크롬드라이버 위치
key = ''  # 구글 API KEY
server_ip = '118.220.3.71'  # 몽고 DB 서버 IP address


# --------------------지오 코딩------------------------------
def get_r_info(keyword):
    global key
    headers = {'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'}
    base_url = "https://maps.googleapis.com/maps/api/geocode/xml?"
    url = base_url + 'address=' + keyword + '&key=' + key
    resp = requests.get(url, headers=headers)
    html = BeautifulSoup(resp.content, 'lxml')
    place_id = html.select('place_id')
    lat = html.select('location > lat')
    lng = html.select('location > lng')
    addr = html.select('result > formatted_address')
    print('<', keyword, '>')
    print('place_id :', place_id[0].get_text())
    print('address :', addr[0].get_text())
    print('lat :', lat[0].get_text())
    print('lng :', lng[0].get_text())
    return place_id[0].get_text(), addr[0].get_text(), lat[0].get_text(), lng[0].get_text()


# -------------------몽고 디비 관련 함수 ---------------------
def data_format(place_id,keyword, addr, lat, lng, name, comment, date):
    return {
        'place_id': place_id,
        'r_name': keyword,
        'r_addr': addr,
        'r_lat': lat,
        'r_lng': lng,
        'name': name,
        'comment': comment,
        'date': date,
        'rate': -1,
        'location': ''
    }


# --------------------인스타그램 크롤링----------------------
def instagram_crawling(keyword, last):
    global id, password, driver_path, server_ip

    conn = pymongo.MongoClient(server_ip, 27017)
    db = conn.crawling

    place_id, addr, lat, lng = get_r_info(keyword)

    driver = webdriver.Chrome(driver_path)
    driver.implicitly_wait(3)
    driver.get('https://www.instagram.com/accounts/login/')
    driver.find_element_by_name('username').send_keys(id)
    driver.find_element_by_name('password').send_keys(password)
    driver.find_element_by_class_name('L3NKy').click()
    try:  # 어플 다운로드 광고 페이지 넘기기
        driver.find_element_by_class_name('_7XMpj').click()
    except NoSuchElementException:
        pass
    try:  # 알림 설정 팝업 넘기기
        driver.find_element_by_class_name('HoLwm').click()
    except NoSuchElementException:
        pass

    driver.find_element_by_class_name('x3qfX').send_keys(keyword)
    searches = driver.find_elements_by_class_name('z556c')
    for curr in searches:
        try:
            curr.find_element_by_class_name('coreSpriteLocation')
        except NoSuchElementException:
            continue
        curr.find_element_by_class_name('Ap253').click()
        time.sleep(10)
        with open(keyword + '.txt', 'w', encoding='UTF-8') as f:
            driver.find_element_by_class_name('_9AhH0').click()
            driver.implicitly_wait(1)
            count = 0
            while True:
                if count == 2:
                    try:
                        count = 0
                        driver.find_element_by_class_name('coreSpriteRightPaginationArrow').click()
                    except NoSuchElementException:
                        break
                try:
                    driver.find_element_by_class_name('_97aPb')
                except NoSuchElementException:
                    count += 1
                    time.sleep(1)
                    continue
                try:
                    name = driver.find_element_by_class_name('nJAzx').text
                    comment = driver.find_element_by_class_name('PpGvg').find_element_by_tag_name('span').text
                    date = driver.find_element_by_class_name('_1o9PC').text
                    db.instagram.insert_one(data_format(place_id, keyword, addr, lat, lng, name, comment, date))
                except NoSuchElementException:
                    pass
                try:
                    driver.find_element_by_class_name('coreSpriteRightPaginationArrow').click()
                    count = 0
                except NoSuchElementException:
                    break
        break
    driver.close()


# ------------------ 테스트 부분 ----------------------------
if __name__=='__main__':
    instagram_crawling('생고기제작소 경기대점', datetime.datetime.now().replace(year=1950,month=1,day=1).date())