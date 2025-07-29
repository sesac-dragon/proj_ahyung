import re


def keyword_sentences(text, keyword_list):
    if not text:
        return []
    # 문장 단위로 분리 (간단한 한글 기준)
    sentences = re.split(r"[.!?。\n]", text)
    # 키워드가 포함된 문장만 필터링
    return [s.strip() for s in sentences if any(k in s for k in keyword_list)]
