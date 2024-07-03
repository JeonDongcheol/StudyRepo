# CNI

> Kubernetes를 이해하는 것에 있어서 중요한 CNI에 대한 Reference
> 

**CNI(Container Network Interface)** : 컨테이너 간 네트워킹을 제어할 수 있는 플러그인을 만들기 위한 표준

→ 컨테이너 런타임을 포함하고 있는 Kubernetes도 이미 Network Interface로 **kubenet**이라는 CNI 존재

---

[Whereabouts](https://www.notion.so/Whereabouts-3f3c855dc1574da9bd264017e9ee51e6?pvs=21)

[Multus CNI](https://www.notion.so/Multus-CNI-088dce62685c41ad98fdb570be0dd574?pvs=21)

# 배경

컨테이너 발전의 가속화

→ 컨테이너 런타임과 오케스트레이터 사이의 **네트워크 계층**을 구현하는 방식의 다양화

→ 다양화로 인한 복잡성을 피하기 위한 공통된 인터페이스 필요성의 부각

- **오케스트레이션(Container Orchestration)** : 컨테이터 배포, 관리, 확장 등등의 자동화를 위한 체계
    
    → Kubernetes는 컨테이너 오케스트레이션 툴 중에 하나 (Docker 기반)
    

---

# 3rd Party Plugin

> 특정 서비스에 맞는 기능 구현을 위한 CNI 기반 추가 기능 개발 및 서비스 적용을 위한 3rd party plugin
> 

## 3rd Party Plugin의 종류

- **Calico** (중요)
- **Multus** (중요)
- Weave
- Cilium

## 왜 3rd Party Plugin을 사용할까?

1. 다양한 기능 제공 (Network Policy, Public Cloud와의 통합, 대규모 트래픽 안정성)
2. kubenet 기능 부족 : 컨테이너 간의 노드 간 교차 네트워킹조차 지원하지 않음

## CNI Plugin Network Model

Container 및 Node 간 통신을 중개할 때 사용하는 **Network Model**을 어떤 것을 사용하는지에 따라 분류

- CNI Plugin이 사용하는 Network Model
    1. **Overlay Network Model** : VXLAN(Virtual Extensible LAN) 혹은 IP-in-IP Protocol 사용
    2. **Non-overlay Network Model** : BGP(Border Gateway Protocol)을 사용

### 1. Overlay Network Model

실제로는 복잡할 수도 있는 **Endpoint 간의 Network 구조를 추상화**하여 **Network 통신 경로를 단순화**하는 것

**3계층 이상**으로 구축된 네트워크 간에 있는 Endpoint의 Node 간의 통신이 일어날 때 패킷을 한겹 **캡슐화(Encapsulation)**한 뒤 통신시켜서, **2계층(같은 LAN)에서 통신이 일어나는 것처럼 통신**할 수 있도록 함

![Untitled](CNI%2083416d835a3f46489399276f3e80eb63/Untitled.png)

**Calico** 기준으로 2가지 방식의 Overlay Network 지원

1. VXLAN Protocol : 성능이 좀 더 떨어지지만 범용성이 있어서 기본적으로 사용되는 방식
2. IP-in-IP Protocol

Overlay Network Model 특징

- 기존 Network 환경에 영향 없이 CNI 환경 구성 가능
- BGP Protocol 대비 캡슐화 과정에서 컴퓨팅 자원 소모, 패킷 당 송/수신 데이터의 양이 감소

### Non-overlay Network Model

통신이 발생하는 Node 간에 BGP를 사용하는 Software Router 구현을 통해 최적의 경로 정보를 현재 Endpoint들의 상태를 따라서 동적으로 감지하여 적용할 수 있다는 전제를 통해 구현

![Untitled](CNI%2083416d835a3f46489399276f3e80eb63/Untitled%201.png)

BGP(Border Gateway Protocol) 을 사용한 CNI 구성의 특징

- HA(고가용성, High Availability)를 위해 Cluster 구성 Node들 간의 Subnet이 다르게 구성되어 있는 경우 상위의 Physical Router에도 별도의 설정이 필요
- 통신이 가능한 대역에서 여러 Cluster를  활용하거나 별도의 외부 서비스들을 운영하는 경우 Network 대역이 겹치지 않아야 함
- Public Cloud 환경에서의 구성이 자유롭지 않음
- 별도의 패킷 가상화 없이 기존 네트워크에서 사용하던 직관적인 Routing 방식을 이용
- Cluster 외부에서도 Ingress나 Service의 도움 없이 Pod 접근 가능
- 통일화 된 보안 설정 및 디버깅/로깅의 용이성
- Overlay Network 대비 좋은 성능

### Overlay Network vs BGP(Non-overlay)

BGP Network Model

- 빠르고 안정적인 성능 (패킷의 캡슐/복호화 과정에서 발생하는 Overhead가 없기 때문)
- Node 간 Subnet이 다를 경우 Physical Router 장비의 설정을 변경해야 함 - 높은 환경 의존성
    - Public Cloud 환경에서 치명적인 단점

---

# CNI Configuration

> Multus Github의 CNI Configuration 설명 기반
> 
- CNI Configuration Sample

```json
{
  "cniVersion": "0.3.0",
  "type": "loopback",
  "additional": "information"
}
```

- CNI Configuration 구성 요소(지속적인 Update 필요)
    - **cniVersion** : 사용하는 CNI Plugin의 버전 정보
    - **type** : Disk에서 부를 CNI Plugin Binary, **/opt/cni/bin**에 위치
    - **additional** : CNI Plugin에 따라 구성하는 Configuration Parameter로, Type에 따라 다양함
        - additional이라는 필드가 존재하는 것이 아니라, 추가적인 필드가 들어온다는 의미
- CNI Configuration Examples
    - Example 1. 00-multus.conf
        
        ```json
        {
          "cniVersion": "0.3.1",
          "name": "multus-cni-network",
          "type": "multus",
          "capabilities": {
            "portMappings": true,
            "bandwidth": true
          },
          "kubeconfig": "/etc/cni/net.d/multus.d/multus.kubeconfig",
          "delegates": [
            {
              "name": "k8s-pod-network",
              "cniVersion": "0.3.1",
              "plugins": [
                {
                  "type": "calico",
                  "log_level": "info",
                  "log_file_path": "/var/log/calico/cni/cni.log",
                  "datastore_type": "kubernetes",
                  "nodename": "master1",
                  "mtu": 0,
                  "ipam": {
                    "type": "calico-ipam"
                  },
                  "policy": {
                    "type": "k8s"
                  },
                  "kubernetes": {
                    "kubeconfig": "/etc/cni/net.d/calico-kubeconfig"
                  }
                },
                {
                  "type": "portmap",
                  "snat": true,
                  "capabilities": {
                    "portMappings": true
                  }
                },
                {
                  "type": "bandwidth",
                  "capabilities": {
                    "bandwidth": true
                  }
                }
              ]
            }
          ]
        }
        ```
        
    - Example 2. 10-calico.conflist
        
        ```json
        {
          "name": "k8s-pod-network",
          "cniVersion": "0.3.1",
          "plugins": [
            {
              "type": "calico",
              "log_level": "info",
              "log_file_path": "/var/log/calico/cni/cni.log",
              "datastore_type": "kubernetes",
              "nodename": "master1",
              "mtu": 0,
              "ipam": {
                  "type": "calico-ipam"
              },
              "policy": {
                  "type": "k8s"
              },
              "kubernetes": {
                  "kubeconfig": "/etc/cni/net.d/calico-kubeconfig"
              }
            },
            {
              "type": "portmap",
              "snat": true,
              "capabilities": {"portMappings": true}
            },
            {
              "type": "bandwidth",
              "capabilities": {"bandwidth": true}
            }
          ]
        }
        ```
        

CNI Configuration이 변경되어도 kubelet restart 하지 않아도 된다. (Pod에 반영되어 자동으로 restart)

---

### Reference

- [CNI Documents](https://www.cni.dev/docs/)
- [CNI 개념](https://tommypagy.tistory.com/390)
- [CNI Plugin Configuration](https://github.com/containernetworking/plugins)
