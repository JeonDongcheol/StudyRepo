# Kubernetes
> 공부한 내용 & 실습들을 정리
> Index를 통해서 필요한 부분으로 이동할 수 있도록 해두었으니 참조
> Kubernetes 느낀점 : 끝이 없다 정말...
> Kubeflow 쪽이 생각보다 정리할 것이 많아서 22/09/01 기준으로 따로 분리

### Index :
1. [__What is Kubernetes?__](#about_k8s)
1. [__Kubernets Installation__](#install_k8s)
2. [__Kubeflow Installation__](#install_kubeflow)
3. [__Kubeflow Multiuser Isolation__](#multiuser)
4. [__Kubernetes Resource__](#k8s_resource)

Ref. [**Kubernetes Useful Command**](#kubernetes_useful_cmd)

# 1. What is Kubernetes <a name="about_k8s" />
> Kubernetes에 대한 개념을 잡아보자

Kubernetes(a.k.a k8s)는 _Container_ 를 쉽고 빠르게 배포 및 확장하고 관리를 자동화해줄 수 있도록 하는 Open Source Platform으로, __MSA__ & __Cloud Platformm__ 을 지향하고 Container로 이루어진 Application을 손쉽게 담고 관리할 수 있도록 해준다. __Serverless__ , __CI/CD__ , __Machine Learning__ 등 다양한 기능들이 Kubernetes 위에서 동작 가능하다.

Kubernetes는 다양한 배포 방식들을 지원하는데, 대표적으로 나열하자면 다음과 같다.

- __Deployment__ : New Version Application을 다양한 전략을 통해 중단 없이 배포
- __StatefulSets__ : 실행 순서를 보장하고 __Host Name__ 과 __Volume__ 을 일정하게 사용할 수 있어서, 순서 혹은 데이터가 중요한 경우 사용
- __DaemonSets__ : _Log_ , _Monitoring_ 등 모든 Node에 설치가 필요한 경우
- __Job__ , __CronJob__ : _Batch_ 성 작업

![Alt Text][k8s_deployment]

### Kubernetes Desired State

![Alt Text][k8s_desired_state]

- __Desired State__ : 관리자가 바라는 환경으로, 얼마나 많은 Web Server가 실행되고 있으면 좋은지, 몇 번 Port로 서비스하길 원하는지 등
- __Current State__ : 현재 상태를 Monitoring하면서 Desired State를 유지하려고 내부적으로 여러 작업들을 수행함

관리자가 Server를 배포할 때 직접적인 동작을 명령하지 않고 __State__ 를 선언하는 방식을 사용한다. 예를 들어서 Nginx Container를 실행하는데, 80번 Port로 Open(명령, Imperative) 한다는 명령어는 80번 Port를 Open한 Nginx Container를 1개 유지(선언, Declarative)해달라는 선언으로 한다고 보면 된다.

### Object
> Kubernetes에서 사용되는 Base Object로 매우 중요하다.

- __Pod__ : Kubernetes에서 배포할 수 있는 __가장 작은 단위__ 로, 한 개 이상의 _Container, Storage, Network_ 속성을 가진다. Pod에 속한 Container는 Storage와 Network를 공유하고, 서로 Localhost로 접근이 가능하다. Container 하나만 사용하는 경우에도 반드시 Pod로 감싼다. Pod의 구조는 아래와 같다.

![Alt Text][pod_structure]

- __ReplicaSet__ : Pod를 여러 개(한 개 이상) 복제하여 관리하는 Object로, Pod를 생성하고 개수를 유지할 때 사용한다. 복제할 개수, 개수를 체크할 Label Selector, 생성할 Pod의 설정 값(Template) 등을 가지고 있다.

- __Service__ : _Network_ 와 관련된 Object로, Pod를 외부 Network와 연결해주고, 여러 개의 Pod를 바라보는 내부 _Load Balancer_ 를 생성할 때 사용한다. 내부 __DNS__ 에 Service 이름을 Domain으로 등록하기 때문에 Service Discovery 역할도 수행한다.

- __Volume__ : Storage와 관련된 Object, Host Directory를 그대로 사용할 수도 있고, EBS 같은 Storage를 동적으로 생성하여 사용할 수도 있다.

Object Spec은 __YAML__ 형태로 구성되며, Object 종류와 원하는 상태를 입력한다. 생성, 조회, 삭제로 관리할 수 있기 때문에 RESTful API로 쉽게 노출할 수 있고, 접근 권한 설정도 같은 개념을 적용하여 누가 어떤 Object에 요청을 할 수 있는지도 정의할 수 있다.

Kubernetes는 Application을 배포하기 위해 _Desired State_ 를 다양한 Object에 __Label__ 을 붙여 정의하고 API Server에 전달한다.

### Architecture

![Alt Text][k8s_architecture]

Kubernetes는 __Master__ 에 _API Server_ 와 _Status Storage_ 를 두고 각 __Node(Server)__ 와 __Agent(Kubelet)__ 와 통신하는 구조를 갖는다. 기본적으로 Node는 전체 Cluster를 _관리_ 하는 __Master__ 와 Container가 _배포_ 되는 __Worekr__ 로 구성이 되는데, 모든 명령은 Master의 _API Server_ 를 통해 호출하고 Worker는 Master와 통신하면서 필요한 작업들을 수행한다. 각각의 Node들은 IP Address를 가지며, Node들이 모여 Cluster를 구성하게 된다. 그래서 Kubernetes에서 포함 관계는 ```Contaiiner < Pod < Node(Master, Worker) < Cluster``` 라고 볼 수 있다.

하나의 Pod가 생성되는 과정은 다음과 같이 표현할 수 있다.

![Alt Text][pod_create_process]

### Kubernetes Component
> Kubernetes에서 중요한 역할을 수행하는 Component들에 대해서 간략하게만 서술한다.

- __Ingress__ : 다양한 Web Application을 하나의 __Load Balancer__ 로 서비스하기 위해 사용하는데, _Proxy Server_ 는 _Domain_ 과 _Path_ 조건에 따라 등록된 Server로 요청을 전달하는데, Server가 바뀌거나 IP Address가 변경되면 매번 수정해야한다. Kubernetes에서는 이를 자동화하여 거의 그대로 사용이 가능하게 해준다.

![Alt Text][ingress]

- __Namespace__ & __Label__ : 하나의 Cluster를 _논리적_ 으로 구분해서 사용 가능하게 해준다.

![Alt Text][namespace_and_label]

- __RBAC(Role-Based Access Control)__ : 접근 권한 시스템으로, 각각의 _Resource_ 에 대하여 User 단위로 CRUD 같은 권한을 쉽게 지정 가능하게 해준다.

![Alt Text][rbac]

- __Cloud Support__ : 외부 Storage를 Container 내부 Directory에 Mount하여 사용하는 것도 일반적인데, _Cloud Controller_ 를 통해 Cloud와의 연동을 쉽게할 수 있도록 한다.

- __CRD(Custom Resource Definition)__ : Kubernetes가 기본적으로 제공하지 않는 기능을 기본 기능과 동일한 방식으로 적용하고 사용 가능하게 해준다. _Kubeflow_ 에서도 여러 CRD가 존재한다.

- __Auto Scaling__ : _CPU_ , _Memory_ 사용량에 딷른 확장 및 현재 접속자 수와 같은 값들을 사용 가능하다.
  - _Horizontal Pod Autoscaler(HPA)_ : Container 개수를 조정
  - _Vertical Pod Autoscaler(VPA)_ : Container Resource 할당량을 조정
  - _Cluster Autoscaler(CA)_ : Server 개수 조정

### CNI(Container network Interface)

Container 간의 _Networking_ 제어를 할 수 있는 _Plug-in_ 을 만들기 위한 표준으로, 공통된 Interface를 제공하기 위해 만들어졌으며, Kubernetes에서는 _Pod_ 간의 통신을 위해서 사용한다. Kubernetes 자체적으로 ```kubelet``` 이라는 CNI Plug-in을 제공하지만, Network 기능이 매우 제한적이어서 __Flannel, Calico, Weavenet, NSX__ 등의 _3rd Party_ CNI Plug-in 을 사용하기도 한다.

![Alt Text][k8s_cni]

-------------------------------------------------------------------

# 2. Kubernetes Installation <a name="install_k8s" />
> Kubernetes 설치하는 과정을 Command Line 위주로 서술한다.

개발 환경에 따라서 차이가 있을 수 있기 때문에 잘 참고해야 한다.

또한 __AWS EC2 Instance__ 위에서 구축을 했기 때문에 추가적인 설정이 들어갈 수도 있으니 참고해야 한다.

<details>
<summary>Kubernetes 기본 구축 환경</summary>
<div markdown="1">
- Cloud : Amzon Web Service(AWS) EC2 Instance
</div>
<div markdown="2">
- OS : Redhet Enterprise Linux(Rhel) 7.9
</div>
<div markdown="3">
- Kubernetes Version : v1.21.9
</div>
<div markdown="3">
- Node 구성 : Master 1대, Worker 3대
</div>
</details>

- 먼저 **Master Node 1대** 와 **Worker Node 3대** 의 환경을 구성하기 위한 기본 Setting을 진행한다.

```bash
# (Optional) 각 Instance에 SSH 접속을 하게 되면 Private IP 주소로 나오기 때문에 이에 대한 간단한 설정만 진행한다
sudo su
hostnamectl set-hostname <Node Name>
su ec2-user

# 기본적으로 ROOT USER가 아닐 때를 가정하고 진행한다.
# 1. yum repo check
sudo yum repolist all
sudo yum update -y

# /etc/hosts에 Cluster를 구성할 IP를 넣어준다.
sudo vi /etc/hosts

# 안에 들어갈 내용 : 완료되면 저장하고 나온다.
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
# IPv6는 사용하지 않기 때문에 주석 처리
#::1         localhost localhost.localdomain localhost6 localhost6.localdomain6

<Master Node Private IP>   master1
<Worker1 Node Private IP>   worker01
<Worker2 Node Private IP>   worker02
<Worker3 Node Private IP>   worker03
```

- __Docker__ 와 사용할 것이므로 Docker를 사전에 설치해주도록 한다. Docker 설치를 했다면 ```kubeadm init``` 과정에서 __kubelet__ 관련 이슈를 제거하기 위해 ```/etc/docker``` 경로에 ```daemon.json``` 파일을 추가해주도록 한다.

```bash
# /etc/docker 경로에 daemon.json 파일 추가 -> kubeadm init 시 kubelet 관련 이슈를 제거
cat <<EOF | sudo tee /etc/docker/daemon.json
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}cd
EOF

# Docker daemon reload 및 Docker Re-start
sudo systemctl daemon-reload
sudo systemctl restart docker
sudo systemctl enable docker
```

- Kubernetes 설치하기 전 *System Configuration* 을 진행한다.

```bash
# 방화벽 Disable : firewalld 자체가 없으면 Error
sudo systemctl stop firewalld && sudo systemctl disable firewalld

# Swap off
swapoff -a && sudo sed -i '/swap/s/^/#/' /etc/fstab

# SE Linux Off
sudo setenforce 0
sudo sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' /etc/selinux/config

# Kubernetes Configuration Setting

cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
br_netfilter
EOF

cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

sudo sysctl --system

# Kubernetes, Centos 우회 Repo Registration
# [주의!] 처음에 vi를 통해서 작성을 하게 되면 '$' 부분이 정상적으로 적용이 안되는 Case가 발생한다.
# 반드시 re-check해주고 수정해준다.
# [Kubernets Repo]
cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-\$basearch
enabled=1
gpgcheck=0
#repo_gpgcheck=1
#gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
exclude=kubelet kubeadm kubectl
EOF

#[Centos7 Repo]
# 마찬가지로 re-check
cat <<EOF | sudo tee /etc/yum.repos.d/cent7.repo
[base]
name=CentOS-$releasever - Base
baseurl=http://mirror.centos.org/centos/7/os/$basearch/
gpgcheck=0

[updates]
name=CentOS-$releasever - Updates
baseurl=http://mirror.centos.org/centos/7/updates/$basearch/
gpgcheck=0
EOF

# 적용 후 update
sudo yum repolist all
sudo yum update -y
```

- System & Kubernetes Configuration까지 설정했다면, 본격적으로 Kubernetes를 사용하기 위한 Package들을 설치한다. 설치하는 Package는 다음과 같다.

1. **Kubeadm**
2. **Kubelet**
3. **Kubectl**

```bash
# Kubernetes 설치를 위한 Version Check
sudo yum list ==showduplicates kubeadm --disableexcludes=kubernetes

# Version Check에서 Release Version 문제가 발생하면 수행
sudo su
echo 7Server > /etc/yum/vars/releasever
su ec2-user

# Kubelet Kubeadm Kubectl Version에 맞춰서 설치 : 여기서는 1.21.x 버전 사용
sudo yum install -y kubelet-1.21.1-0 kubeadm-1.21.1-0 kubectl-1.21.1-0 --disableexcludes=kubernetes

# Enable kubelet(Kubernetes)
# 다 끝나고 version check 통해서 설치되었는지 확인
sudo systemctl enable --now kubelet
kubelet --version
kubeadm version
kubectl version
```

- 정상적으로 버전이 나온다면 설치가 완료되었다는 것이므로, 다음으로는 Master Node와 Worker Node의 환경을 구성해준다.

- __Master Node__ (Worker Node에서는 해당 작업을 수행하지 않음)

```bash
# Master Node에서 Initialization을 할 때 Endpoint는 Master Node가 설치되어 있는 Instance의 Private IP를 넣어준다.
# 기본적으로 Kubernetes는 6443 Port를 사용한다.
# kubeadm init을 하게 되면, Token, Certification Hash Key 값이 나옴 : 모르면 아래의 Command를 참조한다.
sudo kubeadm init --control-plane-endpoint "<Master Node Private IP>:6443" --upload-certs

# (Optional) Token 값을 모를 때
kubeadm token list

# (Optional) Certification Hash 값을 모를 때
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed 's/^.* //'

# Initilization이 끝나면 Root Mode를 설정해준다.
export KUBECONFIG=/etc/kubernetes/admin.conf

# 일반 사용자를 위한 Configuation Setting
# .kube directory에 admin config file 복사
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
# config file 권한 설정
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

- **Worker Node** (Master Node에서는 해당 작업을 수행하지 않음)

```bash
# Master Node와 Connection을 위한 작업으로, Master Node Private IP를 가져옴
# Token, Certification Hash Value는 위에서 작업한 것을 토대로 가져온다.
sudo kubeadm join <Master Node Private IP>:6443 --token <Token Value> --discovery-ca-cert-hash sha256:<Certification Hash Value>
```

- 여기까지 작업이 다 끝났다면, Master Node가 설치되어 있는 Instance를 시원하게 Reboot 해준 뒤에, __CNI__ 설치하고 정상적으로 Connection이 되었는지 확인해준다.

```bash
# After Reboot
curl https://docs.projectcalico.org/manifests/calico.yaml -O

# Kubernetes에 다운받은 CNI 적용
kubectl apply -f calico.yaml

# Node Connection Check
kubectl get nodes -o wide

# (Optional) kubectl 명령어를 계속 쓰게 되는데 보통 alias 설정을 k로 해준 뒤에 작업을 많이 한다. 이에 대한 Command
# .bashrc 열기 (Root 권한으로 Open)
sudo vi ~/.bashrc

# .bashrc에 alias 등록
alias k='kubectl'

# alias 적용 (kubectl -> k)
source ~/.bashrc
```

- 모두 정상적으로 설치되었을 때 나오는 화면 :

![Alt Text][kubernetes_install_success]

--------------------

# 3. Kubeflow Installation <a name="install_kubeflow" />
> Kubeflow에 대한 설치 과정을 Command Line 위주로 작성한다. 아무래도 생각보다 어려운 작업이 아닌가 싶다.


# 4. Kubeflow Multiuser Isolation <a name="multiuser" />
> Kubeflow를 사용하는 과정에서 Multi User에 대한 설정을 안내한다. 이를 활용해서 Kubeflow 관련 작업을 할 때 계정을 구분 할 수 있지 않을까 싶다.

Kubeflow에서 작업을 하다보면 User Account가 추가적으로 있으면 좋겠다는 생각을 할 때가 있다. 관련 프로젝트를 할 때 한 계정으로 작업하기엔 무리가 있고, 리소스를 계정 단위로 구분하고 싶을 때, Kubeflow에서는 Dex 기반의 __Multi User Isolation__ 을 적용한다. Kubeflow에서 계정을 추가로 할당하는 방법은 크게 3가지 단계를 거친다.

1. __Dex__ 의 _ConfigMap_ 에 계정 추가
2. __Dex__ Deployment _Restart_
3. __Profile__ 생성 : 생성한 계정 owner로 지정

위 2단계를 거치게 되면, Dex에 계정이 추가되면서 해당 계정에 Namespace를 할당할 수 있다. 그와 동시에 리소스를 분할해서 관리할 수 있게 된다. (물론 Terminal에서는 공통된 Resource로 관리된다는 점...)

### [1] Dex의 ConfigMap에 계정 추가

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

### 2. Profile

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

### 3. Usage in Python

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

-------------------

# 5. Kubernetes Resource <a name="k8s_resource" />
> Kubernetes에 대한 Resource를 간단하게 안내

Kubernetes에서는 __Pod__ 를 설정하면서 Container에 필요한 Resource를 지정할 수가 있는데, 기본적으로 __CPU__ 와 __Memory(RAM)__ 를 지정할 수 있다. Resource 할당은 2개의 분류로 나누어서 할 수 있는데, 다음과 같다.

- Requests : Pod를 실행시키기 위한 Minimum Resource
- Limits : Pod가 사용할 수 있는 Maximum Resource

### Resource 단위

- CPU : CPU 단위로 측정이 되는데, 기본적으로 __m__ 을 사용하여 "Milli-core" 단위로 표현을 한다. 즉 ```100m``` 은 ```100 milli-core```를 나타내며, 이는 1 CPU 기준 0.1에 해당한다. CPU 단위로도 표현할 수 있지만, 주로 Detail Control을 위해 milli-core 단위로 많이 표기한다.
- Memory(RAM) : Memory는 Byte 단위로 측정이 되는데, ```E, P, T, G, M, k``` 와 같은 수량 접미사를 사용할 수도 있고, ```Ei, Pi, Ti, Gi, Mi, Ki``` 와 같은 2의 거듭제곱 형태로도 사용할 수 있다.

> 여기서 대소문자의 구분을 명확하게 해줄 수 있도록 한다.

YAML 파일에서 어떻게 표현이 되는지 Inference CRD를 기반으로 간단하게 나타내보았다.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  annotations:
    sidecar.istio.io/inject: "false"
  name: volume-test
  namespace: kubeflow-user-example-com
spec:
  predictor:
    sklearn:
      protocolVersion: v2
      resources:
        limits:
          cpu: 750m
          memory: 1Gi
        requests:
          cpu: 500m
          memory: 2Gi
      storageUri: pvc://test-volume/model/model.joblib
```

- Overcommit : Node 내의 Container 모든 Resource의 __Limit__ 합계가 Node 전체 Resource의 양을 초과한 상태로, Kubernetes는 Overcommit을 허용하는데, 보통 Node가 _Scale up_ 되어지거나, Pod가 삭제되고 다시 생성된다. 이때 Pod가 삭제되는 순서는 Resource 요청을 _가장 많이 초과한_ Pod부터 삭제된다.

### GPU Resource
> NVIDIA GPU

Kubeflow 자체가 _MLOps_ 를 위한 것이기 때문에 대부분 GPU를 사용하게 될 것이다. 그래서 GPU를 사용하는 방법에 대해서 간단하게 서술하려고 한다. 흐름은 [Kubernetes - GPU 스케줄링](https://kubernetes.io/ko/docs/tasks/manage-gpus/scheduling-gpus/) 을 참조했으며, __AWS EC2 Instance__ 중에서 __G4dn.xlarge__ 을 기반으로 작업했다. (사실 돈 나가는 것이 무서워서 G4dn 했음...) G4dn은 __NVIDIA GPU Tesla T4__ 1개를 사용한다.

GPU를 할당하고 싶다면 Computing Resource에 GPU가 있어야 하며, 해당 Computer를 Cluster에 구성할 수 있어야 한다.

NVIDIA GPU Resource를 사용하기 위해서 우선 __NVIDIA GPU Driver__ 를 설치해야한다. [GPU Driver 검색](https://www.nvidia.com/Download/index.aspx?lang=en-us) 에 가서 맞는 버전을 찾아서 다운받은 다음에 설치를 진행한다.

Driver 설치 과정에서 다양한 오류들이 발생할 수도 있는데, (Nouveau 충돌 이슈, Kernerl Install 이슈 등...) 이 과정들은 구글링을 통해서 해결하는 것이 더 나을 것 같다. Driver 설치 후 __NVIDIA Docker 2.0__ 를 설치하는데, 과정은 다음과 같다.

- Repository 및 GPG Key 설정

```shell
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
      && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
      && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

- NVIDIA Docker 2.0 Install

```shell
sudo yum update
sudo yum install -y nvidia-docker2
```

- NVIDIA Docker 2.0 설치가 정상적으로 끝나면 Docker의 ```Daemon.json``` 파일을 수정

```shell
# sudo vi /etc/docker/daemon.json
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}

sudo pkill -SIGHUP dockerd

# Restart Docker
sudo systemctl restart docker
```

작업을 마친 후 ```nvidia-smi``` 를 Terminal에 입력하면 다음과 같은 NVIDIA GPU Spec이 나온다.

![Alt Text][nvidia-smi]

이후 해당 Computer를 Node로 붙인 후 Kubernetes에서 NVIDIA GPU를 사용할 수 있게 _Master_ Node에서 __Kubernetes NVIDIA Device Plugin__ 을 설치해준다.

```shell
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/1.0.0-beta4/nvidia-device-plugin.yml
```

GPU를 사용할 수 있도록 설정을 해주었으니, 이를 Pod에 할당해주면 된다.

Pod 혹은 CRD에 할당하는 방법은 다음과 같이 Resource 선언 부분에서 _Requests_ 및 _Limits_ 에 정의해주면 되는데, 주의할 점은 Limit와 Request의 GPU 수를 __반드시__ 동일하게 맞춰주도록 한다.

```yaml
# GPU 스케줄링을 가져옴
apiVersion: v1
kind: Pod
metadata:
  name: cuda-vector-add
spec:
  restartPolicy: OnFailure
  containers:
    - name: cuda-vector-add
      # https://github.com/kubernetes/kubernetes/blob/v1.7.11/test/images/nvidia-cuda/Dockerfile
      image: "k8s.gcr.io/cuda-vector-add:v0.1"
      resources:
        limits:
          nvidia.com/gpu: 1
  nodeSelector:
    accelerator: nvidia-tesla-p100 # 또는 nvidia-tesla-k80 등.
```

여기서 __Node Selector__ 에 대한 설명을 간단하게 하자면 해당 GPU Node에 __Label__ (accelerator)을 달고, value를 본인이 구분할 수 있도록 GPU Model명을 달아주면, 추후에 다양한 GPU Model이 있을 때 Node Selector를 통해서 원하는 GPU Model을 할당할 수 있다. Kubeflow의 Notebook, Inference 등도 위와 같이 정의해주면 된다.

참고로 Kubeflow Notebook의 생성 화면에서 GPU를 할당할 때 Plugin 설치가 되어있지 않으면 GPU Vendor가 없다고 나오며, GPU Node를 할당하지 않았거나 설정 과정에서 오류가 있어서 정상적으로 할당이 불가능하면 Pod가 생성되지 않는다. 가급적이면 Sample Pod로 올려보고 사용하는 것이 좋지 않을까 싶다.

또한, AWS 및 타 Cloud Service 회사에서 GPU Resource를 이용하게 되면 비용이 꽤 많이 부가된다. 그래서 습관적으로 On/Off 할 수 있는 습관을 들이면 좋을 것 같다.

#### Resource 부분은 배워갈 때마다 하나씩 추가하도록 한다.

---------------------

# Ref. Kubernetes Useful Command <a name="kubernetes_useful_cmd" />
> Kubernetes를 사용하면서 알아두면 유용한 Command를 기록해둔다.

- Pod 재시작 : ```kubectl get pod -n ${NAMESPACE} ${POD_NAME} -o yaml | kubectl replace --force -f-```
- Pod Log 조회 : ```kubectl logs -c ${CONTAINER_NAME} -n ${NAMESPACE} ${POD_NAME}```
- 특정 Service Type으로 Pod 노출 : ```kubectl expose pod -n ${NAMESPACE} {POD_NAME} --type=${SERVICE_TYPE}``` (NodePort, Cluster IP, LoadBalancer)
- Inference Service 환경설정 조회 : ```kubectl edit(describe) configmap -n ${NAMESPACE} inferenceservice-config```
- 특정 Pod Shell Script 접속 : ```kubectl exec --stdin --tty -n ${NAMESPACE} ${POD_NAME} -- /bin/bash```
- Kubernetes Defualt Namespace 설정 : ```kubectl config set-context --current --namespace=${NAMESPACE}```
- Persistant Volume Claim(PVC) State가 'Terminating' 상태로 남아있을 때 삭제하는 방법 : ```kubectl patch pvc -n ${NAMESPACE} ${PVC_NAME} -p '{"metadata": {"finalizers": null}}'```

#### Reference :
- [Kubernetes Documents](https://kubernetes.io/ko/docs/home/)
- [Subicura Kubernetes 안내서](https://subicura.com/k8s/)

[kubernetes_install_success]:https://imgur.com/APkDbp1.png
[k8s_deployment]:https://imgur.com/AVVuwQi.png
[k8s_desired_state]:https://imgur.com/D7RtHwT.png
[pod_structure]:https://imgur.com/E8LcdJZ.png
[k8s_architecture]:https://imgur.com/6cxacVO.png
[pod_create_process]:https://imgur.com/wQikQok.png
[ingress]:https://imgur.com/D7h3jhP.png
[namespace_and_label]:https://imgur.com/QSBanW5.png
[rbac]:https://imgur.com/BBM8uMM.png
[k8s_cni]:https://imgur.com/LkegChr.png
[auth_get_all]:https://imgur.com/z29X5yr.png
[nvidia-smi]:https://imgur.com/JomsaIy.png
