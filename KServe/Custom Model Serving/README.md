# Custom Model Serving

> KServe에서 Custom Model Serving을 하는 방법 기술

### 1. ConfigMap 설정
    
Custom Model Server를 만들기 위한 선행 작업으로 **Init Container,** **Persistent Volume Claim** 관련 스펙 정의를 허용하도록 설정

**knative-serving** 네임스페이스의 **config-features** 라는 ConfigMap 안에 해당 설정 가능

```bash
kubectl edit configmap -n knative-serving config-features
```

```yaml
apiVersion: v1
data:
  # Example
  # ...
  kubernetes.podspec-init-containers: enabled # Allow definition about init container
  kubernetes.podspec-persistent-volume-claim: enabled # Allow definition about PVC
  kubernetes.podspec-persistent-volume-write: enabled # Allow definition about PVC Write (Default: Read Only)
  kubernetes.podspec-tolerations: enabled
  # ...
```
    
### 2. Cluster Serving Runtime 설정
    
KServe의 Inference Service를 정의할 때 **Cluster Serving Runtime** CRD를 통해 미리 Model Serving 이미지의 **Spec, Command, env, Resource** 등을 미리 정의할 수 있음

- lightllm_qwen_vl_clusterservingruntime.yaml
    
    ```yaml
    apiVersion: serving.kserve.io/v1alpha1
    kind: ClusterServingRuntime
    metadata:
      name: kserve-lightllm-qwen-vl
    spec:
      annotations:
        prometheus.kserve.io/path: /metrics
        prometheus.kserve.io/port: "8080"
      containers:
      # Way to serve model by LightLLM
      - args:
        - --model_dir
        - /mnt/models
        - --host
        - 0.0.0.0
        - --port
        - "8080"
        - --tp
        - "4"
        - --enable_multimodal
        - --cache_capacity
        - "1000"
        - --max_total_token_num
        - "12000"
        - --trust_remote_code
        command:
        - python
        - -m
        - lightllm.server.api_server
        image: {IMAGE_URL}/{IMAGE_NAME}:{TAG}
        name: kserve-container
        # Default Resource Spec
        resources:
          limits:
            cpu: "10"
            memory: 100Gi
            nvidia.com/gpu: 4
          requests:
            cpu: "10"
            memory: 100Gi
            nvidia.com/gpu: 4
        # Default Volume
        volumeMounts:
        - mountPath: /dev/shm
          name: shmdir
      supportedModelFormats:
      - autoSelect: true
        name: lightllm-qwen-vl
        version: "3"
      # Default Volume
      volumes:
      - emptyDir:
          medium: Memory
          sizeLimit: 5Gi
        name: shmdir
    ```
        
### 3. Inference Service 생성
    
앞서 생성한 리소스를 기반으로 Custom Inference Service 생성

- custom_isvc.yaml **(S3 Base)**
    
    Custom Volume을 Mount하는 경우 **volumeMounts** 에 model path에 대해 반드시 해당 부분을 정의해주어야 함
    
    ```yaml
    apiVersion: serving.kserve.io/v1beta1
    kind: InferenceService
    metadata:
      annotations:
        prometheus.io/path: /metrics
        prometheus.io/port: "8082"
        prometheus.io/scrape: "true"
      name: {NAME}
      namespace: {NAMESPACE}
    spec:
      predictor:
        model:
          modelFormat:
            name: {CLUSTER_SERVING_RUNTIME_MODEL_TYPE}
          storageUri: {STORAGE_URI} # S3, GCS, PVC...
          volumeMounts:
          - name: kserve-provision-location
            mountPath: /mnt/models
        initContainers:
        - name: storage-initializer
          image: kserve/storage-initializer:v0.10.0
          args:
          - {STORAGE_URI}
          - /mnt/models
          env:
          - name: AWS_ACCESS_KEY_ID
            valueFrom:
              secretKeyRef:
                key: AWS_ACCESS_KEY_ID
                name: {AWS_SECRET_NAME}
          - name: AWS_SECRET_ACCESS_KEY
            valueFrom:
              secretKeyRef:
                key: AWS_SECRET_ACCESS_KEY
                name: {AWS_SECRET_NAME}
          - name: awsAnonymousCredential
            value: "false"
          - name: AWS_DEFAULT_REGION
            value: {AWS_REGION}
          volumeMounts:
          - mountPath: /mnt/models
            name: kserve-provision-location
        # Set Toleration
        tolerations:
        - effect: NoSchedule
          key: llm
          operator: Equal
          value: "true"
        volumes:
        - name: kserve-provision-location
          persistentVolumeClaim:
            claimName: {PVC_NAME}
    ```
    

    ```bash
    kubectl apply -f custom_isvc.yaml
    ```
