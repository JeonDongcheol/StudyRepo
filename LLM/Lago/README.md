# LiteLLM

> LLM Metric & Billing을 담당하는 Lago에 대한 정리

## Lago with Helm

### Prerequisite

    기존 Database(PostgreSQL)과 Redis를 바라보게 설정할 것이기 때문에, PostgresQL 및 Redis를 미리 배포하고, Helm을 통해 생성할 테이블을 만들 Database를 미리 만들어 두어야 함.

### Deploy by Helm

1. Clone Lago Helm
    ```shell
    git clone -b ${TAG} https://github.com/getlago/lago-helm-charts.git

    cd lago-helm-charts
    ```

2. Set values.yaml file

    ```yaml
    # 수정 내역만 정리
    version: '1.12.2' # Lago Version

    apiUrl: api # 기본 Domain 뒤에 붙는 Lago API Endpoint
    frontUrl: ui # 기본 Domain 뒤에 붙는 Lago Front Endpoint

    # 기존에 있는 Redis를 사용하기 위해 해당 설정은 Off
    redis:
      enabled: false # true 설정을 하면 Lago를 위해 Redis가 새롭게 배포됨
      # ...
    
    # 기존의 PostgreSQL을 사용하기 위해 마찬가지로 설정을 off
    postgresql:
      enabled: false

    global:
      # Database URL 설정 : postgresql://${USERNAEM}:${PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}
      databaseUrl: postgresql://{username}:{password}@postgresql.database.svc.cluster.local:5432/{database_name}

      # Redis URL 설정 : redis://${USERNAME}:${PASSWORD}@${REDIS_HOST}:${REDIS_PORT}
      redisUrl: redis://{username}:{password}@redis-master.redis.svc.cluster.local:6379

      # databaseUrl을 설정했기 때문에 건너뜀
      postgresql:
        # ...

      signup:
        enabled: true # 배포된 환경에서 테스트를 위해 회원가입해야하므로 true 설정

      # ...
      kubectlVersion: 1.29 # Lago 배포할 때 bitnami의 kubectl 이미지를 가져오는데, 잘못 설정하면 InvalidImageName Error 발생

    # ...
    ```

3. [If Required] Edit Chart.yaml

    `Chart.yaml` 안에 __Minio__ 관련 설정이 있는데, Minio 설정을 `charts` 디렉토리 안에 설정을 해주거나 Chart.yaml 파일에서 minio 설정을 제외시켜야 함

    Minio를 사용하지 않기 때문에 Chart.yaml 에서 minio 설정 제외

    ```yaml
    # 해당 내용으로 덮어 쓰거나, minio 관련 부분부터 전부 주석 처리
    apiVersion: v2
    appVersion: '1.12.2'
    description: the Lago open source billing app
    name: lago
    version: 1.12.2
    dependencies:
    - name: postgresql
        version: '13.2.2'
        repository: https://charts.bitnami.com/bitnami
        condition: postgresql.enabled
    - name: redis
        version: '18.2.1'
        repository: https://charts.bitnami.com/bitnami
        condition: redis.enabled
    ```

4. [If Required] Edit storage-data-persistentvolumeclaim.yaml

    Helm 배포 과정에서 `templates/storage-data-persistentvolumeclaim.yaml` 의 첫 번째 조건문에서 오류가 발생할 수 있음.
    
    해당 부분을 다음과 같이 수정 진행

    ```yaml
    {{- if not .Values.global.s3.enabled -}}
    # 나머지 동일
    {{- end -}}
    ```

5. Deploy by Helm

    ```shell
    helm install ${RELEASE_NAME} . -n ${NAMESPACE}

    watch 'kubectl get pod -n ${NAMESPACE}`
    ```

6. Edit Worker & Event Worker Deployment

    Lago 배포를 하게 되면 아래의 항목들이 배포

    - __Deployment__
    
        1. lago-api
        2. lago-clock
        3. lago-events-worker
        4. lago-front
        5. lago-pdf
        6. lago-worker

    - __Job__ (Database 초기화 담당)

        1. lago-migrate

    `lago-migrate` Job은 __Database Initializing__ 을 수행하는데, 기존에 해당 Database 안에 Table이 남아 있다면, 모두 지워야 함

    또한, `lago-events-worker` 및 `lago-worker` 에서 _liveness-probe_ 을 실행하는 과정에서 Timeout이 Default(1초)로 설정되어 있는데, 해당 커맨드를 수행하는 과정에서 1초 이상의 시간이 걸려 __CrashLoopBackOff__ Error 를 발생시킴.

    따라서 두 개의 Deployment를 수정해서 재배포 수행

    `lago-worker` (lago-events-worker도 동일하게 수행)

    ```shell
    kubectl edit deployment -n ${NAMESPACE} lago-worker
    ```
    
    ```yaml
    # ...
    spec:
      containers:
      - args:
        # ...
        # 해당 부분 수정
        livenessProbe:
          exec:
            command:
            - /bin/bash
            - -l
            - -c
            - bundle exec sidekiqmon processes | grep $(hostname) || exit 1
          failureThreshold: 3
          periodSeconds: 10
          successThreshold: 1
          timeoutSeconds: 5 # 해당 부분 수정
        # ...
    ```

---

## Report

### 1. Lago UI에서 Developers > API keys & ID 화면이 정상적으로 출력되지 않는 현상

__현상__ : Lago API를 사용하기 위해 Lago API Key를 조회해야하는데, UI에서 정상적으로 조회되지 않음

__원인__ : 현재 파악 중

Lago API Key를 발급받기 위해 `Postman` 을 기반으로 __GraphQL API__ 호출

- API Key 조회 과정

    1. Lago Login in UI
    
        Lago UI에서 새롭게 회원가입 후 로그인 진행하게 되면 나오는 _Authorization Bearer_ Token 값 및 _X-Lago-Organization_ 값 확인

    2. Set Authorization & X-Lago-Organization in Postman

        Postman 안에서 _Auth Type_ 을 __Bearer Token__ 으로 설정하고, Token 값을 사전에 확인한 Token 값으로 설정

        또한, Headers 부분에 __X-Lago-Organization__ 필드를 새롭게 추가하고 사전에 확인한 값으로 설정

    3. Set Body

        ```graphql
        query getOrganizationApiKey{
            organization {
                id
                apiKey
            }
        }
        ```

    4. Send Request

        __POST__ Method로 해당 API를 호출하게 되면 API Key 값 확인 가능

        ```json
        {
            "data": {
                "organization": {
                    "id": "organization_id",
                    "apiKey": "use_this_key_for_calling_lago_api"
                }
            }
        }
        ```
