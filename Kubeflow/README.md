# Kubeflow
> Kubernetes 파트에서 정리를 하다보니 작업이 많아져서 분리
 
> Inference 부분은 따로 KServe로 분할

>  Pipline, Hyperparameter 부분은 아직 없음

### Index :
1. [__What is Kubeflow?__](#about_kubeflow)
2. [__Kubeflow Installation__](#install_kubeflow)
3. [__Kubeflow Multiuser Isolation__](#multiuser)

# 2. Kubeflow Multiuser Isolation <a name="multiuser" />
> Kubeflow를 사용하는 과정에서 Multi User에 대한 설정을 안내한다. 이를 활용해서 Kubeflow 관련 작업을 할 때 계정을 구분 할 수 있지 않을까 싶다.

Kubeflow에서 작업을 하다보면 User Account가 추가적으로 있으면 좋겠다는 생각을 할 때가 있다. 관련 프로젝트를 할 때 한 계정으로 작업하기엔 무리가 있고, 리소스를 계정 단위로 구분하고 싶을 때, Kubeflow에서는 Dex 기반의 __Multi User Isolation__ 을 적용한다. Kubeflow에서 계정을 추가로 할당하는 방법은 크게 3가지 단계를 거친다.

1. __Dex__ 의 _ConfigMap_ 에 계정 추가
2. __Dex__ Deployment _Restart_
3. __Profile__ 생성 : 생성한 계정 owner로 지정

위 2단계를 거치게 되면, Dex에 계정이 추가되면서 해당 계정에 Namespace를 할당할 수 있다. 그와 동시에 리소스를 분할해서 관리할 수 있게 된다. (물론 Terminal에서는 공통된 Resource로 관리된다는 점...)

### - Dex의 ConfigMap에 계정 추가

Kubeflow의 컴포넌트를 낱개로 설치한 것이 아닌 전체를 설치했다고 가정했을 때, __Dex__ 가 설치된다. Dex를 통해서 사용자 인증을 하게 되는데, Kubeflow Central Dashboard의 로그인도 Dex 인증을 타게 된다. 기본적으로 Dex는 _Auth_ Namespace에 할당되어있는데, Auth Namespace가 갖고 있는 자원은 아래와 같다. (Command : ```kubectl get all -n auth``` )

![Alt Text][auth_get_all]

또한 Dex ConfigMap은 ```kubectl get configmap -n auth``` 를 통해서 있는지 확인할 수 있다. Dex ConfigMap은 다음과 같이 구성이 되어있다.

```yaml
# Please edit the object below. Lines beginning with a '#' will be ignored,
# and an empty file will abort the edit. If an error occurs while saving this file will be
# reopened with the relevant failures.
#
apiVersion: v1
data:
  config.yaml: |-
    issuer: http://dex.auth.svc.cluster.local:5556/dex
    storage:
      type: kubernetes
      config:
        inCluster: true
    web:
      allowedOrigins: ['*']
      http: 0.0.0.0:5556
    logger:
      level: "debug"
      format: text
    oauth2:
      skipApprovalScreen: true
    enablePasswordDB: true
    staticPasswords:
    - email: $EMAIL
      hash: $HASH_VALUE
      # https://github.com/dexidp/dex/pull/1601/commits
      # FIXME: Use hashFromEnv instead
      username: user
      userID: $USER_ID
    staticClients:
    # https://github.com/dexidp/dex/pull/1664
    - idEnv: OIDC_CLIENT_ID
      redirectURIs: ["/login/oidc"]
      name: 'Dex Login Application'
      secretEnv: OIDC_CLIENT_SECRET
kind: ConfigMap
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"v1","data":{..."name":"dex","namespace":"auth"}}
  creationTimestamp: "2022-07-27T08:03:13Z"
  name: dex
  namespace: auth
  resourceVersion: "71276012"
  uid: $UID
```

계정을 추가하기 위해서는 해당 YAML File에서 __data__ 의 __config.yaml__ 을 수정해야한다. 참고로 config.yaml 안에 있는 데이터는 String인 것을 참고하도록 한다. config.yaml 안의 ```staticPasswords``` field를 보면 email, hash, username, userID로 구성이 되어 있는 것을 볼 수 있는데, 저 형식에 맞추어 계정을 추가한다. 추가할 때 Format은 다음과 같이 하면 된다.

```yaml
# staticPassword에 추가할 데이터로 Sample이니 참고한다.
# 이대로 갖다 붙이면 반드시 에러나니까 잘 보고 위의 포맷과 함께 맞출 수 있도록 한다.
# Email은 로그인할 계정
- email: ${USER EMAIL}
  # Password 값인데, Password를 Hash 값으로 변환한 결과이다.
  hash: ${PASSWORD_TO_HASH}
  username: ${USER_NAME}
  userID: ${USER_ID}
```

Hash 값으로 변환하는 작업은 hash 변환기를 검색해서 변환해도 좋고, python의 경우, ```bcrypt``` Module을 사용해서 변환할 수 있다.

Configmap을 수정했으니, 해당 Configmap이 적용되어있는 _Dex Deployment_ 를 Restart하면서 변경사항을 반영해준다.

```shell
kubectl rollout restart deployment -n auth dex
```

### - Profile

Dex 계정을 정상적으로 생성했다면, Kubeflow Central Dashboard에 로그인할 때 Namespace가 할당되어있지 않을 것이다. 그도 그럴 것이 Configmap을 수정해서 계정만 추가했을 뿐, Namespace를 건드는 작업을 하지 않았기 때문이다. 그렇다고 Namespace만 생성하기엔 Kubeflow 작업을 수행할 때 온갖 에러를 마주하며, 자원 사용에 있어서 제약이 없기 때문에 Kubeflow에서 제공하는 CRD(Custom Resource Definition)인 __Profile__ 을 사용해서 Namespace를 자동으로 생성하게 해준다.

Profile을 생성할 때 owner를 지정해주는 부분이 있는데, 이 부분을 생성했던 계정의 email로 설정해주고 배포해주면 된다.

```yaml
# Please edit the object below. Lines beginning with a '#' will be ignored,
# and an empty file will abort the edit. If an error occurs while saving this file will be
# reopened with the relevant failures.
# Profile Format
apiVersion: kubeflow.org/v1
kind: Profile
metadata:
  creationTimestamp: "2022-08-31T04:07:40Z"
  # Profile Name이 Namespace로 할당된다.
  name: ${Profile_Name}
spec:
  # Owner 부분을 생성한 계정으로 지정해줄 수 있도록 한다.
  owner:
    kind: User
    name: ${User_Email}
  # Profile 단위로 Resource 제한을 둘 수 있는데, 이 부분은 추후에 다루도록 한다.
  resourceQuotaSpec: {}
```

Profile을 정상적으로 생성했다면, ```kubectl get namespace``` 를 통해서 해당 Namespace가 정상적으로 생성되었는지 확인할 수 있다. 생성된 Namespace는 아래와 비슷한 구조를 가진다.

```yaml
# Please edit the object below. Lines beginning with a '#' will be ignored,
# and an empty file will abort the edit. If an error occurs while saving this file will be
# reopened with the relevant failures.
#
apiVersion: v1
kind: Namespace
metadata:
  annotations:
    owner: ${OWNER_EMAIL}
  creationTimestamp: "2022-08-31T04:07:40Z"
  labels:
    app.kubernetes.io/part-of: kubeflow-profile
    katib.kubeflow.org/metrics-collector-injection: enabled
    kubernetes.io/metadata.name: ${NAMESPACE}
    pipelines.kubeflow.org/enabled: "true"
    serving.kubeflow.org/inferenceservice: enabled
  name: ${NAMESPACE}
  ownerReferences:
  - apiVersion: kubeflow.org/v1
    blockOwnerDeletion: true
    controller: true
    kind: Profile
    name: ${OWNER_userID}
    uid: ${UID}
  resourceVersion: "71005888"
  uid: ${NAMESPACE_UID}
spec:
  finalizers:
  - kubernetes
status:
  phase: Active
```

이후에 Kubeflow Central Dashboard 로그인을 하게 되면 정상적으로 Namespace도 할당받는 것을 볼 수 있을 것이다.

### [Ref] Usage in Python

이 모든 것을 Kernel 환경에서 하기엔 다소 무리가 있다. (결국 어떤 개발 언어 속에서 작업을 할 것이기 때문이다.) Python에서 작업할 때는 Kubernetes SDK를 활용해서 ConfigMap을 수정하고 Deployment를 재시작해주면서 Profile을 자동으로 시작하게 해주면 될 것 같다. 내가 작업했던 코드를 일부 공유하자면 아래와 같다.

```python
from kubernetes import config, client
from bcrypt import hashpw, gensalt

# Kubernetes Config File Load
config.load_kube_config()

# Kubernetes Client SDK API 정의
CUSTOM_OBJECT_API = client.CustomObjectsApi()
CORE_V1_API = client.CoreV1Api()
APPS_V1_API = client.AppsV1Api()

# Kubeflow Profile, Dex ConfigMap 수정 과정에서 필요한 것들
GROUP = "kubeflow.org"
VERSION = "v1"
PLURAL = "profiles"
KIND = "Profile

"""
일부 코드는 생략(Skip) 했다.
코드는 Python 기반의 Pseudo Code이며,
정확하게 사용하기 위해서는 본인 입맛에 맞출 수 있도록 한다.
"""

# Email을 기반으로 Namespace 할당
namespace = str(data.get("email")).split("@")[0]

# Dex Configmap에 들어갈 Password Hash 값을 만들기 위한 작업
# Password를 UTF-8로 Encoding -> Hash 값으로 나온 Password를 UTF-8로 다시 Decoding
# Salt는 Hash를 만들 때 적용하는 규칙이라고 보면 되는데, 궁금하면 검색
password = hashpw(
  password = data.get("password").encode("utf-8"),
  salt=gensalt(rounds=10)).decode("utf-8")
)

# ConfigMap에 사용자를 추가하기 위한 Format 정의
multiuser_format = (
  "-email: " + data.get("email") +
  "\n  hash: " + password +
  "\n  username: " + data.get("username"),
  "\n  userID: " + namespace
)

# Dex Configmap의 config.yaml 할당 : ConfigMap YAML에서 config.yaml은 data 안에 들어있기 때문이며, String형태로 저장될 것이다.
dex_configmap_config_yaml = CORE_V1_API.read_namespaced_config_map(name="dex", namespace="auth").data.get("config.yaml")

# 이 부분은 사실 알아서 정의해준다. 좋은 방법이 있으면 그걸로 하면 된다.
# staticPasswords 다음에 staticClients가 왔기 때문에 이를 기점으로 나눠서 추가하고 다시 붙여주었다.
dex_configmap_config_yaml = (
  dex_configmap_config_yaml.split("staticClients:")[0] +
  multiuser_format +
  "\nstaticClients:" +
  dex_configmap_config_yaml.split("staticClients:")[1]
)

# 재정의했던 config.yaml을 기존의 ConfigMap에 덮어써준다.
CORE_V1_API.patch_namespaced_config_map(
  name="dex",
  namespace="auth",
  body={"data" : {"config.yaml" : dex_configmap_config_yaml}}
)

# Deployment 재시작 : Dex Deployment의 annotation 중 kubectl.kubernetes.io/restartedAt 의 시간을 현재 시간으로 바꿈으로써 재시작해줄 수 있다.
now = str(datetime.datetime.utcnow().isoformat("T") + "Z")
APPS_V1_API.patch_namespaced_deployment(name="dex", namespace="auth", body={
  "spec" : {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": now}}}}
})

# 이제 Profile 생성
kubeflow_user_email = data.get("email")
# Profile은 Kubeflow의 Resource이므로 이는 Custom Resource가 된다.
CUSTOM_OBJECT_API.create_cluster_custom_object(
  group = GROUP,
  version = VERSION,
  plural = PLURAL,
  body = {
    "apiVersion" : GROUP + "/" + VERSION,
    "kind" : KIND,
    "metadata" : {"name" : namespace},
    "spec" : {"owner" : {"kind" : "User", "name" : kubeflow_user_email}}
  }
)
```

해당 Python Code는 참고하기 위한 Source이므로 알아서 바꿔 쓰도록 한다.

---------------------------------


[auth_get_all]:https://imgur.com/z29X5yr.png
