# LiteLLM & Lago

> AI Serving Gateway인 LiteLLM과 Billing&Metering을 처리하는 Lago에 대한 문서

## LiteLLM

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

## Lago in LiteLLM

LiteLLM에서 Logging Callback을 위한 다양한 도구 중 Billing, Metering을 담당하는 Lago 사용 방법

### Lago in Python

> PyPi 패키지 이름 : lago-python-client

### Lago & LiteLLM in Python

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
