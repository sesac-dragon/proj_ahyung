import streamlit as st
import pandas as pd
import pymysql
from db import load_env
from streamlit_folium import folium_static
import folium
from folium.plugins import MarkerCluster

st.markdown("# cafe-map")

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
    query = "SELECT cafename, cafeaddress, latitude, longitude, blogdate FROM tb_cafe ORDER BY blogdate DESC"
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    conn.close()
    return pd.DataFrame(result)

df = get_cafe_data()

# 지도
if not df.empty:
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()
    my_map = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # 마커 추가
    for index, row in df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"{row['cafename']}<br>{row['cafeaddress']}<br>{row['blogdate']}",
            tooltip=row["cafename"]
        ).add_to(my_map)

    # folium 지도 출력
    st_folium(my_map, width=1000, height=600)
else:
    st.warning("표시할 데이터가 없습니다.")
    