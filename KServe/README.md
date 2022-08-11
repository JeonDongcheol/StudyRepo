# KServe

> KServe와 관련해서 공부 & 실습한 내용들을 정리했다. KServe Version 0.7을 기준으로 작성했으며, 어디까지나 내 기준의 환경에서 작업한 것이기 때문에 참조 정도만 하면 좋을 듯 하다.

> AWS EC2 Instance 위에서 실습했으며, OS Image는 CentOS 7 환경에서 이루어졌다.

> Index를 통해서 원하는 부분을 찾아서 이동하자... 나름 열심히 적었지만 부족한 부분도 많다고 계속 느끼는 중이다... (끝도 없이 뭔가가 튀어나옴)

### Index :
1. [__What is KServe?__](#about_kserve)
2. [__Model Serving Using PVC__](#model_serving_pvc)
3. [__KServe Dex Authentication__](#dex_auth)

# 1. What is KServe? <a name="about_kserve" />
> KServe에 대한 개념을 조금이라도 잡을 수 있게 설명을 적어둔다.

KServe는 Kubeflow의 _KFServing_ 가 독립된 컴포넌트 형태로 나온 이름이며, 임의의 Framework(e.g. Tensorflow, ScikitLearn, Pytorch...)에서 나온 Machine Learning Model을 Serving하기 위한 컴포넌트다. 여러 ML Platform 회사들이 협업하여 Kubernetes의 Open Source Cloud Native Model Server로 개발했으며, 쉽게 말해서 여러 Framework들 및 MLServer 들에서 지원하는 _AI Model Serving_ 역할을 수행한다고 보면 된다.

참고로 Model Serving의 개념을 대략적으로 설명하자면, 학습된 Model을 만들고 난 후 여기서 끝내는 것이 아니라 이를 활용하여 서비스화 하여 실제 Data Input을 받고 원하는 Output을 낼 수 있어야 한다. 이것을 __REST API__ 혹은 __gRPC__ 를 기반으로 동작시킨다. 예를 들자면, 강아지&고양이 분류 학습 모델을 만들었을 때 이를 Serving하여 실제 내가 찍은 강아지 사진을 Input하고 이 사진을 강아지라고 Output을 내는 것이라고 보면 된다.

기존의 Kubernetes 배포 또는 Scale-to-Zero를 지원하는 Serverless로 배포할 수 있는데, 여기서 Auto-Scale Up & Down 기능을 갖춘 Serverless용 _KNative Serving_ 을 활용한다. 또한 __Istio__ 는 Model Service Enpoint를 API Client에게 공개하기 위한 _Ingress_ 로 활용한다.

![Alt Text][kserve_structure]

### KServe Architecture

KServe Model Server에는 Control Plane과 Data Plane이 있으며, 각 역할은 다음과 같다.

1. [__Control Plane__](https://kserve.github.io/website/0.8/modelserving/control_plane/) : Inference를 담당하는 Custom Resource를 관리 및 조정하는데, Serverless Mode에서는 KNative Resource와 연계하여 Auto-Scale을 관리한다. KServe Control Plane 핵심에는 _Inference Service Life Cycle_ 을 관리하는 __KServe Controller__ 가 있다. _Service, Ingress Resource, Model Server Container, Request/Response Logging을 위한 Model Agent Container, Batch & Model Storage에서 Model Pulling_ 업무 등을 담당한다.
2. [__Data Plane__](https://kserve.github.io/website/0.7/modelserving/data_plane/) : 특정 Model을 대상으로 하는 Request/Response 주기를 관리한다. 또한 Model Ready Status와 이상 존재 여부를 상태를 확인할 수 있는 Endpoint도 있으며, Model Metadata를 검색하기 위한 API도 제공한다. Data Plane의 요소는 다음과 같다.

<details>
  <summary>KServe Data Plane Component</summary>
  <div markdown="1">
  &nbsp;&nbsp;&nbsp;&nbsp;- Predictor (Essential) : Transformer Component를 호출하는 Inference Pipline으로 작동한다.
  </div>
  <div markdown="2">
  &nbsp;&nbsp;&nbsp;&nbsp;- Transformer : Inbound Data의 Preprocess Request와 Outbound Data의 Postprocess(Response)를 실행한다.
  </div>
  <div markdown="3">
  &nbsp;&nbsp;&nbsp;&nbsp;- Explainer : AI의 설명 가능성을 제공한다. (확실하게는 개념을 모르겠다 아직...)
  </div>
</details>

![Alt Text][kserve_architecture]

### Supporting Runtime Server
> KServe에서 지원하는 Runtime Server를 안내하는데, 기본적으로 _KFServer_를 사용하고, V2 Data Plane은 작업 중이라 일부만 지원한다.

KServe에서 기본적으로 제공하는 Runtime Server로는 아래 표와 같다. (KServe Official Website의 내용에서 최대한 필요한 내용만 )

| Protocol Version | Model Server | 지원하는 AI Model | Server Version | YAML Key (계속 수정 중) |
|:---------:|---------|---------|:---------:|:---------:|
| __V2__ | Triton Inference Server | [Tensorflow, TorchScript, ONNX](https://github.com/triton-inference-server/server/blob/r21.09/docs/model_repository.md) | [Compatibility Matrix](https://docs.nvidia.com/deeplearning/frameworks/support-matrix/index.html) | __triton__ |
| | SKLearn MLServer | [Pickled Model](https://scikit-learn.org/stable/model_persistence.html) | 0.23.1 | __sklearn__ |
| | XGBoost MLServer | [Saved Model](https://xgboost.readthedocs.io/en/latest/tutorials/saving_model.html) | 1.1.1 | __xgboost__ |
| __V1__ | TFServing | [Tensorflow SavedModel](https://www.tensorflow.org/guide/saved_model) | [TFServing Version](https://github.com/tensorflow/serving/releases) | __tensorflow__ |
| | TorchServe | [Eager Model/TorchScript](https://pytorch.org/docs/master/generated/torch.save.html) | 0.4.1 | pytorch |
| | SKLearn KFServer | [Pickled Model](https://scikit-learn.org/stable/model_persistence.html) | 0.20.3 | __sklearn__ |
| | XGBoost KFServer | [Saved Model](https://xgboost.readthedocs.io/en/latest/tutorials/saving_model.html) | 0.82 | __xgboost__ |
| | PMML KFServer | [PMML](https://dmg.org/pmml/v4-4-1/GeneralStructure.html) | PMML4.4.1 | __pmml__ |
| | LightGBM KFServer | [Saved LightGBM Model](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.Booster.html#lightgbm.Booster.save_model) | 2.3.1 | __lightgbm__ |
  
##### - Custom Model Server에 대해서는 특별하게 기술하지 않는다.
  
### Data Plane Protocol
> KServe Data Plane Protocol의 Version에 따른 내용을 기술. Explainer에 대한 내용을 아직 명확하지 않기에 작성하지 않음
  
- V1 Protocol
  
| API Usage | Method | Path (Endpoint) | Request | Response |
|------|:------:|-------|-------|------|
| Read Model's Health | __GET__ | ```/v1/models/${MODEL_NAME}``` | | { "name": String, "ready": Boolean } |
| Read Model's List | __GET__ | ```/v1/models``` | | |
| Predict | __POST__ | ```/v1/models/${MODEL_NAME}:predict``` | { "instances" : [ Input Tensor ] } | { "predictions" : [ Output ] } |

__Predict__ 의 경우 Tensorflow Model을 제외한 모든 Inference Model은 Input이 [Tensorflow V1 HTTP API](https://www.tensorflow.org/tfx/serving/api_rest#predict_api) Format을 따른다.

Tensorflow Model은 ```{ "signature_name" : String, "inputs"("instances"도 가능) : [ Input Tensor] }``` 형태의 Request Input Format을 따른다.
  
- V2 Protocol

V2 Protocol은 현재 작업 중인 것(22.07.28 기준)으로 알고 있으며, 현재 나온 Model에 대해서는 다음과 같은 URL을 지원한다.
  
| API Usage | Method | Path (Endpoint) | Request | Response |
|---------|:---------:|------------|----------|----------|
| Read Model's Health | __GET__ | ```/v2/models/${MODEL_NAME}/ready``` | | ```Empty Result``` (Error Code에 따른 상태 체크) |
| Read Model's List | __GET__ | ```/v2/models``` | | |
| Read Model's Metadata | __GET__ | ```/v2/models/${MODEL_NAME}``` | | ```{ "name" : String, "version" : [ ], "platform" : String, "inputs" : [ ], "outputs" : [ ] }``` |
| Predict | __POST__ | ```/v2/models/${MODEL_NAME}/infer``` | ```{ "id" : String, "parameters" : [ ], "inputs" : [{ "name" : String, "shape" : [ ], "datatype" : String, "parameters" : [ ], "data" : [ Input Tensor ] }], "outputs" : [ { "name" : String, "parameters" : [ ] } ] }``` | ```{ "model_name": String, "model_version" : String, "id" : String, "parameters" : String, "outputs" : [{ "name" : String", "shape":[ ], "datatype" : "String", "parameters" : String, "data" : [ ] }]}``` |
  
__Model's Health__ 의 경우에는 _Server Live status, Server Ready status, Model Ready status_ 를 나타내는데, 특별한 Response Body가 있는 것이 아닌 REST API 호출했을 때 Status Code가 __200__ 인 경우 정상적으로 동작 가능하다는 것이며, Status가 __4XX__ 인 경우에는 정상적으로 동작하지 않는다는 것이므로 Error Message를 참조해야 한다.
  
__Model Metadata__ 의 경우에는 _Model Name, Model Version, Platform, Input&Output Format_ 등의 정보를 포함하고 있다.
  
__Inference__ 의 경우에는 Serving Model를 사용하기 위해 REST API를 통해서 실제 Data를 Input하고 결과 값을 반환 받는다. Request Body에서 __"inputs"__ Field만큼은 __Essential__ 로, 반드시 들어가야 한다. (나머지는 설정에 따라 Optional)
  
Tensor Data의 Type (Prediction Input에서 _'datatype'_ field)은 다음과 같다. (추후 V2 Data Input 과정에서 아래의 Data Type 중 하나를 골라서 선언해주면 된다.)
  
| Data Type | Size (Bytes) |
|-----------|:------:|
| BOOL | 1 |
| UINT8 | 1 |
| UINT16 | 2 |
| UINT32 | 4 |
| UINT64 | 8 |
| INT8 | 1 |
| INT16 | 2 |
| INT32 | 4 |
| INT64 | 8 |
| FP16 | 2 |
| FP32 | 4 |
| FP64 | 8 |
| BYTES | Variable (max 2^32) |
  
- Model Storage
  
KServe는 기존에 학습시켜 만들어 두었던 Model을 Pulling하고 이를 ```/mnt/models``` (Default, 설정에 따라 다름)에 저장해두고 이를 Serving하는 형식이기 때문에 Model Storage에 대한 정보를 반드시 담아야 한다. Model Storage의 종류로는 다음과 같다.
  
<details>
  <summary>Model Storage List</summary>
  <div markdown="1">
    &nbsp;&nbsp;&nbsp;&nbsp;- Google Cloud Storage
  </div>
  <div markdown="2">
    &nbsp;&nbsp;&nbsp;&nbsp;- Amazone Web Service S3
  </div>
  <div markdown="3">
    &nbsp;&nbsp;&nbsp;&nbsp;- Azure Blob Storage
  </div>
  <div markdown="4">
    &nbsp;&nbsp;&nbsp;&nbsp;- Local Path
  </div>
  <div markdown="5">
    &nbsp;&nbsp;&nbsp;&nbsp;- Persistant Volume Claim (PVC)
</div>
</details>

_Google Cloud Storage_ 와 _AWS S3_ Case에는 사용자 인증을 환경 변수에 추가해야한다. **(이에 대해서는 추후 작성)**

------------------

# 2. Model Serving Using PVC <a name="model_serving_pvc" />
> Google Cloud Storage를 활용한 것이 아닌 따로 학습시킨 Model을 PVC에 저장하고 이를 Serving하는 부분을 안내한다.

KServe의 __Inference Service__ 를 이용해서 Model을 Serving하고 Test까지 하는 것을 진행하는데, Test는 Kubernetes 안의 Container 안에서 배포하는 것을 가정하고 진행한다. Tensorflow의 홈페이지에 나와있는 Image Classification의 [__Mobile Net__](https://www.tensorflow.org/guide/saved_model) 을 사용해서 학습을 하고 Model을 PVC에서 불러온다.
  
Model Serving은 위에서 언급했던 것처럼 Training이 완료된 Model을 사용자들이 사용할 수 있도록 __REST API / gRPC(여기서는 사용하지 않음)__ 형태로 제공하는 작업이다. KServe에서 Model을 Serving하는 방법은 다양하겠지만 전반적인 Process는 다음과 같다.

<details>
  <summary>Model Serving 과정</summary>
  <div markdown="1">
  &nbsp;&nbsp;&nbsp;&nbsp;1. Model Creation (Pyton, Jupyter, Java ...)
  </div>
  <div markdown="2">
  &nbsp;&nbsp;&nbsp;&nbsp;2. Inference YAML Creation (Kubeflow Central Dashboard를 통해서도 가능)
  </div>
  <div markdown="3">
  &nbsp;&nbsp;&nbsp;&nbsp;3. Inference Service Creation on Kubernetes (Basic하게는 Pod 1개, Deployment 1개, Service 4개가 생성된다. 설정에 따라 다름)
  </div>
  <div markdown="4">
  &nbsp;&nbsp;&nbsp;&nbsp;4. REST API/gRPC를 기반으로 Serving Model 사용
  </div>
</details>

Serving을 위한 YAML file 구조는 다양하지만 Base Structure는 다음과 같다.
  
```yaml
apiVersion: ${KServe API Version}
kind: "InferenceService"
metadata:
  name: ${Inference Service Name}
spec:
  predictor:
    ${Predictor Framework Name}:
      storageUri: ${MODEL_STORAGE_PATH}
```
  
해당 구조는 가장 기본적인 구조로 해당 값들만 넣어주어도 Inference Service가 생성되긴 한다. (물론 정상적인 값들을 넣었을 때만...)

좀 더 정교한 설정을 하고 싶다면 다음과 같이 해준다.
  
```yaml
apiVersion: ${KServe API Version}
kind: "InferenceService"
metadata:
  name: ${Inference Service Name}
  namespace: ${NAMESPACE}
  annotations:
    # istio injection을 false로 설정해야지 정상적으로 통신을 한다. 
    # 나는 Serving하는 Model에 대해서는 전부 해당 값을 넣었다.
    # 왜 그런 것인지는 잘 모르겠으나, 추후 보충 설명할 예정
    sidecar.istio.io/inject: "false"
spec:
  predictor:
    ${Predictor Framework Name}:
      storageUri: ${MODEL_STORAGE_PATH}
      # Protocol Version은 Data Plane이 V1, V2 둘 다 있는 Case에서 맞춰서 사용
      # 내가 알기로는 Triton Inference Server, Scikit Learn, XGBoost 등이 V2 Protocol도 사용할 수 있는 것으로 알고 있음
      protocolVersion: ${PROTOCOL_VERSION}
      # Runtime Version은 기본적으로 Configmap의 inferenceservice-config에 Default Model Server Image가 포함되어 있음
      # 그 외의 다른 Runtime Version을 사용하고 싶다면 해당 Field를 사용하여 정의해준다.
      runtimeVersion: ${RUNTIME_VERSION}
      # 자원 사용에 대한 정의 : Inference 과정에서 요구되는 자원과 한계 자원에 대한 정의를 내린다.
      # 따로 정의를 해주지 않는다면 Default로 CPU 1, Memory 2Gi 값이 들어감
      resources:
        limits:
          cpu: ${LIMITS_CPU}
          memory: ${LIMITS_MEMORY}
        requests:
          cpu: ${REQUESTS_CPU}
          memory: ${REQUESTS_MEMORY}
```

## Model 생성
  
Model의 생성 방법은 다양하다. 대중적으로 사용되는 모델은 이미 생성된 Model File이 Cloud에 저장되어 있을 수도 있고, Custom Model의 경우에는 PVC, Local, 개인 Cloud Storage...등에 저장이 되어있을 수 있다. 여기서는 Kubeflow Jupyter Notebook에 Mount 되어 있는 __Persistant Volume Claim(PVC)__ 에 Model을 저장한다.
  
- Model Code

```python
import tensorflow as tf
from matplotlib import pyplot as plt
import numpy as np

# Tensorflow + MobileNet
# Kubeflow Jupyter Notebook 위에서 코드를 실행시켰다. (사실 이건 어떻게 되었든 상관 없음)
# Directory 형태로 Model을 만드는데 '${Model Name}/${Nubmer}/' 안에 만들어진 Model을 저장
# Path : pvc://dc-test-volume/mobilenet_tf/mobilenet

# Load Data
file = tf.keras.utils.get_file(
    "grace_hopper.jpg",
    "https://storage.googleapis.com/download.tensorflow.org/example_images/grace_hopper.jpg"
)

# Data Preprocessing
img = tf.keras.preprocessing.image.load_img(file, target_size=[224, 224])
plt.imshow(img)
plt.axis('off')
x = tf.keras.preprocessing.image.img_to_array(img)
x = tf.keras.applications.mobilenet.preprocess_input(x[tf.newaxis,...])

# Label Setting
labels_path = tf.keras.utils.get_file('ImageNetLabels.txt','https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt')
imagenet_labels = np.array(open(labels_path).read().splitlines())

# Model Training
pretrained_model = tf.keras.applications.MobileNet()
result_before_save = pretrained_model(x)

decoded = imagenet_labels[np.argsort(result_before_save)[0,::-1][:5]+1]

print("저장 전 결과:\n", decoded)

# Model Save : Serving하는 과정에서 Model을 불러올 때 경로는 반드시 '{Model Name}/{Number}' 형태로 지정해준다.
tf.saved_model.save(pretrained_model, "mobilenet_tf/1")
```
  
## InferenceService YAML file 작성 및 생성
  
- Serving하기 위한 Model이 담긴 __YAML__ file을 작성한다.
  
```yaml
# Version에 따라서 YAML 구조가 조금씩 다르게 나타나기 때문에 Version은 반드시 확인하고 넘어간다.
apiVersion: "serving.kserve.io/v1beta1"
kind: "InferenceService"
metadata:
  annotations:
    sidecar.istio.io/inject: "false"
  # Serving Name
  name: "mobilenet"
  namespace: "kubeflow-user-example-com"
spec:
  predictor:
    # Serving Engine
    tensorflow:
      # Serving Engine Protocol Version : 상황에 맞춰서 선언해줌
      ProtocolVersion: "v1"
      # Model Storage Path : 여기서는 'dc-test-volume'이라는 PVC를 지정하고,
      # Path는 'mobilenet_tf/1'로 설정했다.
      # pvc://dc-test-volume/mobilenet_tf/1
      storageUri: "pvc://{PVC Name"}/{Path}"
```

YAML file을 만들었다면 Kubernetes에 올린다. Kubeflow Central Dashboard 위에서 올려도 되고, CLI로 직접 apply 해주어도 상관 없다.

```shell
kubectl create -f ${INFERENCE_YAML}
```

여기서 Model을 Serving하는 대략적인 Logic은 다음과 같다.

1. Inference Service YAML __배포__
2. __Pod 1개__ , __Service 4개__ (Service Name : {Model Name}, {Model Name}-defualt, {Model Name}-defaul-0001, {Model_Name}-default-0001-private)
3. Pod를 생성하면서 _storageUri_ Field에 지정한 __PVC__ 를 Pod 안의 ```/mnt``` 안에 __Mount__ 한다.
4. ```/mnt``` 안에 ```models``` 라는 _Directory_ 를 생성하고 _storageUri_ Field의 __Path__ 로 지정된 Directory 혹은 File을 해당 경로로 __Pulling__ 한다.
5. _Srving Engine_ 은 ```/mnt/models``` 안으로 가져온 Model을 Serving 한다.

## Serving Model에 대한 REST API 정보 가져오기

Model을 생성하고 정상적으로 Kubernetes에 Serving을 했다면, 다음과 같은 명령어를 통해 정상적으로 올라갔는지 확인할 수 있다.
  
```shell
# Inference Service 상태 조회
kubectl get isvc ${SERVING_NAME} -n ${NAMESPACE}
  
# Pod에도 정상적으로 올라갔는지 확인
kubectl get pod -n ${NAMESPACE} | grep ${MODEL_NAME}
```

- 결과 화면 (참조 정도만 하자)
  
![Alt Text][check_inference_service_status]

정상적으로 올라갔다면, REST API 호출을 위한 Service의 Cluster IP 값을 알아야 하기 때문에 Service 조회를 해준다.

```shell
kubectl get svc -n ${NAMESPACE} | grep ${MODEL_NAME}
```

![Alt Text][get_inference_service]

Test 환경에서는 Kubernetes 내부에서 진행하기 때문에 ${MODEL_NAME}-default-0001-private 에서 할당된 __Cluster IP__ 와 Serving Port인 __80__ Port를 사용한다. 또한, Kubeflow 설치 과정에서 사용된 Dex 인증을 진행한 뒤에 ID Token 값을 설정해준다.

Serving Model에 대한 REST API 에서 _Endpoint_ 는 __Protocol Version__ 에 따라 나뉜다. _Protocol Version_ __V2__ 기준으로 Serving Model에 대한 Predict Endpoint는 ```/v2/models/${MODEL_NAME}/infer``` 이 된다. 만약 _Protocol Version_ __V1__ 이라면, Predict Endpoint는 ```/v1/models/${MODEL_NAME}:predict``` 가 된다.

## Serving Model Test
> Serving Model에 대한 Test

Prediction REST API Test는 다양하게 할 수 있다.
- Kubeflow Jupyter Notebook 환경에서 ```ipynb``` file 에 Prediction Request
- __Kubeflow Jupyter Notebook 환경에서__ ```py``` __file에 Prediction Request 하고 python3 ${PREDICTION_FILE}__ : 해당 환경에서 Test를 진행한다.
- Kubernetes에 Test 용 __Pod__ 를 올리고 해당 Shell Script 안에서 Test
- Postman 등 __외부__ 에서 Test (AWS EC2 Instance 환경에서 진행할 때는 Public IP를 통해서 접근했다.)

언급한대로, __Kubeflow의 Jupyter Notebook__ 환경에서 Test를 진행하는데, Model을 만들었던 Notebook이 아닌, 다른 Notebook 환경에서 Test를 진행해봤다.

Python Code는 __Data Preprocessing__ 과 __Prediction Test__ Code로 나뉘며, 이렇게 하는 이유는 보통 전처리 코드는 따로 구성을 해두고 불러오기 때문에 이를 가정하고 Setting을 진행한 것이다.

1. Data Preprocessing

전처리 코드에서는 Sample Image를 불러오고 이를 전처리하여 그 결과를 Return 한다. 결과는 __Tensor__ 형태로 나오게 된다.

```python
import tensorflow as tf
import os

# Data Preprocessing Method
def data_preprocess(image_path):
    # Image Resizing(224, 224)
    img = tf.keras.preprocessing.image.load_img(image_path, target_size=[224, 224])

    # Image Preprocessing -> Image to Array
    x = tf.keras.preprocessing.image.img_to_array(img)
    x = tf.keras.applications.mobilenet.preprocess_input(x[tf.newaxis,...])
    
    
    return x.tolist()
```

2. Model Prediction

Model Prediction 코드에서는 전처리 후 나온 Data를 Input Format (Protocol Version에 따른 Format)에 맞추고, Serving Model을 _REST API_ 로 호출하여 Prediction 수행하고 그 결과를 출력한다. __ID Token, Host, Model Name__ 등을 설정해주고 이를 기반으로 Request를 수행한다.

```python
import numpy
import requests
import json
import os

# Preprocess Code Load
from data_preprocessing import data_preprocess

# MobileNet Model Prediction Test
# ID Token Setting
TOKEN = "" # ID Token

# Header Setting (ID Token)
HEADER = {"Cookie" : "authservice_sessoin=" + TOKEN}

# Cluster IP & PORT / Model Name Setting
CLUSTER_IP = "" # Inference Service Cluster IP
CLUSTER_PORT = "" # Inference Service Cluster Port
MODEL_NAME = "" # Model Name

# Sample Image & Data Preprocessing
image_path = os.getcwd() + "/sample_img.png" # Sample Image Path Input
preprocessed_data = data_preprocess(image_path) # Data Preprocessing

# Input Shape Formatting
data = json.dumps({"instances" : preprocessed_data})

# URL Setting
url = "http://" + CLUSTER_IP + ":" + CLUSTER_PORT + "/v1/models/" + MODEL_NAME + ":predict"

# Request & Response
response = requests.post(url, data=data, headers=HEADER)

# Numpy Convert & Print
result = numpy.array(response.json()["predictions"])
print(result)
```

정상적으로 Prediction을 수행한다면, 아래와 같은 결과가 나온다.

```
{'predictions': [[6.6335673e-08, 4.0237822e-09, ...
...
...
, 5.67394398e-09, 4.12778064e-07]]}
```

이 외에도 다양한 방식으로 Test를 해볼 수 있겠지만, CLI 환경에서 Test 하는 것은 의미가 없을 것 같아서 제외했다. 대략 로직을 설명해주자면, Test 하기 위한 Pod (OS 환경은 상관없다.)를 하나 만들어주고, Shell Script로 접속한 다음에 ID Token, Model Name, Host 정보 설정하고 Input Shape에 맞춘 Data를 cURL로 날려주면 비슷한 결과가 나올 것이다.

----------------------

# 3. KServe Dex Authentication <a name="dex_auth"/>

## Dex Auth : ID Token through REST API
__Dex__ 란 3rd Party로부터 _OAuth Token_ 을 가져와 관리하는 인증 도구로, Kubeflow를 설치하게 되면 Dex가 설치되는데, 이를 활용해서 KServe 기반의 Model Serving이후 필요한 인증 ID Token 값을 발급받고 이를 활용하여 Serving Model에 Data Input을 수행한다.

<details>
  <summary>Dex 인증을 요구하는 자원</summary>
  <div markdown="1">
  &nbsp;&nbsp;&nbsp;&nbsp;1. Kubeflow Central Dashboard (Login)
  </div>
  <div markdown="2">
  &nbsp;&nbsp;&nbsp;&nbsp;2. KFServing/KServe
  </div>
  <div markdown="3">
  &nbsp;&nbsp;&nbsp;&nbsp;3. Knative Serving
  </div>
  <div markdown="4">
  &nbsp;&nbsp;&nbsp;&nbsp;4. Istio Virtual Service
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
  &nbsp;&nbsp;&nbsp;&nbsp;- authservice_session=MTY...YtfZ
  </div>
  <div markdown="2">
  &nbsp;&nbsp;&nbsp;&nbsp;- Path=/
  </div>
  <div markdown="3">
  &nbsp;&nbsp;&nbsp;&nbsp;- Expires=Thu, 21 Jul 2022 05:30:11 GMT
  </div>
  <div markdown="4">
  &nbsp;&nbsp;&nbsp;&nbsp;- Max-Age=86400
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

-------------------

#### Reference :
- [KServe Github](https://github.com/kserve/kserve)
- [KServe Website](https://kserve.github.io/website)
- [Dex 인증/우회](https://1week.tistory.com/83)
- [KServe Concept 참조](https://devocean.sk.com/blog/techBoardDetail.do?ID=163739)

[first_dex_trial_screen]:https://imgur.com/ZNxXlKY.png
[ingress_url_call]:https://imgur.com/rMZbdp0.png
[get_req]:https://imgur.com/jfqjoN7.png
[account_and_req_auth]:https://imgur.com/64fCZMx.png
[get_approval]:https://imgur.com/AZ84iwi.png
[get_id_token_and_result]:https://imgur.com/i57E2PJ.png
[dex_auth_id_token_test_result]:https://imgur.com/UV3hZ9M.png
[dex_auth_id_token_test_result_cluster_ip]:https://imgur.com/fff0Uc8.png
[check_inference_service_status]:https://imgur.com/3ZTMVhU.png
[kserve_structure]:https://imgur.com/NU2oBQ8.png
[kserve_architecture]:https://imgur.com/rGnc7dy.png
[get_inference_service]:https://imgur.com/vmED0lg.png
