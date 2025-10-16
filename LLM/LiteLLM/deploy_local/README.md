# LiteLLM Local 환경 배포

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
