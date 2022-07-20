# KServe
> KServe 작업 과정에서 공부한 내용들을 정리한다.

## 1. Dex Auth

### Dex Auth : ID Token through REST API
__Dex__란 3rd Party로부터 OAuth Token을 가져와 관리하는 인증 도구로, Kubeflow를 설치하게 되면 Dex가 설치되는데, 이를 활용해서 KServe 기반의 Model Serving이후 필요한 인증 ID Token 값을 발급받고 이를 활용하여 Serving Model에 Data Input을 수행한다.

<details>
<summary>Dex 인증을 요구하는 자원</summary>
<div markdown="1">
1. Kubeflow Central Dashboard (Login)
</div>
<div markdown="2">
2. KFServing/KServe
</div>
<div markdown="3">
3. Knative Serving
</div>
  
<div markdown="4">
4. Istio Virtual Service
</div>
</details>

Dex 인증을 요구하는 자원들을 호출하게 되면 _'/dex/auth'_ 로 Redirect 되면서 인증을 요구하는데, 이에 대한 해결 방법으로는 2가지가 있다.
- 요청할 URL에 대하여 Dex 인증을 __우회__ 하는 방법
- 사전에 인증 과정을 거쳐서 __authservice_session__ 값을 얻고, authentication 요청시 __ID Token__ 값을 전달
  - KFP(Kubeflow Piplines SDK)를 이용한 ID Token 발급
  - __REST API__ 를 이용한 ID Token 발급

#### 초기 Authentication을 거치지 않은 경우
'curl -v http://${HOST}:${PORT}/v2/models/${MODEL_NAME} -d ${INPUT_DATA}'를 하게 되면 다음과 같은 Exception이 발생

Authentication Issue로 인하여 Serving Model을 정상적으로 사용하지 못함 -> 해결 방안
- Dex에 등록된 ID/Password를 전달
- ID Token 발급을 통한 Authentication 수행

#### REST API를 이용한 ID Token 발급

ID Token 발급 과정에서 사전에 Serving 했던 'sklearn-irisv2'라는 model을 기반으로 작업 수행
1. Ingress Host IP & Port 설정 후 URI 호출

```shell
# External IP를 할당받지 않은 경우 수행
INGRESS_HOST=$(kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath='{.items[0].status.hostIP}')
INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].NodePort}')

# URI 호출
curl http://${INGRESS_HOST}:${INGRESS_PORT}/v2/models/sklearn-irisv2
```

- 결과에서 Dex auth 요청하는 href 부분을 복사 (/dex/auth?client_id=...HYb1)


2. __REQ__ value 얻기

- 결과에서 req 값을 복사해서 REQ 변수로 할당

3. ID/Password를 통한 인증 수행

```shell
# 인증 정보 : ID/Password는 Kubeflow Central Dashboard Login 정보
REQ=k44hx2...da3g
LOGIN=<Dex ID Value>
PASSWORD=<Dex Password>

# 인증 : 아무런 결과 없음
curl "http://${INGRESS_HOST}:${INGRESS_PORT}/dex/auth/local?req=${REQ}" \
-H "Content-Type: application/x-www-form-urlencoded" \
--data "login=${LOGIN}&password=${PASSWORD}"
```

4. approval 얻기

5. ID Token 값 얻기

- ID Token 값을 얻으면 반드시 기억하고 있어야 하며, 하루가 지나야 재발급 가능
- ID Token 값은 한 번만 조회 가능하며, 두 번째 호출부터는 _'504 Gateway Timeout' Exception_ 이 발생

<details>
<summary>set-cookies의 내용</summary>
<div markdown="1">
authservice_session=MTY...YtfZ
</div>
<div markdown="2">
Path=/
</div>
<div markdown="3">
Expires=Thu, 21 Jul 2022 05:30:11 GMT
</div>
  
<div markdown="4">
Max-Age=86400
</div>
</details>

#### ID Token을 활용한 Model Data Input Test
> Test는 Serving했던 Inference를 NodePort로 Expose 한 작업으로 1차 수행하고, 추후 Cluster IP를 통해 내부에서 작업한 내용을 Upload할 예정

1. Serving된 Model Pod를 NodePort로 expose
2. 해당 Service의 8080 NodePort를 가져옴
3. ID Token 값을 활용해 인증한 뒤에 Test

```shell
# KServe를 활용해 Model을 Serving하게 되면, Pod가 생성되는데, 해당 Pod를 NodePort로 service
kubectl expose pod -n <Inference Namespace> <Inference Pod Name> --type=NodePort

# 8080의 nodeport를 가져옴
NODE_PORT=$(kubectl get svc -n <Inference Namespace> <Inference Pod Name> -o jsonpath='{.spec.ports[?(@.name=="port-1")].nodePort}')

# 사전에 Test를 위한 input data가 있어야 함 (사진에서는 iris-input.json)
INPUT=@./iris-input.json

# Token 정보 저장 : set_cookies의 authservice_session 값
TOKEN=MTY...YtfZ

# Model Test
curl -v -H "Cookie: authservice_session=${TOKEN}" -d ${INPUT} http://${INGRESS_HOST}:${NODE_PORT}/v2/models/sklearn-irisv2/infer
```

- 결과 값 : Terminal - 정상적으로 수행되었음을 보여준다.
