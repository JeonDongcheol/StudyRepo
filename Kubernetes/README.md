# Kubernetes
> 공부한 내용 & 실습들을 정리
> Index를 통해서 필요한 부분으로 이동할 수 있도록 해두었으니 참조
> Kubernetes & Kubeflow 느낀점 : 설치만 잘해도 반은 먹고 들어가는 것 같다.

### Index :
1. [__What is Kubernetes?__](#about_kubernetes)
1. [__Kubernets Installation__](#install_k8s)
2. [__Kubeflow Installation__](#install_kubeflow)
3. [__Kubernetes Resource__](#k8s_resource)

Ref. [**Kubernetes Useful Command**](#kubernetes_useful_cmd)

# 2. Kubernetes Installation <a name="install_k8s" />
> Kubernetes 설치하는 과정을 Command Line 위주로 서술한다.

Kubernetes에 대한 개념은 이미 알고 있다고 가정을 하고 Kubernetes 구축 환경에 대해서 작성을 한다.

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

- 기본 구성을 완료했다면, Kubernetes를 설치하기 전에 **Docker** 를 먼저 설치한다.

```bash
# 사전에 Docker가 설치되어 있다면, 제거하고 다시 설치한다.
sudo yum remove docker \
docker-client \
docker-client-latest \
docker-common \
docker-latest \
docker-latest-logrotate \
docker-logrotate \
docker-engine \
podman \
runc

# Docker Repolist에 Base URL 추가
sudo yum-config-manager \
--add-repo \
https://download.docker.com/linux/rhel/docker-ce.repo

# Docker Stable Base URL 수정을 위해 편집모드 이동
sudo vi /etc/yum.repos.d/docker-ce.repo

# 기존의 Docker CE Stable Base URL 부분을 주석 처리하고, 다음 내용을 추가한다.
# 추가할 내용 : baseurl=https://download.docker.com/linux/centos/7/x86_64/stable

# Docker 설치에 필요한 Package Install
sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/slirp4netns-0.4.3-4.el7_8.x86_64.rpm
sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/container-selinux-2.107-1.el7_6.noarch.rpm
sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/fuse3-libs-3.6.1-4.el7.x86_64.rpm
sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/fuse-overlayfs-0.7.2-6.el7_8.x86_64.rpm

# Dokcer Pakage 설치
sudo yum install docker-ce docker-ce-cli containerd.io -y


# 일반 사용자의 Docker 사용을 위한 작업
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# Docker 실행
sudo systemctl start docker


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

- 여기까지 Docker 설치가 Error 없이 잘 끝났다면, Kubernetes 설치하기 전 *System Configuration* 을 진행한다.

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



-------------------

# 4. Kubernetes Resource <a name="k8s_resource" />
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
1. [Kubernetes Documents](https://kubernetes.io/ko/docs/home/)


[kubernetes_install_success]:https://imgur.com/APkDbp1.png
