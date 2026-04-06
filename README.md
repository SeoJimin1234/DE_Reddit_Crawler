# Reddit 크롤러 사용 가이드

위고비(Wegovy) / 마운자로(Mounjaro) 부작용 데이터 수집을 위한 Reddit JSON API 크롤러입니다.

---

## 📁 파일 구성

```
project/
├── reddit_crawler.py   # 수집 코드
└── README.md
```

---

## 👥 팀원별 수집 분담

> 각자 담당 기간을 실행 시 입력하면 됩니다. 서브레딧은 코드가 자동으로 전체 수집합니다.

| 이름 | 수집 기간 | 상태 |
|------|----------|------|
| 서지민 | 2025-01-01 ~ 2026-04-06 | 수집 중 |
| 서지민 | 2024-01-01 ~ 2024-12-31 | 위 완료 후 추가 수집 |
| 김민영 | 2022-05-01 ~ 2022-08-31 | |
| 김서영 | 2022-09-01 ~ 2022-12-31 | |
| 김형신 | 2023-01-01 ~ 2023-06-30 | |
| 남재은 | 2023-07-01 ~ 2023-12-31 | |

> **CSV 파일 합치기**: 각자 수집 완료 후 `wegovy_reddit.csv`, `mounjaro_reddit.csv` 파일을 취합 담당자(서지민)에게 전달하면 됩니다. `document_id` 기준으로 중복 제거 후 합칩니다.

---

## ⚙️ 환경 설정

### 1. 레포지토리 클론

터미널(Mac) 또는 명령 프롬프트/PowerShell(Windows)을 열고 아래 명령어를 실행합니다.

```bash
git clone https://github.com/SeoJimin1234/DE_Reddit_Crawler.git
cd DE_Reddit_Crawler
```

> Git이 없다면 [git-scm.com](https://git-scm.com/downloads) 에서 설치하세요.

### 2. VSCode 설치 및 열기

[VSCode 다운로드](https://code.visualstudio.com/) 후 프로젝트 폴더를 열어주세요.

VSCode 상단 메뉴 → `Terminal` → `New Terminal` 로 터미널을 열 수 있습니다.

### 2. Python 버전 확인

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

### 3. 가상환경 생성 및 활성화

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

> **Windows 오류 대응**: 활성화 시 `cannot be loaded because running scripts is disabled` 오류가 나면 아래 명령어 실행 후 다시 시도하세요.
> ```bash
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. 라이브러리 설치

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

실행하면 기존 CSV가 있을 경우 자동으로 감지해 이어서 수집할지 물어봅니다.

```
🔍 기존 수집 데이터 감지!
   마지막으로 저장된 데이터: 2025-08-15 까지
   → 시작일을 2025-08-15 로 자동 설정할 수 있습니다.

이어서 수집할까요? (y/n):
```

처음 실행이거나 새 기간을 수집할 경우 날짜를 직접 입력합니다.

```
시작일 입력 (YYYY-MM-DD): 2025-01-01
종료일 입력 (YYYY-MM-DD): 2026-04-06
```

Enter를 누르면 수집이 시작됩니다.

### 수집 완료 시 생성되는 파일

```
project/
├── reddit_crawler.py
├── README.md
├── wegovy_reddit.csv       # r/Wegovy + r/WegovyWeightLoss 수집 결과
└── mounjaro_reddit.csv     # r/Mounjaro 수집 결과
```

각 CSV는 실행할 때마다 **기존 파일에 이어서 저장**됩니다. 덮어쓰지 않으므로 안심하고 재실행해도 됩니다.

---

## 💾 자동 저장 및 휴식

**800행마다 자동으로 CSV에 저장 후 10~15분 휴식**합니다.
중간에 프로그램이 꺼져도 저장된 데이터는 유지됩니다.

```
💾 중간 저장 완료
   - 이번 실행 누적: 800행
   - 현재까지 수집된 데이터: 2025-03-12 까지
⏸️  12분 휴식 후 재개...
▶️  수집 재개
```

---

## 🔄 중단 후 재실행

컴퓨터가 꺼지거나 예기치 않게 중단됐을 때 **그냥 다시 실행**하면 됩니다.

재실행 시 기존 CSV를 자동으로 읽어 마지막으로 저장된 날짜를 감지하고, 거기서부터 이어서 수집합니다. 이미 수집된 데이터는 자동으로 스킵되므로 중복이 생기지 않습니다.

```
🔍 기존 수집 데이터 감지!
   마지막으로 저장된 데이터: 2025-08-15 까지

이어서 수집할까요? (y/n): y
✅ 시작일 자동 설정: 2025-08-15
```

---

## 🖥️ 터미널 메시지 설명

| 메시지 | 의미 |
|--------|------|
| `🔍 기존 수집 데이터 감지!` | 기존 CSV 발견, 마지막 저장 날짜 표시 |
| `이어서 수집할까요? (y/n)` | y: 마지막 날짜부터 자동 시작 / n: 날짜 직접 입력 |
| `▶️  Enter를 누르면 수집을 시작합니다` | Enter 누르면 수집 시작 |
| `📂 기존 수집 N건 로드 (중복 스킵)` | 이전 수집 데이터 불러옴, 중복 자동 방지 |
| `[WEGOVY] r/Wegovy (날짜 ~ 날짜)` | 해당 서브레딧 수집 시작 |
| `정렬: new` | 최신순으로 게시글 수집 중 |
| `정렬: top` | 인기순으로 게시글 수집 중 |
| `→ 기간 이전 게시글 도달, 중단` | 시작일보다 오래된 글 도달 → 자동 중단 (정상) |
| `⚠️  [Rate limit] 60초 대기 후 재시도` | Reddit 요청 차단 → 60초 후 자동 재시도 (정상) |
| `💾 중간 저장 완료` | 800행 모여서 CSV에 저장됨 |
| `현재까지 수집된 데이터: YYYY-MM-DD 까지` | 저장된 데이터 중 가장 오래된 날짜 |
| `⏸️  N분 휴식 후 재개` | rate limit 방지를 위한 자동 휴식 중 |
| `▶️  수집 재개` | 휴식 끝, 수집 다시 시작 |
| `🎉 수집 완료!` | 담당 기간 전체 수집 완료 |

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

## ❗ 주의사항

- `DELAY = 2.0` 이하로 낮추면 rate limit이 자주 걸릴 수 있습니다
- 추후 Reddit 앱이 승인되면 PRAW로 교체 시 수집 속도가 4~6배 향상됩니다

---

## 🐛 자주 발생하는 오류

| 오류 | 원인 | 해결 |
|------|------|------|
| `[Rate limit] 60초 대기` | 요청 과다 | 자동 재시도, 기다리면 됨 |
| `게시글 0개 수집됨` | 서브레딧 이름 오타 | 대소문자 확인 |
| `HTTP 403` | Reddit 접근 차단 | 잠시 후 재실행 |
| `ModuleNotFoundError: requests` | 라이브러리 미설치 | `pip install requests` |
| `cannot be loaded because running scripts is disabled` | Windows 보안 정책 | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` 실행 |
| `python3: command not found` (Windows) | python3 명령어 미지원 | `python` 으로 대체 |
