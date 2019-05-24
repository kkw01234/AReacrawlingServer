from crawling_dining_code import dining_code_crawling
from crawling_mango_plate import mango_plate_crawling
from crawling_trip_advisor import trip_advisor_crawling

if __name__ == '__main__':
    # 동별로 하는게 좋지않을까???? 그래야 중복이 없을거같은데

    #
    crawling_list = ['일산', '덕양', '용산']
    for crawl in crawling_list:
        # dining_code_crawling(crawl)
        # mango_plate_crawling(crawl)
        trip_advisor_crawling(crawl)

#강남,수원,대전,대구,춘천,전주,인천,천안,완도,용인,광주,



 # 용산구 남영동, 보광동, 서빙고동, 용문동, 이촌동 이태원동, 청파동 한남동 효창동 후암동 한강로동
# 강남, 수원, 대전, 대구, 부산, 춘천, 전주, // 인천, 천안, 완도, 용인, 광주 //서초, 성남, 고양(05.15)
# 마포구 합정동
# 광주시 초월읍