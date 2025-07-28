from crawler import crawl_pages
from db import insert_cafe_data, get_latest_logNo
from datetime import datetime


# 최신 logNo 5개 가져오기
latest_logno = get_latest_logNo(limit=5)

cafe_data = crawl_pages(pages=5, keyword="뜨개카페", latest_logno=latest_logno)


if cafe_data:
    try:
        cafe_data.sort(
            key=lambda x: x["블로그작성일"]
            )
    except Exception as e:
        print(f"정렬 중 오류 발생: {e}")

    print(f"수집된 글 {len(cafe_data)}개 저장")
    insert_cafe_data(blog_data=cafe_data, env_path=".env")
else:
    print("신규 글 없음, 종료")
