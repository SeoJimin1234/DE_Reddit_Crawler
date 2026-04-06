"""
Reddit JSON API Crawler - 기간별 수집용
- 실행 시 기간 직접 입력
- 800행마다 CSV 중간 저장 + 10~15분 자동 휴식
- 저장 시 마지막으로 저장된 날짜 출력
- 중단 후 재실행 시 자동 이어받기 (중복 방지)
"""

import requests
import time
import re
import csv
import os
from datetime import datetime
from typing import Optional, List

# ================================================================
# ⚙️  고정 설정 (수정 불필요)
# ================================================================

SUBREDDITS = {
    "wegovy":   ["Wegovy", "WegovyWeightLoss"],
    "mounjaro": ["Mounjaro"],
}

FETCH_COMMENTS = True    # False면 게시글만 수집 (빠르지만 데이터 적음)
DELAY          = 2.0     # 요청 간 딜레이(초)
SAVE_EVERY     = 800     # 몇 행마다 중간 저장할지
SORT_TYPES     = ["new"] # 정렬 방식 (top 추가 시: ["new", "top"])

HEADERS = {"User-Agent": "Mozilla/5.0 (research-crawler/1.0)"}

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

DEMO_PATTERN = re.compile(
    r'\b(\d{1,2})(F|M|f|m)\b|\b(F|M|f|m)(\d{1,2})\b'
)
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
# 기간 입력
# ================================================================

def input_date_range():
    print("\n" + "="*50)
    print("📅 수집 기간 설정")
    print("="*50)

    # 기존 CSV에서 마지막 저장 날짜 자동 감지
    resume_date = None
    for drug_type in SUBREDDITS.keys():
        filepath   = f"{drug_type}_reddit.csv"
        last_date  = get_last_saved_date(filepath)
        if last_date:
            if resume_date is None or last_date < resume_date:
                resume_date = last_date

    if resume_date:
        print(f"\n  🔍 기존 수집 데이터 감지!")
        print(f"     마지막으로 저장된 데이터: {resume_date} 까지")
        print(f"     → 시작일을 {resume_date} 로 자동 설정할 수 있습니다.")
        use_resume = input(f"\n  이어서 수집할까요? (y/n): ").strip().lower()
        if use_resume == "y":
            start_str = resume_date
            print(f"  ✅ 시작일 자동 설정: {start_str}")
        else:
            print()
            print("  권장 기간 분할 예시:")
            print("    1구간: 2025-01-01 ~ 2026-04-06  ← 최신")
            print("    2구간: 2024-01-01 ~ 2024-12-31")
            print("    3구간: 2023-01-01 ~ 2023-12-31")
            print("    4구간: 2022-05-01 ~ 2022-12-31")
            print()
            while True:
                try:
                    start_str = input("  시작일 입력 (YYYY-MM-DD): ").strip()
                    datetime.strptime(start_str, "%Y-%m-%d")
                    break
                except ValueError:
                    print("  ❌ 형식이 올바르지 않습니다. 예: 2025-01-01")
    else:
        print()
        print("  권장 기간 분할 예시:")
        print("    1구간: 2025-01-01 ~ 2026-04-06  ← 최신")
        print("    2구간: 2024-01-01 ~ 2024-12-31")
        print("    3구간: 2023-01-01 ~ 2023-12-31")
        print("    4구간: 2022-05-01 ~ 2022-12-31")
        print()
        while True:
            try:
                start_str = input("  시작일 입력 (YYYY-MM-DD): ").strip()
                datetime.strptime(start_str, "%Y-%m-%d")
                break
            except ValueError:
                print("  ❌ 형식이 올바르지 않습니다. 예: 2025-01-01")

    while True:
        try:
            end_str = input("  종료일 입력 (YYYY-MM-DD): ").strip()
            datetime.strptime(end_str, "%Y-%m-%d")
            if end_str <= start_str:
                break
            else:
                print("  ❌ 종료일이 시작일보다 나중입니다. 종료일은 시작일보다 과거여야 합니다.")
        except ValueError:
            print("  ❌ 형식이 올바르지 않습니다. 예: 2025-01-01")

    # start_str이 더 최신, end_str이 더 과거
    # 필터링은 end_ts <= created_utc <= start_ts 로 동작
    start_ts = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp()) + 86399
    end_ts   = int(datetime.strptime(end_str,   "%Y-%m-%d").timestamp())

    print(f"\n  ✅ 수집 기간: {end_str} ~ {start_str}")
    return start_str, end_str, end_ts, start_ts  # end_ts가 min, start_ts가 max

# ================================================================
# 중복 방지: 기존 CSV에서 수집된 ID + 마지막 날짜 로드
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

def get_last_saved_date(filepath: str) -> Optional[str]:
    """기존 CSV에서 가장 오래된 timestamp 반환 (수집이 어디까지 됐는지 파악)"""
    if not os.path.exists(filepath):
        return None
    oldest = None
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = row.get("timestamp", "")
            if ts:
                if oldest is None or ts < oldest:
                    oldest = ts
    return oldest[:10] if oldest else None  # YYYY-MM-DD 반환

# ================================================================
# CSV 저장 + 마지막 날짜 출력
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
    """버퍼에서 가장 마지막(오래된) timestamp 반환"""
    timestamps = [r["timestamp"] for r in rows if r.get("timestamp")]
    if not timestamps:
        return "알 수 없음"
    # ISO 형식 문자열 정렬 → 가장 오래된 날짜
    oldest = min(timestamps)
    return oldest[:10]  # YYYY-MM-DD 만 반환

# ================================================================
# API 요청
# ================================================================

def fetch_json(url: str) -> Optional[dict]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print(f"\n  ⚠️  [Rate limit] 60초 대기 후 재시도...")
            time.sleep(60)
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
    comments: list,
    thread_id: str,
    parent_id: str,
    depth: int,
    parent_path: str,
    drug_type: str,
    subreddit: str,
    rows: List[dict],
    existing_ids: set,
    start_ts: int,
    end_ts: int,
):
    for item in comments:
        if item.get("kind") == "more":
            continue

        data        = item.get("data", {})
        comment_id  = data.get("id", "")

        if comment_id in existing_ids:
            continue

        created_utc = data.get("created_utc", 0)
        if not (start_ts <= created_utc <= end_ts):
            continue

        body         = data.get("body", "")
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
                thread_id=thread_id,
                parent_id=comment_id,
                depth=depth + 1,
                parent_path=current_path,
                drug_type=drug_type,
                subreddit=subreddit,
                rows=rows,
                existing_ids=existing_ids,
                start_ts=start_ts,
                end_ts=end_ts,
            )

# ================================================================
# 게시글 + 댓글 수집
# ================================================================

def fetch_post_with_comments(
    subreddit: str, post: dict, drug_type: str,
    existing_ids: set, start_ts: int, end_ts: int,
) -> List[dict]:
    rows        = []
    post_id     = post.get("id", "")
    selftext    = post.get("selftext", "")
    permalink   = post.get("permalink", "")
    created_utc = post.get("created_utc", 0)

    if post_id not in existing_ids and start_ts <= created_utc <= end_ts:
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

    data = fetch_json(
        f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
    )
    if data and isinstance(data, list) and len(data) > 1:
        parse_comment_tree(
            data[1].get("data", {}).get("children", []),
            thread_id=post_id,
            parent_id=post_id,
            depth=1,
            parent_path=post_id,
            drug_type=drug_type,
            subreddit=subreddit,
            rows=rows,
            existing_ids=existing_ids,
            start_ts=start_ts,
            end_ts=end_ts,
        )

    time.sleep(DELAY)
    return rows

# ================================================================
# 서브레딧 수집
# ================================================================

def crawl_subreddit(
    subreddit: str, drug_type: str, filepath: str,
    existing_ids: set, start_ts: int, end_ts: int,
    start_str: str, end_str: str,
) -> int:
    print(f"\n{'='*50}")
    print(f"[{drug_type.upper()}] r/{subreddit}  ({start_str} ~ {end_str})")

    buffer      = []
    total_saved = 0

    for sort in SORT_TYPES:
        print(f"\n  정렬: {sort}")
        after = None
        stop  = False

        while not stop:
            url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit=100"
            if sort == "top":
                url += "&t=all"
            if after:
                url += f"&after={after}"

            data = fetch_json(url)
            if not data:
                break

            children = data.get("data", {}).get("children", [])
            if not children:
                break

            for child in children:
                post        = child.get("data", {})
                created_utc = post.get("created_utc", 0)

                if sort == "new" and created_utc < start_ts:
                    print(f"\n  → 기간 이전 게시글 도달, 중단")
                    stop = True
                    break

                rows = fetch_post_with_comments(
                    subreddit, post, drug_type,
                    existing_ids, start_ts, end_ts,
                )
                buffer.extend(rows)

                # 800행마다 저장
                if len(buffer) >= SAVE_EVERY:
                    last_date  = get_last_date(buffer)
                    save_csv(buffer, filepath)
                    total_saved += len(buffer)

                    print(f"\n  💾 중간 저장 완료")
                    print(f"     - 이번 실행 누적: {total_saved}행")
                    print(f"     - 현재까지 수집된 데이터: {last_date} 까지")

                    buffer.clear()

            after = data.get("data", {}).get("after")
            if not after:
                break

            time.sleep(DELAY)

    # 남은 버퍼 저장
    if buffer:
        last_date = get_last_date(buffer)
        save_csv(buffer, filepath)
        total_saved += len(buffer)
        print(f"\n  💾 저장 완료")
        print(f"     - 이번 실행 누적: {total_saved}행")
        print(f"     - 현재까지 수집된 데이터: {last_date} 까지")
        buffer.clear()

    return total_saved

# ================================================================
# 메인
# ================================================================

def main():
    print("\n🔍 Reddit 부작용 데이터 크롤러")

    start_str, end_str, start_ts, end_ts = input_date_range()

    print("\n수집 대상 서브레딧:")
    for drug, subs in SUBREDDITS.items():
        for s in subs:
            print(f"  - r/{s} ({drug})")

    input("\n▶️  Enter를 누르면 수집을 시작합니다...")

    grand_total = 0

    for drug_type, subreddit_list in SUBREDDITS.items():
        filepath     = f"{drug_type}_reddit.csv"
        existing_ids = load_existing_ids(filepath)

        for subreddit in subreddit_list:
            saved = crawl_subreddit(
                subreddit=subreddit,
                drug_type=drug_type,
                filepath=filepath,
                existing_ids=existing_ids,
                start_ts=start_ts,
                end_ts=end_ts,
                start_str=start_str,
                end_str=end_str,
            )
            grand_total += saved

    print("\n" + "="*50)
    print(f"🎉 수집 완료!")
    print(f"   이번 실행 총 수집: {grand_total}행")
    print(f"   저장 파일: wegovy_reddit.csv / mounjaro_reddit.csv")
    print("="*50)

if __name__ == "__main__":
    main()