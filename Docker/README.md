# Docker
> Container 기반 개발 환경을 위한 Docker Guide

### Index :
1. [__Container Environment__](#container_env)
2. [__What is Docker?__](#what_is_docker)
3. [__Docker Install & Base Command__](#install_docker)
4. [__Dockerfile__](#dockerfile)
5. [__Docker Image Push & Pull__](#docker_push_pull)

# 1. Container Environment <a name="container_env" />
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

# 2. What is Docker? <a name="what_is_docker" />

Docker는 _Container_ 기술을 기반으로 Application에 필요한 환경을 신속하게 구축, 테스트, 배포할 수 있게 도와주는 Platform이다. 한 가지 알아야할 것은 Docker가 Container 기술을 만든 것이 아니라, Docker는 Container 개발 환경을 사용하기 쉽게 만든 Platform인 것이다. __MSA__ (Micro Service Architecture) 환경에서 아주 유용하게 사용되는 기술로, 하나의 서비스에서 기능 단위로 Module화 되어있는 구조를 기본으로 한다.

Docker는 Linux Kernel의 _Namespace_ 를 사용하고 있기 때문에, Container 단위로 논리적인 공간을 갖게 된다는 것을 확인할 수 있다. 이를 통해 Host OS나 다른 Container와 같은 __PID(Process ID)__ 를 갖는 Process를 띄우거나, 같은 Port에 서비스를 띄우는 작업 등을 할 수 있다.

Docker의 Resrouce Management에 대해서는 결국 Host OS의 물리적인 Resource는 공유 받아야하는데, Linux Kernel의 ```cgroups``` 를 활용해서 __CPU, Memory, Network, I/O__ 등을 제어할 수 있다.

###### - cgroups : Process와 Thread를 그룹화해서 관리하기 위한 기능

### Docker Image

Container를 생성하는 Base가 되는 것이 __Image__ 인데, Container를 실행하는데 필요한 모든 것을 포함하고 있으며, 재사용이 가능하다. 또한, Dependency File을 Compile 한다거나, 다른 잡다한 것들을 설치할 필요가 없다. 단순하게 개발하고 있는 Application만 이미지화해서 배포하는 것이 아닌, Database 혹은 WEB/WAS처럼 Middleware로 사용되는 프로그램들, 다른 OS 환경을 실행하기 위한 Image들이 _Docker Image Repository_ 에 배포되어 있어서 이를 다운받아서 사용할 수 있다.

즉, 개발자가 Docker Image _Build_ 를 통해 _Repository_ 에 배포하게 되면, Test, Staging, Production 환경에서는 Docker만 설치하고, Application Image를 다운받아 실행 후 Test하면 끝난다. Repository는 __Docker Registry__ 를 직접 만들어서 관리하거나, __Docker Hub__ 에 등록해서 관리할 수 있다.

__Layer 및 Union File System__ 을 기반으로 여러 개의 Layer를 하나의 File System으로 사용할 수 있게 한다. Docker iamge는 여러 개의 __Read Only Layer__ 로 구성되고, File이 추가되거나 수정되면 새로운 Layer가 생성이 된다. 예를 들어 Ubuntu Image가 A, B, C로 구성이 되어있다면, Nginx는 Ubuntu Image 위에 올리고, Nginx 안에 Web Application이 있다면 Nginx가 구성된 Image 위에 Web App Source가 올라간다. 그래서 Web App Source가 수정되면 나머지는 그대로 두고 Source Layer만 다운로드를 하게 되는 구조이다.

![Alt Text][docker_layer]

------------------------------------

# 3. Docker Install <a name="install_docker" />

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

----------------------------

# 4. Dockerfile <a name="dockerfile" />
> Dockerfile 작성 안내

Dockerfile이란 Docker에서 이용하는 _Image_ 를 기반으로 하여 새로운 Image를 Script File을 통해 나만의 Image를 생성할 수 있는 Image Configuration File이다. Dockerfile을 통해서 기존 Image를 이용했을 때 필요한 사전 설정 및 준비들을 미리 할 수 있어서 Docker Image를 더욱 쉽게 올릴 수 있다.

Dockerfile은 Dockerfile이 있는 Directory를 _Context_ 로 인식하여 작업을 진행하기 때문에, 작성 및 Build까지 새로운 Directory를 만들어서 해당 Directory 내부에서 작업하는 것을 구너장한다. Dockerfile은 따로 확장자 없이 그냥 Naming만으로 생성하는데, 주로 평범하게 Dockerfile이라고 파일을 만든다.

Dockerfile 내부에서 사용되는 명령어는 다음과 같다.

<details>
  <summary>Dockerfile Command 정리</summary>
  <div markdown="1">
  1. <b>FROM</b> : Docker Image를 생성할 때 필요한 Base Image로, 뼈대가 되는 부분이다. 주로 OS 혹은 Code Language 를 설정해준다.
  </div>
  <div markdown="2">
  2. <b>WORKDIR</b> : Shell Script의 'cd' 명령어처럼 Container 상에서 작업 Directory로 전환을 해주는 명령어이다.
  </div>
  <div markdown="3">
  3. <b>RUN</b> : Shell Script를 사용할 수 있도록 해주는 부분으로, Image Build 과정에서 필요한 Command를 실행하기 위해 사용된다.
  </div>
  <div markdown="4">
  4. <b>CMD</b> : 해당 Image를 Container로 띄울 때 Default로 실행시킬 Command 혹은 ENTRYPOINT로 지정된 Command에 Default로 넘길 Parameter를 지정할 때 사용한다.
  </div>  <div markdown="5">
  5. <b>ENTRYPOINT</b> : Image를 Container로 띄울 때 항상 실행되어야 하는 Command를 지정한다. Docker Image를 마치 하나의 실행 파일처럼 사용할 때 유용하다.
  </div>  <div markdown="6">
  6. <b>EXPOSE</b> : Network 상에서 Container로 들어오는 Traffic을 Listening 하는 Port와 Protocol을 지정하기 위해서 사용한다.
  </div>
  <div markdown="7">
  7. <b>COPY</b> : Host PC의 Directory 혹은 File을 Docker Image의 File System으로 복사하기 위해 사용한다. 절대 & 상대 경로를 모두 지원한다.
  </div>
  <div markdown="8">
  8. <b>ADD</b> : COPY 명령어의 상위 호환 명령어로, Network 상의 File도 사용할 수 있는 명령어인데, 왠만하면 COPY를 쓴다.
  </div>
    <div markdown="9">
  9. <b>ENV</b> : 환경 변수를 설정하기 위해 사용하는 명령어로, ENV로 설정된 환경 변수는 Image Build 외에도 해당 Container에서 실행 중인 Application도 접근할 수 있다.
  </div>
    <div markdown="10">
  10. <b>ARG</b> : Image Build 과정에서 '--build-arg' Option을 통해 넘길 수 있는 인자를 정의하기 위해 사용한다. Default 값도 지정해줄 수 있다.
  </div>
    <div markdown="11">
  11. <b>MAINTAINER</b> : 해당 Image의 생성, 유지 보수 등의 관리자를 명시하는 부분인데, 추후에 보충할 예정이다.
  </div>
</details>

##### RUN vs CMD vs ENTRYPOINT

```RUN``` 은 새로운 _Layer_ 를 생성하거나, 생성된 _Layer_ 위에서 _Command_ 를 실행한다.

```CMD``` 는 Docker Container가 실행될 때 실행되는 명령어로, 사용자가 ```docker run``` 을 할 때 따로 명령어를 적어주면 CMD는 실행되지 않는다.

```ENTRYPOINT``` 는 ```docker run``` 으로 생성하거나, ```docker start``` 로 중지된 container를 시작할 때 실행되는 명령어로 __CMD__ 와 동일한 역할을 수행하지만, Dockerfile 내에서 __1번__ 만 정의 가능하며, ```docker run``` 으로 container를 실행할 때 Command를 직접 입력하면 이를 ENTRYPOINT의 파라미터로 인식한다.

### 간단한 Dockerfile
> Django Server를 Dockerfile을 통해 Image를 Build 하는 과정에서 작성한 Docker File이다. 참고만 하자.

```dockerfile
# Python 가상 환경 3.6.8에서 실행
FROM python:3.6.8

# PyPi Upgrade
RUN pip install --upgrade pip

# Server 경로 이동하고 Project를 복사
WORKDIR /usr/src/app
COPY . .

# PyPi Requirements Install
RUN pip3 install -r requirements.txt

# Kubernetes 환경을 위한 Config Setting 작업
RUN mkdir $HOME/.kube
RUN mv config $HOME/.kube

# Manage.py를 실행하기 위해 작업 디렉토리 이동
WORKDIR ./mlopsapi

# Run Server : --settings 부분은 생략함
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000", "--settings=..."]

# Docker 8000 Port Open
EXPOSE 8000
```

### 해당 Dockerfile을 통해 Server를 실행시키는 과정

- Build Dockerfile : Dockerfile을 <USER_NAME>/<IMAGE_NAME>:<TAG> 형태로 Build 한다.

```shell
docker build --tag <USER_NAME>/<IMAGE_NAME>:<TAG> .
```
  
결과 :

![Alt Text][docker_build]
  
- Run Docker Image : Build했던 Image 정보인 <USER_NAME>/<IMAGE_NAME>:<TAG> 를 불러와서 Run을 수행하고, 정상적으로 Server가 동작하는지 Log를 본다.

```shell
# Docker Run
docker run -d -p 8000:8000 <USER_NAME>/<IMAGE_NAME>:<TAG>
  
# Log 조회
docker logs <Image_ID>
```

----------------

# 5. Docker Image Push & Pull <a name="docker_push_pull" />
> 원격에서 Docker Image를 Pull & Push 하는 작업에 대해서 정리한다.

Docker를 사용하면서 Image를 __Docker Hub__ 뿐만 아니라, 다른 Registry에서도 Image를 가져올 때가 있다. 그 때를 대비해서 어떻게 Image를 가져오고, 또 다른 _Private Registry_ 로 어떻게 보내는지를 대략 정리해본다.

Docker Image를 가져오는 Command는 ```docker pull ${IMAGE}:${TAG}``` 를 사용한다. 기본적으로 Registry에서 Image Pulling을 할 때 Default는 [Docker Hub](https://hub.docker.com/)로 지정되는데, 이 때는 별도의 Docker Hub에 대한 지정을 하지 않고 Image 이름 및 태그를 지정해주면 된다. Docker Hub에서 Pulling을 하게 되면 다음과 같이 Image를 다운받고 올라간다.

![Alt Text][docker_pull_from_docker_hub]

Local Registry의 Docker Image는 ```docker images``` 혹은 ```docker image ls``` 로 조회할 수 있다. 위의 이미지와 같이 Docker Image가 정상적으로 올라간 것을 확인할 수 있다.
  
반대로 _Local_ 에서 작업을 해서 만든 Docker Image를 _Remote_ 로 __Push__ 하고 싶을 때가 있다. Docker Hub의 _Public/Private Registry_ 가 될 수도 있고, 다른 _Registry_ 가 될 수도 있다. 여기서는 다른 Registry로 Image를 Push하는 방법에 대해서 안내한다.

Docker Image를 Push하는 Command는 ```docker push ${IMAGE}:${TAG}``` 를 사용하는데, 이전에 먼저 어디로 Push할 것인지에 대한 __Target__ 을 지정해주어야 한다. ```docker tag ${IMAGE}:${TAG} ${TARGET_URL}/${IMAGE}:${TAG}``` Command를 수행하게 되면, Docker Image를 Push하기 위한 Image가 따로 만들어진다. ```Tag``` 명령어를 통해 Image를 만들어주면 해당 조합을 통해 생성된 Image를 볼 수 있으며, 이를 Push 해주면 된다. 정상적으로 Push가 되면 다음과 같은 화면이 나온다. (많은 것들이 가려져 있긴하다.)
  
![Alt Text][docker_push_to_private_reg]
  
Docker Image를 Registry에 올리고 나면 Local의 Image는 필요가 없어지는데, 이는 Image 삭제를 통해 정리해주면 된다. 만약 Image를 사용하는 Local Container가 있다면, 정상적으로 삭제가 되지 않으니, 이를 먼저 제거해주고 작업해주면 된다.
  
```shell
docker rmi ${IMAGE}:${TAG}
```

![Alt Text][docker_image_remove]
  
[container_and_virtual]:https://imgur.com/ApjrMir.png
[docker_layer]:https://imgur.com/40RPTyl.png
[docker_build]:https://imgur.com/0fH7P3E.png
[docker_pull_from_docker_hub]:https://imgur.com/DC5n9u5.png
[docker_push_to_private_reg]:https://imgur.com/eJ3KWFQ.png
[docker_image_remove]:https://imgur.com/HvM8muL.png
