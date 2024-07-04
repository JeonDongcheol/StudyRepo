# Django Redis

> Redis Cache를 활용해 Data Loading을 더 빠르게 하기 위한 Django Redis

# Installation

## OS Env.

```bash
# CentOS 7 Env.
sudo yum install redis

# Checking Installation
redis-server --version

# Connect to Redis Server in Localhost
redis-cli
```

## Django Env.

### Install django-redis

```bash
# Install Django Redis
pip3 install django-redis
```

### Add Env Setting in setting.py

- Location : Redis Connection URL로, 보통 Redis Port는 6379로 설정
- Option : Redis 관련 설정 정보 담는 곳(Password, Client Class, Socket 정보…)

```bash
#...
CACHE = {
	"default": {
		"BACKEND": "django_redis.cache.RedisCache",
		# Connection Host Setup
		"LOCATION": "redis://127.0.0.1:6379",
		# Additional Setting
		"OPTION": {
			"CLIENT_CLASS": "django_redis.client.DefaultClient"
		}
	}
}
#...
```

# Usage

## Useful Method

- **cache.get(key, version)** : Redis Cache에서 Key를 기반으로 Data Import
    - key : Cache에서 가져오고 싶은 Data Key
    - version : Cache Version
- **cache.set(key, value, timeout, version)** : Redis Cache로 Key를 기반으로 한 Data Export
    - key : Export 할 Key
    - value : Export Data
    - timeout : Cache 보존 시간
    - version : Cache Version
- **cache.delete(key, version)** : Redis Cache에 있는 Data 삭제
    - key : Target Key
    - version : Target Version

## Sample Code

- AWS(Region ap-northeast-2 : Seoul) Instance 목록에서 GPU Resource 가져오는 Method

```bash
# Django Redis Cache Module Import
import django.core.cache import cache

# ...

# Hybrid 학습을 위한 AWS Instance 유형 긁어오는 Method
def get_aws_gpu_resources(region_name):
    list_aws_gpu_resource = [] # Return Value
    redis_key_aws_gpu_resource = "aws_gpu" # Redis에서 AWS GPU Resource 목록을 가져올 키

    # Redis에서 해당 Key에 대한 데이터 가져오기
    aws_gpu_resource_from_cache = cache.get(redis_key_aws_gpu_resource)

    # Redis에 데이터가 없는 경우 NoneType 반환
    if aws_gpu_resource_from_cache is None:
        # 설정한 Region에 따라서 Client 선언
        boto3_ec2_client = boto3.client('ec2', region_name=region_name)
        describe_args = {}
        while True:
            # Resource Instance Type 가져오기
            instance_types = boto3_ec2_client.describe_instance_types(**describe_args)

            for instance_type in instance_types["InstanceTypes"]:
                # GPU Resource가 설정된 인스턴스
                if instance_type.get("GpuInfo") != None:
                    # GPU Info 가져오기
                    instance_gpu_info = instance_type.get("GpuInfo").get("Gpus")[0]
                    # GPU List에 추가되어 있지 않은 GPU Resource의 경우 새롭게 추가
                    gpu_name = instance_gpu_info.get("Manufacturer") + "-" + instance_gpu_info.get("Name")
                    if gpu_name not in aws_instances:
                        aws_instances.append(gpu_name)

            # Next Token이 없다면 while 반복문 종료
            if 'NextToken' not in instance_types:
                break
            # Next Token 값을 describe args로 담아냄
            describe_args['NextToken'] = instance_types['NextToken']

        # Cache에 AWS GPU Resource Data input, Expired date : 1 day
        cache.set(redis_key_aws_gpu_resource, aws_instances, 60*60*24)
    else:
        aws_instances = aws_gpu_resource_from_cache

    return aws_instances
```

## Result

- Before using Redis : 0.8760sec
- After applying Redis : 0.0007sec

![redis_test_result.png](img/redis_test_result.png)

### Note.

- Redis와 Django 사이 Key 저장 방식 (Default)

→ Django에서 Redis로 Cache를 저장할 때 Key는 기본적으로 :${VERSION}:${KEY} 형식으로 이루어지는데, Version을 지정해주지 않으면 기본적으로 1 로 설정되므로 :1:sample_key 형태로 key가 구성

→ 따라서, redis-cli를 통해 django에서 설정한 key로 조회를 하고 싶다면 해당 Key로 Get

- Django Redis 사용 기반 Connection 과정에서 dump.rdb 생성

---

# Kubernetes + Redis + Django

> Kubernetes Cluster 내부에 Redis Pod(Deployment)를 배포하고 이를 Django Backend Pod와 Connection하여 사용하는 Guide
> 

## Redis in Kubernetes

### YAML 구성

1. Redis 환경 구성을 위한 Configmap
2. Redis Pod를 생성하기 위한 Deployment
3. Redis Pod를 NodePort로 Expose하기 위한 Service

### Configmap

- Configmap YAML Sample
    
    ```yaml
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: redis-config
      namespace: mlops-dev
    data:
      # Deployment에서 해당 Configmap을 Import
      # Redis의 각종 Config 내용을 담고 있음
      redis-config: |
        maxmemory-policy allkeys-lru
        requirepass password123!
        port 6380
    ```
    
- Configmap Data
    - maxmemory : 메모리 사용 제한을 위한 설정 (Default : 0 - 메모리 사용량 제한 없음)
    - maxmemory-policy : Redis Server의 Memory가 가득 찼을 때의 정책
        - noeviction(Default) : Memory에 데이터가 가득 차면 새로운 Key를 저장하지 않는데, 새로운 Data Input 불가능해서 에러 발생
        - volatile-lru : lru 알고리즘 방식으로 Expire 설정된 Key 중에서 가장 오래 사용하지 않은 Key를 삭제하는데, Memory가 가득 차고, Expire 설정이 되지 않은 Key만 남으면 새로운 Data Input이 불가능한 에러가 발생
        - allkey-lru : 모든 Key 중에서 가장 오래 사용하지 않았던 Key를 삭제 (Most Recommanded)
    - requirepass : Redis Server 비밀번호
    - port : Redis Server Port (Default : 6379) 설정

### Deployment

- Deployment YAML Sample
    
    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      labels:
        name: redis-server
      name: redis-server
      namespace: mlops-dev
    spec:
      replicas: 1
      selector:
        matchLabels:
          name: redis-server
      template:
        metadata:
          labels:
            name: redis-server
        spec:
          containers:
          - name: redis
            image: redis
            env:
            - name: MASTER
              value: "true"
            # Redis Configuration Import를 위한 Command 설정
            command:
            - redis-server
            - "/redis/redis.conf"
            ports:
            - containerPort: 6380
              name: redis-port
            # Redis Data & Configuration Data Volume Mount
            volumeMounts:
            - mountPath: /redis-master-data
              name: data
            - mountPath: /redis
              name: config
          volumes:
          - name: data
            emptyDir: {}
          # Redis ConfigMap Import
          - name: config
            configMap:
              name: redis-config
              items:
              - key: redis-config
                path: redis.conf
    ```
    
- Deployment 배포 후 Pod 내부 접속 확인

```bash
# Pod Name 가져오기
kubectl get pod -n mlops-dev | grep redis-server
# Pod 내부 접속
kubectl exec --stdin --tty -n mlops-dev redis-server-58b57f96b4-b2qmt -- /bin/bash

# Redis CLI 접속
redis-cli -p 6380 -a megazone00!
# ConfigMap에 담은 설정 값 확인
127.0.0.1:6380> CONFIG GET maxmemory-policy
```

- 결과 화면 (정상적으로 설정된 것 확인)

![redis_in_k8s_result.png](img/redis_in_k8s_result.png)

### Service

- Service YAML Sample
    
    ```bash
    # Deployment를 Service로 Expose
    kubectl expose deploy -n mlops-dev redis-server
    # ClusterIP로 설정되어 있던 Service를 NodePort로 수정
    kubectl edit svc -n mlops-dev redis-server
    ```
    
    ```yaml
    # Django Backend에서 사용하기 위해 Node Port로 Service Type을 수정
    apiVersion: v1
    kind: Service
    metadata:
      creationTimestamp: "2023-03-23T04:57:52Z"
      labels:
        name: redis-server
      name: redis-server
      namespace: mlops-dev
      resourceVersion: "224518245"
      uid: 2d138f5d-66a6-420a-9daf-d96df54fa9a5
    spec:
      clusterIP: 10.110.110.40
      clusterIPs:
      - 10.110.110.40
      externalTrafficPolicy: Cluster
      ipFamilies:
      - IPv4
      ipFamilyPolicy: SingleStack
      # 해당 부분 수정
      ports:
      - nodePort: 31791
        port: 6380
        protocol: TCP
        targetPort: 6380
      selector:
        name: redis-server
      sessionAffinity: None
      # Type을 ClusterIP에서 NodePort로 수정
      type: NodePort
    status:
      loadBalancer: {}
    ```
    

## Django Redis Setting

> Redis Pod와 Django Backend Pod 간의 통신을 위한 설정과 테스트 진행. 초기 부분과 동일한 Sample Code 사용
> 

### settings.py 설정

```python
# ...
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        # 현재 Redis Server Info
        "LOCATION": "redis://default:password123!@172.16.186.186:31791/0",
        "OPTION": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}
# ...
```

### Test 결과

- Redis에서 데이터를 가져오지 않고 AWS GPU Resource 가져온 결과 : 1.0534 sec
- Redis에서 Caching한 데이터를 가져온 결과 : 0.0009 sec

![redis_in_k8s_test_result](img/redis_in_k8s_test_result.png)

## Reference.

- [Django Redis Github](https://github.com/jazzband/django-redis)
- [Django Redis 사용법](https://king-minwook.tistory.com/83)
- [Redis RDB 개념](https://mozi.tistory.com/371)
- [Redis ACL 참조](https://velog.io/@inhwa1025/Redis-ACL-%EC%9D%B4%EB%9E%80-ACL-%EC%82%AC%EC%9A%A9-%EB%B0%A9%EB%B2%95)
- [Kubernetes ConfigMap을 사용한 Redis 설정](https://kubernetes.io/ko/docs/tutorials/configuration/configure-redis-using-configmap/)
