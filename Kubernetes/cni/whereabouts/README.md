# Whereabouts

> Kubernetes 3rd Party CNI Plugin 중 하나인 whereabouts에 대한 설명

Whereabouts : IPAM CNI Plugin을 통한 Network Interface Dynamic Allocation

Whereabouts CNI Plugin을 사용하면 DHCP Server를 사용하지 않고도 IP 주소를 할당 받을 수 있음

# IPAM

- IPAM(IP Address Management) : IP 주소를 Kubernetes Cluster 전체에 할당하는 CNI Plugin
    - host-local : 동일한 Node의 Pod에 IP를 할당할 때 사용
    - whereabouts : Cluster 모든 Node에서 작동시키기 위해 사용

# Installation

## 1. Install by Daemonset

- Git clone

```bash
# Git Clone 후 directory로 이동
git clone https://github.com/k8snetworkplumbingwg/whereabouts
cd whereabouts/doc/crds
```

- Apply to Kubernetes

```bash
# Apply to Kubernetes
kubectl apply \
    -f daemonset-install.yaml \
    -f whereabouts.cni.cncf.io_ippools.yaml \
    -f whereabouts.cni.cncf.io_overlappingrangeipreservations.yaml
```

## 2. Install by Helm-chart(Helm version 3)

- Git clone

```bash
# Git Clone
git clone https://github.com/k8snetworkplumbingwg/helm-charts.git
```

- helm install

```bash
# Install using Helm-Chart
cd helm-charts
# Helm Upgrade & Install Whereabouts
helm upgrade --install whereabouts ./whereabouts --namespace kube-system
```

- Confirm

```bash
# Kubernetes에 Whereabouts CNI Pod Node 단위로 배포된 것 확인
kubectl get pod -n kube-system | grep whereabouts

# Root 권한으로 이동 후 net.d에 whereabouts config directory(whereabouts.d) 확인
sudo su
cd /etc/cni/net.d
ls -l
```

## 3. Whereabouts Format

| Field | Format | Example |
| --- | --- | --- |
| type | String | whereabouts |
| range | String | 192.0.2.192/27 |
| exclude | Array | [”192.0.2.192/30”, “192.0.2.196/32”] |
1. type : IPAM의 Address 유형 : whereabouts
2. range : CIDR 표기범의 IP Address 및 범위로, IP Address는 해당 주소 범위 내에서 할당
3. exclude[Optional] : CIDR 표기법으로 0개 이상의 IP Address 및 범위로, 제외된 IP Address 범위 내의 IP 주소는 할당되지 않음

---

## Reference

- [[Github] Whereabouts CNI](https://github.com/k8snetworkplumbingwg/whereabouts)
- [[Redhat] Whereabouts CNI를 활용한 Dynamic IP Address 구성](https://access.redhat.com/documentation/ko-kr/openshift_container_platform/4.6/html/networking/nw-multus-whereabouts_configuring-additional-network)
