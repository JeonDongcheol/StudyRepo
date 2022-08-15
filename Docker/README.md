# Docker
> Container 기반 개발 환경을 위한 Docker Guide

### Index :
1. [__Container Environment__](#container_env)
2. [__Model Serving Using PVC__](#model_serving_pvc)
3. [__KServe Dex Authentication__](#dex_auth)

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

[!Alt Text](container_and_virtual)

### Linux Container

Linux 기반에서 필요한 Library와 Application을 모아서 별도의 Server처럼 구성하는 것을 말한다. 여기서 Container를 이루는 Network Config, Env Variable 등의 _System Resource_ 는 각 Contaiiner가 __독립적__ 으로 소유한다. Linux Container의 특징은 다음과 같다.

- __Process의 구획화__ : 특정 Container에서 작동하는 Process는 기본적으로 해당 Container 안에서만 Access 가능하며, 그 안에서 실행되는 Process는 다른 Container의 Process에게 영향을 주지 않는다.
- __Network의 구획화__ : 기본적으로 Container 하나에 IP 주소가 할당되어 있는데, 하나의 컴퓨터가 하나의 IP 주소를 갖는 것을 극복한다.
- __File System의 구획화__ : 해당 Container에서의 명령이나 File 등의 Access를 제한할 수 있다.


[container_and_virtual]:https://imgur.com/ApjrMir.png
