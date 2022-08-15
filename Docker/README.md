# Docker
> Container 기반 개발 환경을 위한 Docker Guide

### Index :
1. [__Container Environment__](#container_env)
2. [__What is Docker?__](#what_is_docker)
3. [__Docker Install & Base Command__](#install_docker_and_base_command)

# Container Environment <a name="container_env" />
> Docker를 알기 전에 Container 개발 환경에 대해서 먼저 공부한다.

__Host OS__ 위에서 Resource를 _Logical_ 하게 구분하여 마치 별도의 Server인 것처럼 사용할 수 있게 해주는 기술로, 물리적으로 구분을 하지는 않는다. 논리적으로 구분을 해두어서 쉽게 없앨 수 있고 가벼우며, 재생성이 용이하다. Container 기반의 개발 환경을 사용하는 이유는 다음과 같다.

- 여러 Application에서 사용하고 있는 Library 및 Middleware Version에 대한 Confliction을 피함
- 이식성과 확장성의 용이 : Dependency 없이 다른 환경에서 실행 가능하며, Container를 여러 개 실행해서 이중화도 가능
- 다양한 OS 환경 지원 : Windows <-> Linux

_Virtual Environment_ 와의 차이점

- __Virtual Tech(Virtual Box, VMWare...)__ 는 Host OS 위에 Virtual Software를 설치하고 그 곳에서 Virtual Env를 구축한다.
- Container와 다르게 __Guest OS__ 가 존재해서 _Overhead_ 가 크다. (OS 위에 OS를 올리는 것이기 때문이다.)
- Container(Docker, Containered, CRI-O...) 등은 __Container Runtime__ 을 기반으로 운영한다.
- Container는 Guest OS가 없고, Host OS의 _Kernel_ 을 공유하여 Overhead가 적고 가벼워서 빠르다.

![Alt Text][container_and_virtual]

### Linux Container

Linux 기반에서 필요한 Library와 Application을 모아서 별도의 Server처럼 구성하는 것을 말한다. 여기서 Container를 이루는 Network Config, Env Variable 등의 _System Resource_ 는 각 Contaiiner가 __독립적__ 으로 소유한다. Linux Container의 특징은 다음과 같다.

- __Process의 구획화__ : 특정 Container에서 작동하는 Process는 기본적으로 해당 Container 안에서만 Access 가능하며, 그 안에서 실행되는 Process는 다른 Container의 Process에게 영향을 주지 않는다.
- __Network의 구획화__ : 기본적으로 Container 하나에 IP 주소가 할당되어 있는데, 하나의 컴퓨터가 하나의 IP 주소를 갖는 것을 극복한다.
- __File System의 구획화__ : 해당 Container에서의 명령이나 File 등의 Access를 제한할 수 있다.

----------------------------------------------------

# What is Docker? <a name="what_is_docker" />

Docker는 _Container_ 기술을 기반으로 Application에 필요한 환경을 신속하게 구축, 테스트, 배포할 수 있게 도와주는 Platform이다. 한 가지 알아야할 것은 Docker가 Container 기술을 만든 것이 아니라, Docker는 Container 개발 환경을 사용하기 쉽게 만든 Platform인 것이다. __MSA__ (Micro Service Architecture) 환경에서 아주 유용하게 사용되는 기술로, 하나의 서비스에서 기능 단위로 Module화 되어있는 구조를 기본으로 한다.

Docker는 Linux Kernel의 _Namespace_ 를 사용하고 있기 때문에, Container 단위로 논리적인 공간을 갖게 된다는 것을 확인할 수 있다. 이를 통해 Host OS나 다른 Container와 같은 __PID__ 를 갖는 Process를 띄우거나, 같은 Port에 서비스를 띄우는 작업 등을 할 수 있다.

Docker의 Resrouce Management에 대해서는 결국 Host OS의 물리적인 Resource는 공유 받아야하는데, Linux Kernel의 ```cgroups``` 를 활용해서 __CPU, Memory, Network, I/O__ 등을 제어할 수 있다.

###### - cgroups : Process와 Thread를 그룹화해서 관리하기 위한 기능

### Docker Image

Container를 생성하는 Base가 되는 것이 __Image__ 인데, Container를 실행하는데 필요한 모든 것을 포함하고 있으며, 재사용이 가능하다. 또한, Dependency File을 Compile 한다거나, 다른 잡다한 것들을 설치할 필요가 없다. 단순하게 개발하고 있는 Application만 이미지화해서 배포하는 것이 아닌, Database 혹은 WEB/WAS처럼 Middleware로 사용되는 프로그램들, 다른 OS 환경을 실행하기 위한 Image들이 _Docker Image Repository_ 에 배포되어 있어서 이를 다운받아서 사용할 수 있다.

즉, 개발자가 Docker Image _Build_ 를 통해 _Repository_ 에 배포하게 되면, Test, Staging, Production 환경에서는 Docker만 설치하고, Application Image를 다운받아 실행 후 Test하면 끝난다. Repository는 __Docker Registry__ 를 직접 만들어서 관리하거나, __Docker Hub__ 에 등록해서 관리할 수 있다.

__Layer 및 Union File System__ 을 기반으로 여러 개의 Layer를 하나의 File System으로 사용할 수 있게 한다. Docker iamge는 여러 개의 __Read Only Layer__ 로 구성되고, File이 추가되거나 수정되면 새로운 Layer가 생성이 된다. 예를 들어 Ubuntu Image가 A, B, C로 구성이 되어있다면, Nginx는 Ubuntu Image 위에 올리고, Nginx 안에 Web Application이 있다면 Nginx가 구성된 Image 위에 Web App Source가 올라간다. 그래서 Web App Source가 수정되면 나머지는 그대로 두고 Source Layer만 다운로드를 하게 되는 구조이다.

![Alt Text][docker_layer]

------------------------------------

# Docker Install & Base Command <a name="install_docker_and_base_command" />
> Docker를 설치하고 기본적인 Image를 Build하고 Run하는 연습 및 Docker File 작성 Guide

Docker를 설치하고 Image를 Build하는 Test를 진행한다. __AWS EC2 Cloud__ 에 __RedHet Enterprise Linux__ 를 올리고 그 위에 설치한다. 다른 환경에 대해서는 추후에 Guide를 해보려고 한다.

- YUM Update 및 Package Installation

```shell
sudo yum repolist all
sudo yum update -y
```

- Docker Install : 사전에 Docker가 설치되어 있을 경우 이를 제거하고 다싯 설치한다.

```shell
# 사전에 설치되어 있는 Docker Package 제거
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

# Docker Repolist Base URL 추가
sudo yum-config-manager \
--add-repo \
https://download.docker.com/linux/rhel/docker-ce.repo

# 기존 Docker CE Stable Base URL 부분을 주석처리하고 새롭게 Base URL 추가한다.
sudo vi /etc/yum.repos.d/docker-ce.repo
# 해당 내용 추가
baseurl=https://download.docker.com/linux/centos/7/x86_64/stable

# Dokcer에 필요한 Package Install
sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/slirp4netns-0.4.3-4.el7_8.x86_64.rpm
sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/container-selinux-2.107-1.el7_6.noarch.rpm
sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/fuse3-libs-3.6.1-4.el7.x86_64.rpm
sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/fuse-overlayfs-0.7.2-6.el7_8.x86_64.rpm

# Docker Package Install
sudo yum install docker-ce docker-ce-cli containerd.io -y

# 일반사용자 Docker 사용을 위한 작업
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# Docker Start
sudo systemctl daemon-reload
sudo systemctl restart docker
sudo systemctl enable docker

# 성공적으로 설치되었다면, Docker Version 체크를 해주자
docker --version
```

## Docker 

[container_and_virtual]:https://imgur.com/ApjrMir.png
[docker_layer]:https://imgur.com/40RPTyl.png
