import pandas as pd
import pymysql
from crawler.db import load_env
import re
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from tqdm import tqdm
import os

load_env(".env")

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

# API 키를 직접 전달
llm = ChatOpenAI(
    model_name="gpt-4o-mini", temperature=0.5, openai_api_key=openai_api_key
)

# 키워드 리스트 직접 정의
crochet_keywords = [
    "실종류",
    "코바늘",
    "대바늘",
    "원형뜨기",
    "모티브",
    "뜨개수업",
    "니팅",
    "손뜨개",
    "모헤어",
]
cafe_keywords = [
    "좌석",
    "조명",
    "화장실",
    "주차",
    "콘센트",
    "음악",
    "에어컨",
    "와이파이",
    "충전",
]


# 문장 추출 함수
def keyword_sentences(text, keyword_list):
    if not text:
        return []
    # 문장 단위로 분리 (간단한 한글 기준)
    sentences = re.split(r"[.!?。\n]", text)
    # 키워드가 포함된 문장만 필터링
    return [s.strip() for s in sentences if any(k in s for k in keyword_list)]


# 프롬프트 템플릿
template = """
너는 한국어 텍스트 분석 전문가야.
다음 문장들은({context}) 블로그 리뷰에서 추출된 내용이야. 

너가 각 문장에서 찾는 키워드는 뜨개질과 관련된 키워드야
뜨개질과 관련된 키워드가 있는지 없는지 앞 뒤 문장을 보고 문맥을 바탕으로 정확히 판단해서 정리해줘.
너가 생각했을 때 뽑아낸 키워드가 뜨개질과 관련이 없으면 정리하지 마. 

예시를 참고해서 아래 형식으로 정리해줘.
키워드만 작성해서 정리해줘.

형식은 '키워드명: 실제 여부' 이렇게 정리해서 보여주면 돼.
(예시: 화장실, 없음 
주차장, 있음 등등 )
만약 모든 키워드의 실제 여부가 '없음'으로 나오면 키워드는 보여주지 말고 
'관련 정보가 없습니다.' 이것만 출력해줘
"""
prompt = PromptTemplate(input_variables=["context"], template=template)
chain = LLMChain(llm=llm, prompt=prompt)


# DB에서 데이터 가져오기
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
    
    query = "SELECT logNo, cafename, blogtext FROM tb_cafe WHERE summary IS NULL"
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    conn.close()
    return pd.DataFrame(result)


# 요약 결과 DB에 저장
def update_summary(logNo, summary):
    env = load_env(".env")
    conn = pymysql.connect(
        host=env["DB_HOST"],
        user=env["DB_USER"],
        password=env["DB_PASSWORD"],
        database=env["DB_DATABASE"],
        port=int(env["DB_PORT"]),
        charset="utf8mb4",
    )
    with conn.cursor() as cur:
        sql = "UPDATE tb_cafe SET summary = %s WHERE logNo = %s"
        cur.execute(sql, (summary, logNo))
    conn.commit()
    conn.close()


# === 메인 실행 ===
if __name__ == "__main__":
    df = get_cafe_data()

    for idx, row in tqdm(df.iterrows(), total=len(df)):
        text = row["blogtext"]
        logNo = row["logNo"]

        crochet_sent = keyword_sentences(text, crochet_keywords)
        cafe_sent = keyword_sentences(text, cafe_keywords)
        context = "\n".join(crochet_sent + cafe_sent)

        if context.strip():
            try:
                result = chain.invoke({"context": context})
                summary_text = result["text"].strip()
                update_summary(logNo, summary_text)
                print(f"{logNo} 요약 저장 완료")
            except Exception as e:
                print(f"{logNo} 처리 중 오류 발생: {e}")
        else:
            update_summary(logNo, "관련 정보가 없습니다.")
            print(f"{logNo} 문장 없음 처리 완료")

# 중복 제거 
def deduplicate_summary_by_cafename(df):
    grouped = df.groupby("cafename")
    results = []

    for cafename, group in grouped:
        summaries = group["summary"].dropna().tolist()
        unique_summaries = sorted(set(s.strip() for s in summaries if s.strip()))
        
        final_summary = "\n".join(unique_summaries) if unique_summaries else "관련 정보가 없습니다."
        results.append({
            "cafename": cafename,
            "summary": final_summary
        })
    
    return pd.DataFrame(results)
