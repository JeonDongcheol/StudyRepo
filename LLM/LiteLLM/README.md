# LiteLLM

> AI Serving Gateway인 LiteLLM과 Billing&Metering을 처리하는 Lago을 LiteLLM과 함께 사용한 내용

> 추가로 kubernetes 환경에서 배포한 내용 정리

## LiteLLM을 통한 Model API 호출 방법

### cURL 기반 LiteLLM 호출

```shell
curl -v ${LITELLM_URL}/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${LITELLM_API_KEY}" \
  -d '{
    "input": ["LiteLLM Sample input", "Here is input Data."],
    "model": "kserve/gte-large/v1"
  }'
```

### LiteLLM SDK in Python

> PyPi 패키지 이름 : litellm

LiteLLM Python SDK에서 쓰이는 함수는 `completion` 과 `embedding()` 으로, completion() 함수는 LLM 모델을 호출하는 함수이고, embedding() 함수는 Embedding Model을 호출하는 함수

`site-packages > litellm > main.py` 에서 completion()과 embedding() 함수에 대한 부분을 확인할 수 있는데, __OpenAI 파라미터__ , __LiteLLM 파라미터__ 구분되어 있으며, _Provider_ 에 따라 각각에 맞는 embedding() 함수를 호출하여 처리

- Embedding Method Parameters
        
    1. model : __Provider__ + LiteLLM의 __Public Model Name__ (ex. HuggingFace Provider 기반의 Public Model Name이 sample인 경우 : huggingface/sample)

    2. api_key[Optional] : LiteLLM의 API key

    3. input : 보낼 Input Data
    
    4. api_base : LiteLLM의 기본 URL > 추후 이를 기반으로 `~/embeddings` endpoint 호출

- Embedding Model Sample

    ```python
    import os
    import litellm
    from litellm import embedding

    # Setting LiteLLM Env
    os.environ["LITELLM_LOG"] = "DEBUG" # Set Log Level

    # Call Embedding Model
    embedding_response = embedding(
        model = "openai/kserve/gte-large/v1",
        api_key = "sk-my-api-key",
        input = ["This is input value", "Hi LiteLLM"],
        api_base = "Lite LLM API URL"
    )

    print(embedding_response)
    ```

    처리 결과

    ```text
    EmbeddingResponse(model='/mnt/models', data=[{'embedding': [0.011290349066257477, -0.044795550405979156
    ...
    0.007092255633324385, -0.032614316791296005], 'index': 1, 'object': 'embedding'}], object='list', usage=Usage(completion_tokens=0, prompt_tokens=16, total_tokens=16))
    ```
---

## LiteLLM + Lago

LiteLLM에서 Logging Callback을 위한 다양한 도구 중 Billing, Metering을 담당하는 Lago 사용 방법

LiteLLM Python SDK에는 Lago를 지원하는 모듈이 있어 이를 사용할 수 있지만, 경우에 따라 Lago SDK 자체를 사용할 수 있음

### 1. LiteLLM Using LiteLLM's Lago Module

- Environment Variables

    1. LAGO_API_KEY : Lago에서 제공되는 API Key
    
    2. LAGO_API_BASE : Lago API URL

    3. LAGO_API_EVENT_CODE : Lago의 __Billable Metric Code__

    4. LAGO_API_CHARGE_BY : 어떤 항목으로 요금을 부과할 것인지 설정 (__End User ID, User ID, Team ID__ 중 택 1)

- LiteLLM's Extra Parameters

    1. proxy_server_request : LiteLLM Proxy Server 쪽에 보내는 Request Body
        
        - Lago의 __Subscription External ID__ 를 해당 파라미터의 `body > user` 에 설정

- Embedding Model Sample

    ```python
    import os
    import litellm
    from litellm import embedding

    # Set LiteLLM Env
    os.environ["LITELLM_LOG"] = "DEBUG"

    # Set Lago Env
    os.environ["LAGO_API_KEY"] = "my-lago-api-key"
    os.environ["LAGO_API_BASE"] = "http://lago-api.url"
    os.environ["LAGO_EVENT_CODE"] = "embedding-metric"
    os.environ["LAGO_API_CHARGE_BY"] = "end_user_id" # end_user_id | user_id | team_id

    litellm.success_callback = ["lago"] # Set LiteLLM's Success Callback to Lago

    embedding_response = embedding(
        model = "openai/kserve/gte-large/v1",
        api_key = "sk-my-api-key",
        input = ["Test Input", "My Lago Test"],
        api_base = "http://my-litellm.com",
        proxy_server_request = {
            "body": {
                "user": "Lago Subscription External ID"
            }
        }
    )

    print(embedding_response)
    ```

### 2. LiteLLM SDK + Lago SDK

- LLM Model Sample

    ```python
    """
    Import LiteLLM's Module
    """
    import uuid
    from lago_python_client.client import Client
    from lago_python_client.exceptions import LagoApiError
    from lago_python_client.models.event import Event

    """
    Same as before
    """
    
    # Do Not Set proxy_server_request Field
    response = litellm.completion(
        model="openai/starcoder",
        messages=[DATA],
        api_base=LITELLM_API_BASE,
        api_key=LLM_API_KEY
    )

    print("# Usage : {}".format(response.usage))

    # Set Lago Client
    lago_client = Client(
        api_key=LAGO_API_KEY,
        api_url=LAGO_API_BASE
    )

    LAGO_EXTERNAL_SUBSCRIPTION_ID="lago-external-subscription-id" # Lago External Subscription ID
    LAGO_METRIC_CODE="dcjeon-metric" # Lago Billable Metric Code

    # Seperate by type (Input/Output Token)

    # Configure Input Event Format
    lago_input_properties = {
        "type": "input",
        "model": "openai/starcoder",
        "tokens": response.usage.prompt_tokens
    }

    # Mapping to Lago Event Class
    try:
        lago_input_event = Event(
            transaction_id=str(uuid.uuid4()),
            external_subscription_id=LAGO_EXTERNAL_SUBSCRIPTION_ID,
            code=LAGO_METRIC_CODE,
            properties=lago_input_properties
        )
    except LagoApiError as e:
        print("Fail to Make Lago Event Format : {}".format(lago_input_properties["type"]))
        raise LagoApiError()

    # Create Lago's Event
    try:
        lago_input_event_response = lago_client.events.create(lago_input_event)
    except LagoApiError as e:
        print("Fail to Create Lago Input Event...")
        raise LagoApiError()

    # Configure Output Event Format
    lago_output_properties = {
        "type": "output",
        "model": "openai/starcoder",
        "tokens": response.usage.completion_tokens
    }

    # Mapping to Lago Event Class
    try:
        lago_output_event = Event(
            transaction_id=str(uuid.uuid4()),
            external_subscription_id=LAGO_EXTERNAL_SUBSCRIPTION_ID,
            code=LAGO_METRIC_CODE,
            properties=lago_output_properties
        )
    except LagoApiError as e:
        print("Fail to Make Lago Event Format : {}".format(lago_output_properties["type"]))

    # Create Lago's Event
    try:
        lago_output_event_response = lago_client.events.create(lago_output_event)
    except LagoApiError as e:
        print("Fail to Create Lago Output Event...")
        raise LagoApiError()
    ```

---

## LiteLLM on Kubernetes

> LiteLLM을 Kubernetes (Helm)을 사용하여 배포한 내용 (Namespace의 경우 필요한 경우 kubectl을 통한 생성 진행)

### Prerequisite

values.yaml 파일에 사용될 `Env ConfigMap` 과 `Database User Secret` 을 생성

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: litellm-env-configmap
  namespace: litellm-dcjeon
data:
  STORE_MODEL_IN_DB: "True" # Env for Enable to Save in Database
  LITELLM_LOG: "DEBUG" # LiteLLM Log Level
---
apiVersion: v1
kind: Secret
metadata:
  name: psql-secret
  namespace: litellm-dcjeon
data:
  username: {DB_USERNAME_BASE64}
  password: {DB_PASSWORD_BASE64}
```

```shell
kubectl apply -f config_and_secret.yaml
```

### Deploy by Helm

1. Edit values.yaml

    기본적으로 LiteLLM에서 제공하는 values.yaml 파일을 사용하지만, 이미 배포된 PostgreSQL과 Helm 기반으로 배포한 LiteLLM을 엮기 위한 values.yaml 파일 추가 수정

    ```yaml
    # ...
    image:
        repository: ghcr.io/berriai/litellm
        pullPolicy: IfNotPresent
        tag: "main-v1.48.2"
    # ...
    
    # LiteLLM ConfigMap (Used by os.environ)
    environmentConfigMaps:
    - litellm-env-configmap
    
    # ...
    masterkey: "sk-1234" # LiteLLM Master Key (Also Used by Login)
    # ...

    # Setup Database Access
    db:
        useExisting: true # If true, Use Existing Database

        endpoint: postgresql.database.svc.cluster.local # $(DATABASE_HOST) in url
        database: litellm # $(DATABASE_NAME) in url
        url: postgresql://$(DATABASE_USERNAME):$(DATABASE_PASSWORD)@$(DATABASE_HOST)/$(DATABASE_NAME)
        # Database User Name & Password Secret
        # $(DATABASE_USERNAME), $(DATABASE_PASSWORD) in url
        secret:
            name: psql-secret
            usernameKey: username
            passwordKey: password
    
    # ...
    ```

2. Helm Install
  
    수정한 values.yaml 파일 기반의 Helm install 진행

    ```shell
    helm install litellm \
    deploy/charts/litellm-helm \
    -n litellm-dcjeon

    # 배포 진행 상태 확인
    watch 'kubectl get pod -n litellm-dcjeon'
    ```

### Expose by Domain

외부에서 테스트를 진행하기 위해 Istio를 통해 LiteLLM을 노출 (테스트는 위에서 진행한 Ptyhon 코드 기반으로 생략)

1. Gateway

```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: litellm-gateway
  namespace: litellm-dcjeon
spec:
  selector:
    istio: ingressgateway
  servers:
  - hosts:
    - litellm.my-llm-service.com
    port:
      name: http
      number: 80
      protocol: HTTP
```

```shell
kubectl apply -f gateway.yaml
```

2. Virtual Service

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: litellm-virtual-service
  namespace: litellm-dcjeon
spec:
  gateways:
  - litellm-gateway
  hosts:
  - litellm.my-llm-service.com
  http:
  - match:
    - uri:
        prefix: /
    rewrite:
      uri: /
    route:
    - destination:
        host: litellm
        port:
          number: 4000
```

```shell
kubectl apply -f virtual_service.yaml
```

---

## Report

### 1. LiteLLM + Lago Python 코드 실행

정상적으로 호출을 하지만, Log Callback 호출 과정에서 에러 발생

```text
LiteLLM.LoggingError: [Non-Blocking] Exception occurred while success logging with integrations Traceback (most recent call last):
  File "/home/ubuntu/dcjeon/huggingface/venv/lib/python3.11/site-packages/litellm/litellm_core_utils/litellm_logging.py", line 1228, in success_handler
    callback.log_success_event(
  File "/home/ubuntu/dcjeon/huggingface/venv/lib/python3.11/site-packages/litellm/integrations/lago.py", line 140, in log_success_event
    _data = self._common_logic(kwargs=kwargs, response_obj=response_obj)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/dcjeon/huggingface/venv/lib/python3.11/site-packages/litellm/integrations/lago.py", line 108, in _common_logic
    raise Exception(
Exception: External Customer ID is not set. Charge_by=end_user_id. User_id=None. End_user_id=None. Team_id=None

LiteLLM.Logging: is sentry capture exception initialized None
```

- 원인

    LiteLLM 내 Lago 모듈 호출 과정에서 Lago 관련 사용자 설정을 정상적으로 했음에도 External Customer ID 가 정상적으로 설정되지 않았다는 메시지 발생

    `site-package > litellm > integrations > lago.py` 의 `_common_logic()_` 함수를 확인해보면, __end_user_id, user_id, team_id__ 를 받는 부분이 있는데, 해당 부분에서 요구하는 파라미터 형식이 달라서 발생하는 에러

    또한, 받는 3개의 변수들이 모두 `external_customer_id` 로 선언이 되는데, 이는 external_subscription_id 키의 값으로 들어가는 것으로 보아 가급적 Lago의 External Subscription ID 값으로 설정을 해주어야하는 것으로 파악

    - ref. site-package > litellm > integrations > lago.py > _common_logic()

        ```python
        proxy_server_request = litellm_params.get("proxy_server_request") or {}
        end_user_id = proxy_server_request.get("body", {}).get("user", None)
        user_id = litellm_params["metadata"].get("user_api_key_user_id", None)
        team_id = litellm_params["metadata"].get("user_api_key_team_id", None)
        org_id = litellm_params["metadata"].get("user_api_key_org_id", None)

        charge_by: Literal["end_user_id", "team_id", "user_id"] = "end_user_id"
        external_customer_id: Optional[str] = None

        if os.getenv("LAGO_API_CHARGE_BY", None) is not None and isinstance(
            # ...

        if charge_by == "end_user_id":
            external_customer_id = end_user_id
        elif charge_by == "team_id":
            external_customer_id = team_id
        elif charge_by == "user_id":
            external_customer_id = user_id

        # 해당 부분으로 넘어가서 예외 발생
        if external_customer_id is None:
            raise Exception(
                "External Customer ID is not set. Charge_by={}. User_id={}. End_user_id={}. Team_id={}".format(
                    charge_by, user_id, end_user_id, team_id
                )
            )

        returned_val = {
            "event": {
                "transaction_id": str(uuid.uuid4()),
                "external_subscription_id": external_customer_id,
                "code": os.getenv("LAGO_API_EVENT_CODE"),
                "properties": {"model": model, "response_cost": cost, **usage},
            }
        }
        ```
### 2. LiteLLM을 Kubernetes에 배포할 때 나타나는 Database Connection Error

LiteLLM을 Helm/Deployment로 배포할 때 `InitContainer` 인 `db-ready` Container 안에서 Database Connection을 수행할 때 Connection Error 발생

```text
Waiting for database to be ready 0
psql: error: could not translate host name "postgresql.database.svc.cluster.local:5432" to address: Name or service not known
Waiting for database to be ready 1
...
Waiting for database to be ready 59
psql: error: could not translate host name "postgresql.database.svc.cluster.local:5432" to address: Name or service not known
Database failed to become ready before we gave up waiting.
```

Database Connection을 60회 수행 후 정상적으로 연결이 되지 않으면 에러 발생 (간헐적으로 정상적으로 연결)
