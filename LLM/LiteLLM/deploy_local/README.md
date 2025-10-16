# 1. LiteLLM Local 환경 실행

## 1-1. PostgreSQL 설치 및 배포

LiteLLM Database 사용을 위한 PostgreSQL 설치

### HomeBrew를 통한 PostgreSQL 설치

```bash
brew install postgresql@16 # PostgreSQL 16 버전 설치

# PostgreSQL 16버전 기본으로 사용
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

postgres --version # PostgreSQL Version 체크 (16.10)

brew services start postgresql@16 # PostgreSQL 서비스 백그라운드 실행
brew services list # 서비스 정상 실행 여부 체크

psql -U postgres
```

### [Optional] PostgreSQL이 정상적으로 실행되지 않는 경우

1. `brew services list` 이후 PostgreSQL 16의 상태가 `error` 인 경우
    
    ```bash
    brew services stop postgresql@16 # 서비스 중지
    rm -rf /opt/homebrew/var/postgresql@16/* # PostgreSQL 16 디렉토리 삭제
    initdb --locale=en_US.UTF-8 -E UTF-8 /opt/homebrew/var/postgresql@16 # 재초기화
    ```
    
2. 사용자 `postgres` 접속이 되지 않는 경우
    
    ```bash
    psql -d postgres # PostgreSQL Database로 접속
    ```
    
    ```sql
    CREATE ROLE postgres WITH LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD 'PASSWORD';
    ```
    

### [Optional] 테스트를 위한 테이블 생성

```sql
CREATE DATABASE litellm_temp_01;
```

## 1-2. Python 기반 LiteLLM 설치

### 파이썬 환경 설정

`PyEnv`를 통한 기본 파이썬 환경 설정 (3.12.10)

```bash
pyenv local 3.12.10
python --version # [Optional] Python 버전 체크
python -m venv venv # 파이썬 가상 환경 설정

source venv/bin/activate # 가상환경 실행 
```

### 기본 패키지 설치

```bash
pip install --upgrade pip # Upgrade PyPi version
pip install litellm openai prisma # LiteLLM, OpenAI, Prisma라이브러리 설치
pip install 'litellm[proxy]'
```

## 1-3. LiteLLM 실행을 위한 환경 설정 파일 생성

### 환경 변수 설정

`.env` 파일에 기본 환경 변수 파일 생성 (LiteLLM Master Key, Database URL 정보)

```bash
vi .env
```

```bash
LITELLM_MASTER_KEY=sk-****
DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/litellm_temp_01
STORE_MODEL_IN_DB=true
```

### Prisma 스키마 적용

LiteLLM Prisma Schema 파일 다운로드 후 적용

[[LiteLLM Prisma Schema Github Link]](https://github.com/BerriAI/litellm/blob/main/schema.prisma)

```bash
python -m prisma generate
python -m prisma db push # Database 테이블 초기 생성
```

### Config YAML 파일 생성

```bash
vi config.yaml
```

`model_list` 는 부가적인 설정으로 Default 모델을 넣는 부분

`master_key` 는 `.env` 파일에서 설정했던 **LITELLM_MASTER_KEY** 값

```bash
general_settings:
  master_key: sk-****
  database_url: "postgresql://postgres:PASSWORD@localhost:5432/litellm_temp_01"
model_list:
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4
      api_key: os.environ/OPENAI_API_KEY
```

## 1-4. LiteLLM 실행

### Local 환경에서 실행

```bash
litellm --config config.yaml --port 4000
```

# 2. LiteLLM UI 접속 후 확인

[`localhost:4000/ui`](http://localhost:4000/ui) 에 접속하여 아래와 같은 계정 정보로 로그인하면 LiteLLM UI 접속 가능

- ID: admin
- Password: sk-**** (Master Key)

**[Teams]** 탭으로 이동하여 새롭게 팀 추가

**[Models + Endpoints]** 탭으로 이동하여 기존 모델 연동

**[Virtual Keys]** 탭으로 이동하여 API Key 기반의 LiteLLM을 활용하여 모델 통신을 할 수 있도록 키 발급

# 3. API 테스트

Postman을 활용한 LiteLLM API 테스트

- 모델: Perplexity Sonar Pro 모델
- API Endpoint: `/v1/chat/completions`
- 추가 내용: Master Key가 아닌, 발급 받은 Virtual Key를 통한 API 테스트 진행

### Request Body

```json
{
  "model": "dcjeon-sonar-pro",
  "messages": [
    {
      "role": "system",
      "content": "사용자의 질문에 대하여 # 카테고리\n# 핵심 내용\n# 전체 내용 요약\n# 키워드 형태로 알려주세요."
    },
    {
      "role": "user",
      "content": "최근 1주일 동안 서울 날씨에 대해서 알려주세요."
    }
  ]
}
```

### Response Body

```json
{
  "id": "91369226-0506-40a2-9afa-ef2ed624770a",
  "created": 1760594995,
  "model": "perplexity/sonar-pro",
  "object": "chat.completion",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "# 카테고리\n최근 서울 날씨 (2025년 10월 9일~16일)\n\n# 핵심 내용\n최근 일주일간 서울은 **비가 자주 내리고 ...m\n- **기온 변동**: 최저 15.7℃ ~ 최고 28.0℃\n- **잦은 강수**: 일주일 중 5일 비 기록\n- **흐린 날씨**: 평균 운량 9.0~10.0 지속\n- **급격한 기온 하강**: 10월 10일 크게 하락\n- **불안정한 날씨 패턴**: 비-회복-비 반복",
        "role": "assistant"
      },
      "provider_specific_fields": {
        "delta": {
          "role": "assistant",
          "content": ""
        }
      }
    }
  ],
  "usage": {
    "completion_tokens": 644,
    "prompt_tokens": 48,
    "total_tokens": 692,
    "cost": {
      "input_tokens_cost": 0,
      "output_tokens_cost": 0.01,
      "request_cost": 0.006,
      "total_cost": 0.016
    },
    "search_context_size": "low"
  },
  "citations": [
    "https://www.weather.go.kr/w/observation/land/past-obs/obs-by-day.do",
    "https://ko.allmetsat.com/weather-forecast/south-korea.php?city=seoul-kr",
    "..."
  ],
  "search_results": [
    {
      "title": "과거관측 - 일별자료 - 기상청 날씨누리",
      "url": "https://www.weather.go.kr/w/observation/land/past-obs/obs-by-day.do",
      "date": "2024-01-01",
      "last_updated": "2025-10-16",
      "snippet": "일별자료 ; 1일, 2일 ; 평균기온:20.5℃ 최고기온:25.6℃ 최저기온:16.7℃ 평균운량:4.8 일강수량: -, 평균기온:21.4℃ 최고기온:25.8℃ 최저기온:17.3℃ 평균운량:9.0 일강수량: -",
      "source": "web"
    },
    {
	    "...": "..."
    }
  ]
}
```
