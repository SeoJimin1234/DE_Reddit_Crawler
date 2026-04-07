"""
Reddit Top 크롤러
- top 정렬로 전체 수집 (t=all)
- 기존 CSV에 있는 document_id는 자동 스킵
- 800행마다 저장 + 15분 휴식
- rate limit 시 5분 대기 후 재시도
"""

import requests
import time
import re
import csv
import os
import random
from datetime import datetime
from typing import Optional, List

# ================================================================
# ⚙️  설정
# ================================================================

SUBREDDIT_OPTIONS = {
    "1": ("wegovy",   "Wegovy",           "wegovy_reddit.csv"),
    "2": ("wegovy",   "WegovyWeightLoss",  "wegovyweightloss_reddit.csv"),
    "3": ("mounjaro", "Mounjaro",          "mounjaro_reddit.csv"),
}

FETCH_COMMENTS = True
DELAY          = 2.0
SAVE_EVERY     = 800

# 수집할 정렬 방식 (순서대로 실행, 중복은 document_id로 자동 제거)
SORT_TYPES = [
    ("new",  None),       # 최신순
    ("hot",  None),       # 현재 화제
    ("top",  "all"),      # 역대 인기
    ("top",  "year"),     # 최근 1년 인기
]

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def get_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

FIELDNAMES = [
    "document_id", "platform", "drug_type", "subreddit",
    "text_body", "author_id", "timestamp", "score",
    "thread_id", "parent_id", "depth_level", "path",
    "user_demographics", "medication_timeline",
    "post_title", "url",
]

# ================================================================
# 정규식
# ================================================================

DEMO_PATTERN = re.compile(r'\b(\d{1,2})(F|M|f|m)\b|\b(F|M|f|m)(\d{1,2})\b')
TIMELINE_PATTERN = re.compile(
    r'(week\s*\d+|dose\s*[\d.]+\s*mg|[\d.]+\s*mg|titration|starting dose|maintenance)',
    re.IGNORECASE
)

def extract_demographics(text: str) -> str:
    if not text:
        return ""
    matches = DEMO_PATTERN.findall(text)
    results = []
    for m in matches:
        if m[0] and m[1]:
            results.append(f"{m[0]}{m[1].upper()}")
        elif m[2] and m[3]:
            results.append(f"{m[2].upper()}{m[3]}")
    return ", ".join(set(results)) if results else ""

def extract_timeline(text: str) -> str:
    if not text:
        return ""
    matches = TIMELINE_PATTERN.findall(text)
    return ", ".join(set(m.strip() for m in matches)) if matches else ""

# ================================================================
# 서브레딧 선택
# ================================================================

def select_subreddit() -> tuple:
    print("\n" + "="*50)
    print("📌 수집할 서브레딧 선택")
    print("="*50)
    for num, (drug, sub, fp) in SUBREDDIT_OPTIONS.items():
        print(f"  {num}. r/{sub}  →  {fp}")
    print()
    while True:
        choice = input("  번호 입력 (1/2/3): ").strip()
        if choice in SUBREDDIT_OPTIONS:
            drug_type, subreddit, filepath = SUBREDDIT_OPTIONS[choice]
            print(f"  ✅ 선택: r/{subreddit}  →  {filepath}")
            return drug_type, subreddit, filepath
        print("  ❌ 1, 2, 3 중 하나를 입력하세요.")

# ================================================================
# 중복 방지
# ================================================================

def load_existing_ids(filepath: str) -> set:
    if not os.path.exists(filepath):
        return set()
    ids = set()
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.add(row["document_id"])
    print(f"  📂 기존 수집 {len(ids)}건 로드 (중복 스킵)")
    return ids

# ================================================================
# CSV 저장
# ================================================================

def save_csv(rows: List[dict], filepath: str):
    file_exists = os.path.exists(filepath)
    mode = "a" if file_exists else "w"
    with open(filepath, mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

def get_last_date(rows: List[dict]) -> str:
    timestamps = [r["timestamp"] for r in rows if r.get("timestamp")]
    if not timestamps:
        return "알 수 없음"
    return min(timestamps)[:10]

# ================================================================
# API 요청
# ================================================================

def fetch_json(url: str) -> Optional[dict]:
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code == 200:
            time.sleep(random.uniform(1.5, 4.0))
            return response.json()
        elif response.status_code == 429:
            print(f"\n  ⚠️  [Rate limit] 5분 대기 후 재시도...")
            time.sleep(300)
            return fetch_json(url)
        else:
            print(f"  [오류] HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"  [예외] {e}")
        return None

# ================================================================
# 댓글 트리 재귀 순회
# ================================================================

def parse_comment_tree(
    comments: list, thread_id: str, parent_id: str,
    depth: int, parent_path: str, drug_type: str,
    subreddit: str, rows: List[dict], existing_ids: set,
):
    for item in comments:
        if item.get("kind") == "more":
            continue
        data       = item.get("data", {})
        comment_id = data.get("id", "")
        if comment_id in existing_ids:
            continue
        body         = data.get("body", "")
        created_utc  = data.get("created_utc", 0)
        current_path = f"{parent_path}/{comment_id}"
        rows.append({
            "document_id":         comment_id,
            "platform":            "Reddit",
            "drug_type":           drug_type,
            "subreddit":           subreddit,
            "text_body":           body,
            "author_id":           data.get("author", ""),
            "timestamp":           datetime.utcfromtimestamp(created_utc).isoformat(),
            "score":               data.get("score", 0),
            "thread_id":           thread_id,
            "parent_id":           parent_id,
            "depth_level":         depth,
            "path":                current_path,
            "user_demographics":   extract_demographics(body),
            "medication_timeline": extract_timeline(body),
            "post_title":          "",
            "url":                 f"https://www.reddit.com{data.get('permalink', '')}",
        })
        existing_ids.add(comment_id)
        replies = data.get("replies")
        if replies and isinstance(replies, dict):
            parse_comment_tree(
                replies.get("data", {}).get("children", []),
                thread_id=thread_id, parent_id=comment_id,
                depth=depth + 1, parent_path=current_path,
                drug_type=drug_type, subreddit=subreddit,
                rows=rows, existing_ids=existing_ids,
            )

# ================================================================
# 게시글 + 댓글 수집
# ================================================================

def fetch_post_with_comments(
    subreddit: str, post: dict, drug_type: str, existing_ids: set,
) -> List[dict]:
    rows        = []
    post_id     = post.get("id", "")
    selftext    = post.get("selftext", "")
    permalink   = post.get("permalink", "")
    created_utc = post.get("created_utc", 0)

    if post_id not in existing_ids:
        rows.append({
            "document_id":         post_id,
            "platform":            "Reddit",
            "drug_type":           drug_type,
            "subreddit":           subreddit,
            "text_body":           selftext,
            "author_id":           post.get("author", ""),
            "timestamp":           datetime.utcfromtimestamp(created_utc).isoformat(),
            "score":               post.get("score", 0),
            "thread_id":           post_id,
            "parent_id":           None,
            "depth_level":         0,
            "path":                post_id,
            "user_demographics":   extract_demographics(selftext),
            "medication_timeline": extract_timeline(selftext),
            "post_title":          post.get("title", ""),
            "url":                 f"https://www.reddit.com{permalink}",
        })
        existing_ids.add(post_id)

    if not FETCH_COMMENTS:
        return rows

    data = fetch_json(f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json")
    if data and isinstance(data, list) and len(data) > 1:
        parse_comment_tree(
            data[1].get("data", {}).get("children", []),
            thread_id=post_id, parent_id=post_id,
            depth=1, parent_path=post_id,
            drug_type=drug_type, subreddit=subreddit,
            rows=rows, existing_ids=existing_ids,
        )

    time.sleep(random.uniform(DELAY, DELAY + 2.0))
    return rows

# ================================================================
# 정렬별 수집
# ================================================================

def crawl_one_sort(
    subreddit: str, drug_type: str, filepath: str,
    existing_ids: set, sort: str, t: Optional[str],
) -> int:
    label = f"top({t})" if t else sort
    print(f"\n  📂 정렬: {label}")

    buffer      = []
    total_saved = 0
    after       = None
    page        = 1

    while True:
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit=100"
        if t:
            url += f"&t={t}"
        if after:
            url += f"&after={after}"

        print(f"  페이지 {page} 요청 중...", end="\r")
        data = fetch_json(url)
        if not data:
            break

        children = data.get("data", {}).get("children", [])
        if not children:
            break

        for child in children:
            post = child.get("data", {})
            rows = fetch_post_with_comments(subreddit, post, drug_type, existing_ids)
            buffer.extend(rows)

            if len(buffer) >= SAVE_EVERY:
                last_date = get_last_date(buffer)
                save_csv(buffer, filepath)
                total_saved += len(buffer)
                print(f"\n  💾 중간 저장 완료")
                print(f"     - 이번 실행 누적: {total_saved}행")
                print(f"     - 현재까지 수집된 데이터: {last_date} 까지")
                buffer.clear()

        after = data.get("data", {}).get("after")
        if not after:
            print(f"\n  → {label} 마지막 페이지 도달")
            break

        page += 1
        time.sleep(random.uniform(DELAY, DELAY + 3.0))

    if buffer:
        last_date = get_last_date(buffer)
        save_csv(buffer, filepath)
        total_saved += len(buffer)
        print(f"\n  💾 저장 완료 ({total_saved}행)")
        buffer.clear()

    return total_saved


def crawl_all_sorts(subreddit: str, drug_type: str, filepath: str, existing_ids: set) -> int:
    print(f"\n{'='*50}")
    print(f"[{drug_type.upper()}] r/{subreddit}")
    print(f"  정렬 순서: new → hot → top(all) → top(year)")
    print(f"  기존 수집 데이터와 중복되는 항목은 자동 스킵")

    grand_total = 0
    for sort, t in SORT_TYPES:
        saved = crawl_one_sort(subreddit, drug_type, filepath, existing_ids, sort, t)
        grand_total += saved
        label = f"top({t})" if t else sort
        print(f"  ✅ {label} 완료: {saved}행 추가 (누적 {grand_total}행)")

    return grand_total

# ================================================================
# 메인
# ================================================================

def main():
    print("\n🔍 Reddit 크롤러 (new / hot / top 다각화)")
    print("  기존 데이터 중복 자동 스킵")

    drug_type, subreddit, filepath = select_subreddit()

    input("\n▶️  Enter를 누르면 수집을 시작합니다...")

    existing_ids = load_existing_ids(filepath)
    saved = crawl_all_sorts(subreddit, drug_type, filepath, existing_ids)

    print("\n" + "="*50)
    print(f"🎉 수집 완료!")
    print(f"   이번 실행 총 수집: {saved}행")
    print(f"   저장 파일: {filepath}")
    print("="*50)

if __name__ == "__main__":
    main()