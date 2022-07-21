# KServe <a name="first">
> 공부한 내용 & 실습들을 정리
> Index를 통해서 필요한 부분으로 이동할 수 있도록 해두었으니 참조

### Index :
1. [__What is KServe?__](#i1)
2. [__Model Serving__](#i2)
3. [__Dex Auth__](#i3)

# 1. What is KServe? <a name="i1">
> KServe에 대한 개념을 간략하게만 설명

KServe는 Kubeflow의 _KFServing_ 가 독립된 컴포넌트 형태로 나온 이름이며, 임의의 Framework(e.g. Tensorflow, ScikitLearn, Pytorch...)에서 나온 Machine Learning Model을 Serving하기 위한 컴포넌트이다. 

\* Ref) Inference는 Machine Learning에서 학습된 Model을 올려서 실 데이터들을 입력 받아서 실제 output을 내는 것을 말한다고 보면 된다. 예를 들자면, 학습을 통해 강아지 고양이 분류 모델이 나오게 되면 이것을 Serving함으로써 Client가 새로운 Data를 Input하게 되면 그에 대한 output을 내줄 수 있다. (사실상 서비스로 배포하는 것)

###### <- 처음으로 (#first)

------------------

# 2. Model Serving <a name="i2" />

KServe의 __Inference Service__ 를 이용해서 Model을 Serving하고 Test하는 것까지 진행하며, Test는 Kubernetes 같은 Container 안에서 배포하는 것을 가정하여, Ubuntu Image 기반의 Test Pod를 생성하고 그 안에서 __Cluster IP__를 통해 API를 호출한다. Test는 ScikitLearn의 Iris 분류 Model을 기반으로 진행하였다.

<details>
<summary>Model Serving 과정</summary>
<div markdown="1">
1. Model 생성 (Python, Jupyter 등등 이용해서 Serving할 Model 생성)
</div>
<div markdown="2">
2. InferenceService YAML file 작성 및 생성
</div>
<div markdown="3">
3. Input Data, REST API 정보 가져오기
</div>
<div markdown="4">
4. Serving한 Model 사용
</div>
</details>

## Model 생성
  
Model의 생성 방법은 다양하다. 대중적으로 사용되는 모델은 이미 생성된 Model File이 Cloud에 저장되어 있을 수도 있고, Custom Model의 경우에는 PVC, Local, 개인 Cloud Storage...등에 저장이 되어있을 수 있다. 여기서는 __[1] Google Cloud Storage 의 Model__ 과 __[2] Persistant Volume Claim(PVC)__ 에 올린 Custom Model을 Serving하는 Test를 진행한다. [1]의 경우에는 추후 YAML file 생성 과정에서 storage URI를 작성하는데, 그 부분에 gcs:// 접두사와 함께 Storage 경로를 작성하면 되기 때문에 그 때 다룬다.
  
```python
from sklearn import svm # Support Vector Machine module import
from sklearn import datasets # ScikitLearn에 있는 Iris data set을 가져오기 위한 module import
from joblib import dump # 추후 Model을 떨구기 위한 Module
  
# Data와 label 선언
iris_datasets = datasets.load_iris()
X, y = iris_datasets, iris.target

clf = svm.SVC(gamma='scale')
clf.fit(X, y)
  
dump(clf, 'iris-model.joblib') # iris-model.joblib으로 Model이 생성
```
  
## InferenceService YAML file 작성 및 생성
  
- Serving하기 위한 Model이 담긴 __YAML__ file을 작성한다.
  
```yaml
# Version에 따라서 YAML 구조가 조금씩 다르게 나타나기 때문에 Version은 반드시 확인하고 넘어간다.
apiVersion: "serving.kserve.io/v1beta1"
kind: "InferenceService"
metadata:
  name: "sklearn-iris"
  # Namespace는 필요에 맞춰서 선언해주면 된다.
  # namespace: "kubeflow-user-example-com"
spec:
  predictor:
    # Predictor Framework
    sklearn:
      # Serving Protocol Version
      ProtocolVersion: "v2"
      # Model Storage Path
      storageUri: "gs://seldon-models/sklearn/iris"
```

- YAML file을 만들었다면 Kubernetes에 올린다.
  
```shell
kubectl create -f sklearn-iris.yaml
```

## Input data & Serving Model에 대한 REST API 정보 가져오기

Model을 생성하고 정상적으로 Kubernetes에 Serving을 했다면, 다음과 같은 명령어를 통해 정상적으로 올라갔는지 확인할 수 있다.
  
```shell
# Serving한 Model의 이름과 -n 옵션을 통해 Namespace를 선언
kubectl get isvc sklearn-iris -n kubeflow-user-example-com
  
# Pod에도 정상적으로 올라갔는지 확인
kubectl get pod -n kubeflow-user-example-com | grep sklearn-iris
```

- 결과 화면
  
![Alt Text][check_inference_service_status]

###### <- 처음으로 (#first)

----------------------

# 3. Dex Auth <a name="i3"/>

## Dex Auth : ID Token through REST API
__Dex__ 란 3rd Party로부터 _OAuth Token_ 을 가져와 관리하는 인증 도구로, Kubeflow를 설치하게 되면 Dex가 설치되는데, 이를 활용해서 KServe 기반의 Model Serving이후 필요한 인증 ID Token 값을 발급받고 이를 활용하여 Serving Model에 Data Input을 수행한다.

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

Dex 인증을 요구하는 자원들을 호출하게 되면 _'/dex/auth'_ 로 Redirect 되면서 인증을 요구하는데, 이에 대한 해결 방법으로는 __2__ 가지가 있다.
- 요청할 URL에 대하여 Dex 인증을 __우회__ 하는 방법
- 사전에 인증 과정을 거쳐서 __authservice_session__ 값을 얻고, authentication 요청시 __ID Token__ 값을 전달
  - __KFP(Kubeflow Piplines SDK)__ 를 이용한 ID Token 발급
  - __REST API__ 를 이용한 ID Token 발급

### 초기 Authentication을 거치지 않은 경우
```'curl -v http://${HOST}:${PORT}/v2/models/${MODEL_NAME} -d ${INPUT_DATA}'``` 를 하게 되면 다음과 같은 Exception이 발생

![Alt Text][first_dex_trial_screen]

Authentication Issue로 인하여 Serving Model을 정상적으로 사용하지 못함 -> 해결 방안
- Dex에 등록된 _ID/Password_ 를 전달
- _ID Token_ 발급을 통한 Authentication 수행

### REST API를 이용한 ID Token 발급

ID Token 발급 과정에서 사전에 Serving 했던 _'sklearn-irisv2'_ 라는 model을 기반으로 작업 수행
1. Ingress Host IP & Port 설정 후 URI 호출

```shell
# External IP를 할당받지 않은 경우 수행
INGRESS_HOST=$(kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath='{.items[0].status.hostIP}')
INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].NodePort}')

# URI 호출
curl http://${INGRESS_HOST}:${INGRESS_PORT}/v2/models/sklearn-irisv2
```

- 결과에서 Dex auth 요청하는 _href_ 부분을 복사 (/dex/auth?client_id=...HYb1)

![Alt Text][ingress_url_call]

2. __REQ__ value 얻기

- 결과에서 req 값을 복사해서 REQ 변수로 할당

![Alt Text][get_req]

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

![Alt Text][account_and_req_auth]

4. _approval_ 얻기

![Alt Text][get_approval]

5. __ID Token__ 값 얻기

- ID Token 값을 얻으면 _반드시_ 기억하고 있어야 하며, 하루가 지나야 재발급 가능
- ID Token 값은 _한 번_ 만 조회 가능하며, 두 번째 호출부터는 __'504 Gateway Timeout' Exception__ 이 발생

![Alt Text][get_id_token_and_result]

<details>
<summary>set-cookies의 내용</summary>
<div markdown="1">
- authservice_session=MTY...YtfZ
</div>
<div markdown="2">
- Path=/
</div>
<div markdown="3">
- Expires=Thu, 21 Jul 2022 05:30:11 GMT
</div>
<div markdown="4">
- Max-Age=86400
</div>
</details>

### ID Token을 활용한 Model Data Input Test
> Test Env 1. : Serving했던 Model Pod를 NodePort로 Expose 후 Testing
> Test Env 2. : KServe로 Serving 후 생긴 Service에서 Model의 Cluster IP를 통한 Testing (Prerequisite : Ubuntu Image를 올린 Pod 배포)


#### Test Env 1.
KServe로 Serving했던 Model _Pod_ 를 __NodePort__ 로 Expose 후 Test를 진행하는데, 과정은 다음과 같다.

1. Serving된 Model __Pod__ 를 __NodePort__ 로 expose
2. 해당 Service의 _8080 NodePort_ 를 가져옴
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

- 결과(Terminal) : 정상적으로 수행되었음을 보여준다.

![Alt Text][dex_auth_id_token_test_result]

#### Test Env 2.
KServe로 Serving 후 생긴 Inference의 Service에서 Model의 __Cluster IP__ 를 통한 Testing으로, 과정은 다음과 같다.

1. Ubuntu Image가 올라간 임의의 Pod 생성
2. 해당 Pod의 Shell Connection
3. input data 샘플(iris-input.json) 생성
4. Serving Model의 private svc Cluster IP를 가져옴
5. ID Token 값을 활용해 인증한 뒤에 Test

```shell
# Ubuntu가 들어있는 Pod를 정의한 YAML 이름을 model-test-ubuntu라고 가정
kubectl create -f model-test-ubuntu

# 생성된 Pod의 shell connection
kubectl exec --stdin --tty model-test-ubuntu -n ${Pod Namespace} -- /bin/bash

# 임의의 경로로 이동한 뒤에 input data(iris-input.json)을 생성한 뒤 Cluster IP, Port, Token 설정 (Test에서는 80으로 함)
CLUSTER_IP=${Served Model Private Service Cluster IP}
CLUSTER_PORT=80
TOKEN=${ID Token Value}

# ID Token 인증 후 Testing
curl -v -H "Cookie: authservice_session=${TOKEN}" -d ${INPUT_DATA} http://${CLUSTER_IP}:${CLUSTER_PORT}/v2/models/${MODEL_NAME}/infer
```

- 결과 (Terminal) : 정상적으로 수행되었음

![Alt Text][dex_auth_id_token_test_result_cluster_ip]

###### <- 처음으로 (#first)


[first_dex_trial_screen]:https://imgur.com/ZNxXlKY.png
[ingress_url_call]:https://imgur.com/rMZbdp0.png
[get_req]:https://imgur.com/jfqjoN7.png
[account_and_req_auth]:https://imgur.com/64fCZMx.png
[get_approval]:https://imgur.com/AZ84iwi.png
[get_id_token_and_result]:https://imgur.com/i57E2PJ.png
[dex_auth_id_token_test_result]:https://imgur.com/UV3hZ9M.png
[dex_auth_id_token_test_result_cluster_ip]:https://imgur.com/fff0Uc8.png
[check_inference_service_status]:https://imgur.com/3ZTMVhU.png
