import streamlit as st
import pandas as pd
import pymysql
from db import load_env
from streamlit_folium import st_folium  
from folium.plugins import MarkerCluster
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
    query = "SELECT cafename, cafeaddress, latitude, longitude, blogdate, blogtext FROM tb_cafe ORDER BY blogdate DESC"
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    conn.close()
    return pd.DataFrame(result)

df = get_cafe_data()
df = df[
    (df["latitude"].between(33.0, 38.7)) &
    (df["longitude"].between(124.5, 131.9))
]

# 중복 카페 제거
df_unique = df.drop_duplicates(subset=['latitude','longitude'])

# 지도 표시
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
            tooltip=row["cafename"]
        ).add_to(marker_cluster)

    # folium 지도 출력
    st_data = st_folium(my_map, width=1000, height=600, returned_objects=['last_object_clicked'])
else:
    st.warning("표시할 데이터가 없습니다.")

# 마커 클릭시 카페 정보 출력

clicked = st_data['last_object_clicked']

select_loc = df[(df['latitude'] == clicked['lat']) & (df['longitude'] == clicked['lng'])]

# 좌표 일치한 데이터 찾기
if not select_loc.empty:
    cafename = select_loc.iloc[0]['cafename']
    st.markdown(f"## {cafename} ")
    # 같은 카페이름을 가진 모든 블로그 데이터가져오기
    cafe_rows = df[df["cafename"] == cafename].sort_values("blogdate", ascending=False)

    # 공통 주소 정보
    address = select_loc.iloc[0]['cafeaddress']
    st.markdown(f'**주소 :** {address}')
    st.markdown("---")
    
    # 블로그 글 불러오기
    for idx, row in cafe_rows.iterrows():
        st.markdown(f"""
                    **작성일 :** {row['blogdate']}\n
                        """)
        st.text_area("**블로그내용**", row.get('blogtext',""), height=250)
        # st.text(f"블로그내용, {row['blogtext']}")
        st.markdown("---")
else:
    st.write("카페 정보 없음")