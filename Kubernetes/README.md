# Kubernetes
> 공부한 내용 & 실습들을 정리
> Index를 통해서 필요한 부분으로 이동할 수 있도록 해두었으니 참조

### Index :
1. [__Kubernets Installation__](#i1)

# 1. Kubernetes Installation <a name="i1" />
> Kubernetes 설치 

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

- 여기까지 작업이 다 끝났다면, Master Node가 설치되어 있는 Instance를 시원하게 Reboot 해준 뒤에, CNI 설치하고 정상적으로 Connection이 되었는지 확인해준다.

```bash
# After Reboot
curl https://docs.projectcalico.org/manifests/calico.yaml -O

# Kubernetes에 다운받은 CNI 적용
kubectl apply -f calico.yaml

# Node Connection Check
kubectl get nodes -o wide

# (Optional) kubectl 명령어를 계속 쓰게 되는데 보통 alias 설정을 k로 해준 뒤에 작업을 많이 한다. 이에 대한 Command
sudo vi ~/.bashrc

# .bashrc에 alias 등록
alias k='kubectl'

# alias 적용 (kubectl -> k)
source ~/.bashrc
```

- 모두 정상적으로 설치되었을 때 나오는 화면 :

![Alt Text][kubernetes_install_success]

-------------------

#### Reference :
1. [Kubernetes Documents](https://kubernetes.io/ko/docs/home/)


[kubernetes_install_success]:https://imgur.com/APkDbp1.png
