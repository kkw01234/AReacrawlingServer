from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import requests
import time
import pymongo
import traceback
import datetime
from bs4 import BeautifulSoup
from restaurant_crawling import restaurant_common
import re


# ------------------하이퍼 파라미터---------------------------
id = 'sohwakhang_studio'  # 인스타그램 아이디
password = 'rjsdnrkkw4809!!'  # 인스타그램 패스워드
 # 검색 단어
driver_path = 'C:/Users/gny32/OneDrive/바탕 화면/chromedriver'  # 크롬드라이버 위치
key = 'AIzaSyDGUj-frLFa_pp5Jer5IKWUfRv1tQ-mrJI'  # 구글 API KEY
server_ip = '118.220.3.71'  # 몽고 DB 서버 IP address


# --------------------인스타그램 크롤링----------------------
def instagram_crawling(place_id, last):
    global id, password, driver_path, server_ip

    conn = pymongo.MongoClient(server_ip, 27017)
    db = conn.crawling

    rest_name, addr, lat, lng = restaurant_common.get_r_info(place_id)

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
    href_list = []
    driver.find_element_by_class_name('x3qfX').send_keys(rest_name)
    hrefs = driver.find_elements_by_class_name('yCE8d')
    for hr in hrefs:
        href=hr.get_attribute('href')
        if 'locations' in href:
            href_list.append(href)
        else:
            continue
    find = False
    print(href_list)
    for site in href_list:
        driver.get(site)
        location = driver.find_elements_by_tag_name('meta')
        print(len(location))
        two = 0
        for meta in location:
            try:
                if 'place:location:latitude' in meta.get_attribute('property'):
                    r_lat = round(float(meta.get_attribute('content')), 2)
                    print(r_lat)
                    two += 1
                elif 'place:location:longitude' in meta.get_attribute('property'):
                    r_lng = round(float(meta.get_attribute('content')), 2)
                    print(r_lng)
                    two += 1
                    break
                else:
                    continue
            except:
               pass
        print(str(r_lat)+" "+str(r_lng)+" "+str(round(lat, 2))+" "+str(round(lng, 2)))
        if two == 2 and round(lat, 2) == r_lat and round(lng, 2) == r_lng:
            # 크롤링시작!!
            find = True
            searches = driver.find_element_by_class_name('_9AhH0')  # 사진들
            searches.click()
            while True:
                time.sleep(2)
                try:
                    name = driver.find_element_by_class_name('_6lAjh').text
                    comment = driver.find_element_by_class_name('C4VMK').find_element_by_tag_name('span').text
                    date = driver.find_element_by_class_name('FH9sR').get_attribute('datetime')
                    p = re.compile('[0-9]*-[0-9]*-[0-9]*')
                    date = p.match(date)[0]
                    print(date)
                    print(type(date))
                    if datetime.datetime.strptime(date, "%Y-%m-%d").date() > last:
                        db.rest_instagram.insert_one(restaurant_common.data_format(place_id, rest_name, addr, lat, lng, name, comment, 0, date, place_id))
                except:
                    pass
                try:
                    driver.find_element_by_class_name('coreSpriteRightPaginationArrow').click()
                except NoSuchElementException:
                    traceback.print_exc()
                    break
        if find:
            print('find')
            driver.close()
            break




    '''
    href_list.append(href)
    for curr in searches:
        try:

        except NoSuchElementException:
            continue
        curr.find_element_by_class_name('Ap253').click()
        time.sleep(10)
        with open(rest_name + '.txt', 'w', encoding='UTF-8') as f:
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
                    db.instagram.insert_one(data_format(place_id, rest_name, addr, lat, lng, name, comment, date))
                except NoSuchElementException:
                    pass
                try:
                    driver.find_element_by_class_name('coreSpriteRightPaginationArrow').click()
                    count = 0
                except NoSuchElementException:
                    break
        break
    driver.close()
    '''

# ------------------ 테스트 부분 ----------------------------
if __name__ == "__main__":
    instagram_crawling('ChIJ7bKnOIiifDURVkqxTJFicrY',None)