import streamlit as st
import pandas as pd
import pymysql
from db import load_env
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import folium
import re

# DB 연결 함수
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
    query = """
    SELECT cafename, cafeaddress, latitude, longitude, blogdate, blogtext, summary
    FROM tb_cafe
    ORDER BY blogdate DESC
    """
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    conn.close()
    return pd.DataFrame(result)

# 키워드 추출 및 중복 제거 함수 (최신값 우선)
def extract_and_deduplicate_keywords(summaries):
    """여러 블로그의 summary에서 키워드를 추출하고 중복 제거 (최신값 우선)"""
    unique_keywords = []
    seen_keywords = set()
    
    # summaries는 이미 최신순으로 정렬되어 있음
    for summary in summaries:
        if not summary or summary.strip() == "":
            continue
            
        # 숫자와 "관련 정보가 없습니다." 부분 제거
        cleaned_summary = re.sub(r'\d+관련 정보가 없습니다\.', '', summary)
        
        # 전체 텍스트를 공백으로 분할하여 키워드-상태 쌍을 찾기
        # 패턴 1: "키워드: 있음" 형태
        colon_pairs = re.findall(r'([^:\d,\s]+):\s*(있음|없음)', cleaned_summary)
        
        # 패턴 2: "키워드, 있음" 형태 (연속으로 나열된 경우 포함)
        comma_pairs = re.findall(r'([^:,\d]+),\s*(있음|없음)', cleaned_summary)
        
        # 모든 쌍 처리
        all_pairs = colon_pairs + comma_pairs
        
        for keyword, status in all_pairs:
            keyword = keyword.strip()
            # "있음" 상태인 키워드만 추가하고, 중복 제거
            if (status == '있음' and keyword and not keyword.isdigit() 
                and keyword != '관련 정보가 없습니다' and keyword not in seen_keywords):
                unique_keywords.append(keyword)
                seen_keywords.add(keyword)
    
    return unique_keywords

def format_keywords_display(unique_keywords):
    """키워드를 보기 좋게 포맷팅"""
    if not unique_keywords:
        return "관련 키워드가 없습니다."
    
    # 키워드들을 쉼표로 구분하여 표시
    return ", ".join(unique_keywords)

# 데이터 불러오기
df = get_cafe_data()
df = df[(df["latitude"].between(33.0, 38.7)) & (df["longitude"].between(124.5, 131.9))]

# 중복 카페 제거
df_unique = df.drop_duplicates(subset=["latitude", "longitude"])

# Streamlit 페이지 설정
st.set_page_config(layout="wide")
st.markdown("# 🧶 뜨개카페 지도")

col1, col2 = st.columns([2, 1])

# 지도 시각화
with col1:
    if not df_unique.empty:
        center_lat = df_unique["latitude"].mean()
        center_lon = df_unique["longitude"].mean()
        my_map = folium.Map(location=[center_lat, center_lon], zoom_start=9)
        marker_cluster = MarkerCluster().add_to(my_map)

        for _, row in df_unique.iterrows():
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=folium.Popup(
                    f"<b>{row['cafename']}</b><br>{row['cafeaddress']}", max_width=500
                ),
                tooltip=row["cafename"],
                icon=folium.Icon(color="blue", icon="info-sign"),
            ).add_to(marker_cluster)

        st_data = st_folium(
            my_map, width=1000, height=600, returned_objects=["last_object_clicked"]
        )
    else:
        st.warning("표시할 데이터가 없습니다.")

# 클릭된 마커의 상세 정보 표시
with col2:
    clicked = st_data["last_object_clicked"]

    if clicked:
        select_loc = df[
            (df["latitude"] == clicked["lat"]) & (df["longitude"] == clicked["lng"])
        ]

        if not select_loc.empty:
            cafename = select_loc.iloc[0]["cafename"]
            cafeaddress = select_loc.iloc[0]["cafeaddress"]

            st.markdown(f"### 📍 {cafename}")
            st.markdown(f"**주소:** {cafeaddress}")
            
            # 해당 카페의 모든 블로그 요약 수집
            cafe_rows = df[df["cafename"] == cafename].sort_values(
                "blogdate", ascending=False
            )

            # 모든 summary 수집
            summaries = []
            for _, row in cafe_rows.iterrows():
                summary = row.get("summary", "")
                if summary and summary.strip():
                    summaries.append(summary.strip())

            # 키워드 추출 및 중복 제거
            unique_keywords = extract_and_deduplicate_keywords(summaries)
            
            st.markdown("### 카페 키워드")
            if unique_keywords:
                formatted_keywords = format_keywords_display(unique_keywords)
                st.markdown(formatted_keywords)
            else:
                st.markdown("추출된 키워드가 없습니다.")
            
            # 원본 블로그 요약들 (선택사항으로 표시)
            with st.expander("원본 블로그 요약 보기"):
                for i, (_, row) in enumerate(cafe_rows.iterrows(), 1):
                    summary = row.get("summary", "")
                    if summary and summary.strip():
                        st.markdown(f"**블로그 {i}:**")
                        # st.markdown(df['blogtext'])
                        st.markdown(summary.strip())
                        st.markdown("---")

        else:
            st.warning("선택된 위치에 해당하는 카페 정보를 찾을 수 없습니다.")
    else:
        st.info("지도의 마커를 클릭해 카페 정보를 확인하세요.")