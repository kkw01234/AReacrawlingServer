from crawling_dining_code import dining_code_crawling
from crawling_mango_plate import mango_plate_crawling
from crawling_instagram import instagram_crawling
from crawling_trip_advisor import trip_advisor_crawling
from flask import Flask, request,jsonify
import traceback
import pymysql
from datetime import datetime
from restaurant_crawling import restaurant_mango_plate, restaurant_trip_advisor, restaurant_instagram, restaurant_dining_code, restaurant_common

app = Flask(__name__)
app.secret_key = 'HZt,}`v{&pwv&,qvtSV8Z9NE!z,p=e?('
private_key = '123456'

# 인스타그램 크롤링
# key 임의의 키값 name : 크롤링할 지역이름
@app.route("/instagram_crawling", methods=['GET'])
def start_crawling():
    key = request.args.get('key')
    name = request.args.get('keyword')
    try:
        if key == private_key:
            crawling_list = [name]
            for crawl in crawling_list:
                instagram_crawling(crawl)
        else:
            return jsonify({"result": "key Error"})
    except:
        traceback.print_exc()
        return jsonify({"result": "fail"})
    return jsonify({"result": "success"})


# 지역검색(망고플레이트, 다이닝코드, 트립 어드바이저)
# 오류났을경우 크롤링한 데이터 삭제....????
@app.route("/location_crawling", methods=['GET'])
def location_crawling():
    key = request.args.get('key')
    keyword = request.args.get('keyword')
    try:
        if key == private_key:
            crawling_list = [keyword]
            for crawl in crawling_list:
                last = last_crawling(crawl)
                dining_code_crawling(crawl, last)
                mango_plate_crawling(crawl, last)
                trip_advisor_crawling(crawl, last)
                sql(crawl)
        else:
            return jsonify({"result": "Key Error"})
    except:
        traceback.print_exc()
        return jsonify({"result": "fail"})
import queue
crawling_list = queue.Queue()
lock = False
@app.route("/restaurant_crawling", methods=['GET'])
def restaurant_crawling():
    global lock, crawling_list
    key = request.args.get('key')
    print(key)
    if key != private_key:
        return jsonify({'result': 'KEY ERROR'})
    place_id = request.args.get('place_id')
    print(place_id)
    while True:
        if lock is False:
            break
    lock = True
    try:
        last = restaurant_common.find_last_crawling_date(place_id)
        restaurant_dining_code.dining_code_crawling(place_id, last)
        restaurant_mango_plate.mango_plate_crawling(place_id, last)
        restaurant_instagram.instagram_crawling(place_id, last)
        restaurant_trip_advisor.trip_advisor_crawling(place_id, last)
        restaurant_common.update_last(place_id)
        lock = False
        return jsonify({'result': place_id+' finish crawling'})
    except:
        traceback.print_exc()
        lock = False
        return jsonify({'result': 'Error'})



def last_crawling(keyword):
    conn = pymysql.connect(host='118.220.3.71', user='root', password='rjsdnrkkw4809!!', db='area', charset='utf8')
    curs = conn.cursor()
    sql = "SELECT last_crawling_date FROM crawling_date WHERE location ='" + keyword + "'"
    curs.execute(sql)
    rows = curs.fetchall()
    if len(rows) >=1:
        for row in rows:
            print(row[0])
            return row[0]
    else:
        date = '1900-01-01'
        return datetime.strptime(date, '%Y-%m-%d').date()


def sql(keyword):
    conn = pymysql.connect(host='118.220.3.71', user='root', password='rjsdnrkkw4809!!', db='area', charset='utf8')
    curs = conn.cursor()
    sql = "SELECT * FROM crawling_date WHERE location ='"+keyword+"'"
    curs.execute(sql)
    rows = curs.fetchall()
    if len(rows) >= 1:
        sql = "UPDATE crawling_date SET last_crawling_date='"+str(datetime.today())+"' WHERE location='"+keyword+"'"
        curs.execute(sql)
        conn.commit()
    else:
        sql = "INSERT INTO crawling_date(last_crawling_date, location) VALUES('"+str(datetime.today())+"','"+keyword+"')"
        curs.execute(sql)
        conn.commit()
    curs.close()
    conn.close()
    return jsonify({"result": "success"})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=15565)












# 강남, 수원, 대전, 대구, 춘천, 전주, 인천, 천안, 완도, 용인, 광주광역시



 # 용산구 남영동, 보광동, 서빙고동, 용문동, 이촌동 이태원동, 청파동 한남동 효창동 후암동 한강로동
# 강남, 수원, 대전, 대구, 부산, 춘천, 전주, // 인천, 천안, 완도, 용인, 광주 //서초, 성남, 고양(05.15)
# 마포구 합정동
