import requests
import pymysql
import datetime
import traceback


key = ''  # 구글 API KEY


# ----------------모두 사용하는 함수 모아놓은 곳----------------
# --------------------지오 코딩------------------------------
def get_r_info(place_id):
    global key
    try:
        headers = {'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'}
        base_url = " https://maps.googleapis.com/maps/api/place/details/json?"
        url = base_url + 'place_id=' + place_id + '&key=' + key
        print(url)
        resp = requests.get(url, headers=headers)
        data = resp.json()
        result = data.get('result')
        rest_name = result.get('name')
        rest_address = result.get('formatted_address')
        rest_lat = str(result.get('geometry').get('location').get('lat'))
        rest_lng = str(result.get('geometry').get('location').get('lng'))
        ans = 0
        print('rest_name :', rest_name)
        print('address :', rest_address)
        print('lat :', float(rest_lat))
        print('lng :', float(rest_lng))
    except:
        return 'None', 'None', 'None', 'None'
    return rest_name, rest_address, float(rest_lat), float(rest_lng)


# -------------------몽고 디비 관련 함수 ---------------------
# ----------------인스타그램은 평점이 없으므로 학습시키지 않는다------------------
def data_format(place_id, r_name, addr, lat, lng, name, comment, rate, date, keyword):
    return {
        'place_id': place_id,
        'r_name': r_name,
        'r_addr': addr,
        'r_lat': lat,
        'r_lng': lng,
        'name': name,
        'comment': comment,
        'rate': rate,
        'date': date,
        'location': keyword
    }


# ---------------마지막 크롤링 날짜 받아오기 ----------
def find_last_crawling_date(place_id):
    conn = pymysql.connect(host='118.220.3.71', user='root', password='rjsdnrkkw4809!!', db='area', charset='utf8')
    curs = conn.cursor()
    sql = "SELECT restcrawlingdate FROM restaurant WHERE restgoogleid='"+place_id+"'"
    curs.execute(sql)
    rows = curs.fetchall()
    if len(rows) >= 1:
        for row in rows:
            if row[0] is None:
                return datetime.datetime.today().replace(year=1900, month=1, day=1).date()
            else:
                return row[0]


# -------------크롤링 마칠 때 -------------
def update_last(place_id):
    print('start')
    conn = pymysql.connect(host='118.220.3.71', user='root', password='rjsdnrkkw4809!!', db='area', charset='utf8')
    curs = conn.cursor()
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    sql = "UPDATE restaurant SET restcrawlingdate ='" + date +"' WHERE restgoogleid='" + place_id + "'"
    curs.execute(sql)
    conn.commit()


# ------------- 메뉴 데이터 추가-----------
def update_text(place_id, menu):
    try:
        conn = pymysql.connect(host='118.220.3.71', user='root', password='rjsdnrkkw4809!!', db='area', charset='utf8')
        curs = conn.cursor()
        sql = "UPDATE restaurant SET restText ='"+menu+"' WHERE restgoogleid='"+place_id+"'"
        curs.execute(sql)
        conn.commit()
    except:
        traceback.print_exc()
