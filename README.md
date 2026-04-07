# Reddit 크롤러 사용 가이드

위고비(Wegovy) / 마운자로(Mounjaro) 부작용 데이터 수집을 위한 Reddit 크롤러입니다.

---

## 📌 현재 수집 방식에 대해

### 현재 수집 전략

1,000개 제한을 우회하기 위해 **정렬 방식을 다각화**하여 수집합니다. 각 정렬은 서로 다른 게시글을 반환하므로, 중복 제거 후 더 많은 데이터를 확보할 수 있습니다.

| 정렬 | 수집 내용 |
|------|---------|
| `new` | 최신 게시글 |
| `hot` | 현재 화제 게시글 |
| `top(all)` | 역대 인기 게시글 |
| `top(year)` | 최근 1년 인기 게시글 |

중복되는 `document_id`는 자동으로 스킵됩니다.

---

## 👥 역할 분담

| 이름 | 담당 서브레딧 |
|------|-------------|
| 김민영 | r/Wegovy (1번) |
| 김서영 | r/WegovyWeightLoss (2번) |
| 김형신 | r/Mounjaro (3번) |
| 남재은 | 위 완료된 것 중 남은 것 보조 |

> 각자 담당 서브레딧 1개씩 실행하면 됩니다.

---

## ⚙️ 환경 설정

### 1. 레포지토리 클론

```bash
git clone https://github.com/SeoJimin1234/DE_Reddit_Crawler.git
cd DE_Reddit_Crawler
```

> Git이 없다면 [git-scm.com](https://git-scm.com/downloads) 에서 설치하세요.

### 2. VSCode 설치 및 열기

[VSCode 다운로드](https://code.visualstudio.com/) 후 클론한 폴더를 열어주세요.

VSCode 상단 메뉴 → `Terminal` → `New Terminal` 로 터미널을 열 수 있습니다.

### 3. Python 버전 확인

Python **3.9 이상** 필요합니다.

**Mac**
```bash
python3 --version
```

**Windows**
```bash
python --version
```

> Python이 없다면 [python.org](https://www.python.org/downloads/) 에서 설치하세요.
> Windows 설치 시 **"Add Python to PATH"** 체크박스를 반드시 선택해야 합니다.

### 4. 가상환경 생성 및 활성화

**Mac**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

> 활성화 후 터미널 앞에 `(.venv)` 가 표시되면 정상입니다.

> **Windows 오류 대응**: `cannot be loaded because running scripts is disabled` 오류가 나면 아래 명령어 실행 후 다시 시도하세요.
> ```bash
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 5. 라이브러리 설치

```bash
pip install requests
```

---

## 🚀 실행 방법

**Mac**
```bash
python3 reddit_crawler.py
```

**Windows**
```bash
python reddit_crawler.py
```

실행하면 수집할 서브레딧을 선택합니다.

```
📌 수집할 서브레딧 선택
  1. r/Wegovy              →  wegovy_reddit.csv
  2. r/WegovyWeightLoss    →  wegovyweightloss_reddit.csv
  3. r/Mounjaro            →  mounjaro_reddit.csv

번호 입력 (1/2/3):
```

담당 번호를 입력하고 Enter를 누르면 `top(all) → top(year) → hot → new` 순서로 자동 수집이 시작됩니다.

---

## 수집 완료 시 생성되는 파일

```
project/
├── reddit_crawler.py
├── README.md
├── wegovy_reddit.csv             # r/Wegovy 수집 결과
├── wegovyweightloss_reddit.csv   # r/WegovyWeightLoss 수집 결과
└── mounjaro_reddit.csv           # r/Mounjaro 수집 결과
```

각 CSV는 실행할 때마다 **기존 파일에 이어서 저장**됩니다. 덮어쓰지 않으므로 안심하고 재실행해도 됩니다.

---

## 💾 자동 저장

**800행마다 자동으로 CSV에 저장**합니다.
중간에 프로그램이 꺼져도 저장된 데이터는 유지되며, 재실행 시 이어서 수집합니다.

```
💾 중간 저장 완료
   - 이번 실행 누적: 800행
   - 현재까지 수집된 데이터: 2025-03-12 까지
```

---

## 🔄 중단 후 재실행

중간에 끊겼을 때 **그냥 다시 실행**하면 됩니다.
기존 CSV의 `document_id`를 자동으로 읽어 이미 수집된 데이터는 스킵합니다.

```
📂 기존 수집 1600건 로드 (중복 스킵)
```

---

## 🖥️ 터미널 메시지 설명

| 메시지 | 의미 |
|--------|------|
| `📌 수집할 서브레딧 선택` | 번호 입력 대기 중 |
| `▶️  Enter를 누르면 수집을 시작합니다` | Enter 누르면 수집 시작 |
| `📂 기존 수집 N건 로드 (중복 스킵)` | 기존 데이터 불러옴, 중복 자동 방지 |
| `📂 정렬: new` | new 정렬 수집 시작 |
| `📂 정렬: hot` | hot 정렬 수집 시작 |
| `📂 정렬: top(all)` | top(all) 정렬 수집 시작 |
| `📂 정렬: top(year)` | top(year) 정렬 수집 시작 |
| `페이지 N 요청 중...` | N번째 페이지 수집 중 (정상) |
| `→ N 마지막 페이지 도달` | 해당 정렬 수집 완료 |
| `✅ N 완료: N행 추가` | 해당 정렬 완료 및 추가 수집량 |
| `⚠️  [Rate limit] 5분 대기 후 재시도` | Reddit 요청 차단 → 5분 후 자동 재시도 (정상) |
| `[오류] HTTP 403` | Reddit IP 차단 → 다른 와이파이로 변경 후 재실행 |
| `💾 중간 저장 완료` | 800행 모여서 CSV에 저장됨 |
| `현재까지 수집된 데이터: YYYY-MM-DD 까지` | 저장된 데이터 중 가장 오래된 날짜 |
| `🎉 수집 완료!` | 전체 수집 완료 |

---

## 📋 수집 컬럼 설명

| 컬럼명 | 설명 |
|--------|------|
| `document_id` | 게시글/댓글 고유 ID |
| `platform` | 데이터 출처 (`Reddit` 고정) |
| `drug_type` | 약물 분류 (`wegovy` / `mounjaro`) |
| `subreddit` | 수집한 서브레딧 이름 |
| `text_body` | 본문 텍스트 (분석 핵심 데이터) |
| `author_id` | 작성자 ID |
| `timestamp` | 작성 시간 (ISO 8601 형식) |
| `score` | 추천수 (Upvote - Downvote) |
| `thread_id` | 최상위 원본 게시글 ID |
| `parent_id` | 바로 위 부모 글 ID (게시글은 `null`) |
| `depth_level` | 계층 깊이 (게시글=0, 댓글=1, 대댓글=2, ...) |
| `path` | 루트부터 현재까지 ID 경로 |
| `user_demographics` | 본문 추출 나이/성별 (예: `30F`, `45M`) |
| `medication_timeline` | 본문 추출 투여 정보 (예: `Week 4`, `2.5mg`) |
| `post_title` | 게시글 제목 (댓글은 빈 값) |
| `url` | 원문 링크 |

---

## 🐛 자주 발생하는 오류

| 오류 | 원인 | 해결 |
|------|------|------|
| `[Rate limit] 5분 대기` | 요청 과다 | 자동 재시도, 기다리면 됨 |
| `[오류] HTTP 403` | Reddit IP 차단 | 다른 와이파이로 변경 후 재실행 |
| `ModuleNotFoundError: requests` | 라이브러리 미설치 | `pip install requests` |
| `cannot be loaded because running scripts is disabled` | Windows 보안 정책 | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` 실행 |
| `python3: command not found` (Windows) | python3 명령어 미지원 | `python` 으로 대체 |