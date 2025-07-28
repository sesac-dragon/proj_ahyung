import streamlit as st
import pandas as pd
import pymysql
from db import load_env
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import folium
from folium.plugins import MarkerCluster
import json
import re


# DB 연결
# .env 파일 불러오는 함수
def get_cafe_data():
    env = load_env(".env")
    conn = pymysql.connect(
        host=env["DB_HOST"],
        user=env["DB_USER"],
        password=env["DB_PASSWORD"],
        database=env["DB_DATABASE"],
        port=int(env["DB_PORT"]),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    query = "SELECT cafename, cafeaddress, latitude, longitude, blogdate, blogtext FROM tb_cafe ORDER BY blogdate DESC"
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    conn.close()
    return pd.DataFrame(result)


df = get_cafe_data()
df = df[(df["latitude"].between(33.0, 38.7)) & (df["longitude"].between(124.5, 131.9))]

# 중복 카페 제거
df_unique = df.drop_duplicates(subset=["latitude", "longitude"])

st.set_page_config(layout="wide")
st.markdown("# 🧶 뜨개카페 지도")
col1, col2 = st.columns([2,1])

# 뜨개카페 지도 표시
with col1:
    if not df_unique.empty:
        center_lat = df_unique["latitude"].mean()
        center_lon = df_unique["longitude"].mean()
        my_map = folium.Map(location=[center_lat, center_lon], zoom_start=9)
        marker_cluster = MarkerCluster().add_to(my_map)

        # 마커 추가
        for index, row in df_unique.iterrows():
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=f"{row['cafename']}<br>{row['cafeaddress']}<br>{row['blogdate']}",
                tooltip=row["cafename"],
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(marker_cluster)

        # folium 지도 출력
        st_data = st_folium(
            my_map, width=1000, height=600, returned_objects=["last_object_clicked"]
        )
    else:
        st.warning("표시할 데이터가 없습니다.")



# 블로그 텍스트 분석
# 키워드 json 파일 불러오기 
with open("keywords.json", "r", encoding="utf-8") as f:
    keywords = json.load(f)

crochet_keywords = keywords['crochet']
cafe_keywords = keywords['cafe']

# 키워드 문장 추출
def keyword_sentences(text, keyword_list):
    if not text:
        return []
    # 문장 단위로 분리 (간단한 한글 기준)
    sentences = re.split(r'[.!?。\n]', text)
    # 키워드가 포함된 문장만 필터링
    return [s.strip() for s in sentences if any(k in s for k in keyword_list)]

with col2:
    # 마커 클릭시 카페 정보 출력
    clicked = st_data["last_object_clicked"]
    
    if clicked:
        select_loc = df[
            (df["latitude"] == clicked["lat"]) & (df["longitude"] == clicked["lng"])
        ]

        # 좌표 일치한 데이터 찾기
        if not select_loc.empty:
            cafename = select_loc.iloc[0]["cafename"]
            st.markdown(f"## {cafename} ")
            # 같은 카페이름을 가진 모든 블로그 데이터가져오기
            cafe_rows = df[df["cafename"] == cafename].sort_values(
                "blogdate", ascending=False
            )

            # 공통 주소 정보
            address = select_loc.iloc[0]["cafeaddress"]
            st.markdown(f"**주소 :** {address}")
            st.markdown("---")

            # 블로그 키워드 문장 출력
            for idx, row in cafe_rows.iterrows():
                blog_text = row["blogtext"]

                crochet_sentences = keyword_sentences(blog_text, crochet_keywords)
                cafe_sentences = keyword_sentences(blog_text, cafe_keywords)

                if crochet_sentences or cafe_sentences:
                    if crochet_sentences:
                        st.markdown("**뜨개 관련 문장:**")
                        for s in crochet_sentences:
                            st.write("- " + s)

                    if cafe_sentences:
                        st.markdown("**카페 관련 문장:**")
                        for s in cafe_sentences:
                            st.write("- " + s)
                    st.markdown("---")
                else:
                    continue

        else:
            st.write("카페 정보 없음")
    else:
        st.write("지도 마커를 클릭하면 카페 정보를 볼 수 있습니다.")
