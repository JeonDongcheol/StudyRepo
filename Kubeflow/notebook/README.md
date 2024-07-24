# Notebook

> Kubeflow Notebook 기반의 작업을 위한 페이지

## Intro

Kubeflow에서 Notebook을 생성하면 기본적으로 **jovyan** 이라는 사용자가 생성 ( **UID 1000** )

Image를 기반으로 Notebook을 생성할 때 Home Directory를 구성하기 위해 다음과 같이 작업

- Image의 **/tmp_home** 경로에 임시로 Home Directory에 들어갈 내용을 가지고 있음
- Image를 Pulling → PVC Mount 후 /tmp_home 내용을 Notebook의 **/home/jovyan** 으로 설정된 PVC로 복사(Terminal을 통해 /tmp_home이 있는 것 확인 가능)

    → 따라서 Notebook에 PVC를 Mount할 때 Path를 **/home/jovyan** 으로 설정한 PVC가 꼭 있어야 함


## Notebook Dockerfile

> Notebook Dockerfile format
>
- Custom Notebook Dockerfile Build 주의 사항
    1. User는 jovyan
    2. Notebook Image를 Build하고 Run할 때 **S6-Overlay** 의 **init system** 을 사용 [https://github.com/just-containers/s6-overlay]
        1. Custom Notebook Dockerfile 작업할 때 마지막에 **ENTRYPOINT [”/init”]** 이 들어감
    3. Image를 Build할 때는 ${HOME}과 관련된 PVC가 Mount되어 있지 않은 상황
        1. Home Directory에 Default Data를 설정하기 위해서는 /tmp_home 에 넣어놓으면 Home Directory로 Copy
        2. Python Package Installation 과정에서 pip install —user 를 사용하게 되면 Home Directory가 없기 때문에 오류가 발생
- 추가 설정 구성
    - KFP(1.8.14) : Pipeline 작업을 위한 Python Module
    - OpenCV 설정 : Root 사용자에서 설치
    - sudo 설정 : Root 사용자에서 설치 및 설정 **[Kubernets Pod에 Sudo를 주게 되면 보안에 치명적]**

```docker
FROM public.ecr.aws/j1r0q0g6/notebooks/notebook-servers/base:v1.5.0

RUN echo "c.FileContentsManager.delete_to_trash = False" >> /tmp_home/jovyan/.jupyter/jupyter_lab_config.py

COPY ./plugin.jupyterlab-settings /tmp_home/jovyan/.jupyter/lab/user-settings/@jupyterlab/docmanager-extension/plugin.jupyterlab-settings

RUN pip3 install kfp==1.8.14

USER root
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A4B469963BF863CC
RUN apt-get update
RUN apt-get install -y libgl1-mesa-glx

USER jovyan
```

- Nexus에 Image Build
    - Daemon.json 수정 : daemon.json에 **insecure-registries** 추가

    ```bash
    # Image를 Nexus에 올리기 전에 반드시 Nexus 인증 설정을 진행
    sudo vi /etc/docker/daemon.json
    ```

    ```json
    {
      "exec-opts": ["native.cgroupdriver=systemd"],
      "log-driver": "json-file",
      "log-opts": {
        "max-size": "100m"
      },
      "storage-driver": "overlay2",
      "insecure-registries":[
        "http://0.0.0.0:5000"
      ]
    }
    ```

    ```bash
    sudo systemctl restart docker
    ```

    - Image Build

    ```bash
    docker build -t 0.0.0.0:5000/${IMAGE_NAME}:${TAG} .
    ```


---

# Notebook Type별 핵심 요소

## Kubeflow Notebook YAML Base Template

> Kubeflow에서 Notebook을 생성하기 위해 구성되어야 하는 YAML Base Template
>

```yaml
apiVersion: kubeflow.org/v1
kind: Notebook
metadata:
  name: test-notebook # Notebook Name
  namespace: matilda
  labels:
    app: test-notebook # Notebook Name
spec:
  template:
    spec:
      serviceAccountName: default-editor # Kubeflow Default Profile
      containers:
      - name: test-notebook # Notebook Name
        image: 0.0.0.0:5000/jupyter-scipy # Nexus Notebook Image
        imagePullPolicy: IfNotPresent
        # Resource Limits, Requests setting
        resources:
          limits:
            cpu: "2"
            memory: 5Gi
          requests:
            cpu: 200m
            memory: 500Mi
        # Notebook Volume : At least 1 volume
        volumeMounts:
        - mountPath: /home/jovyan
          name: test-notebook-vol
      imagePullSecrets:
      - name: nexuscred # Nexus Secret
      securityContext:
        runAsUser: 1000
      volumes:
      - name: test-notebook-vol
        persistentVolumeClaim:
          claimName: test-notebook-vol
```

## 1. Jupyter Notebook

> Kubeflow에서 가장 기본적으로 제공하는 Notebook Type
>
- Jupyter Notebook Dockerfile Sample

    ```docker
    FROM public.ecr.aws/j1r0q0g6/notebooks/notebook-servers/jupyter-tensorflow:v1.5.0

    RUN echo "c.FileContentsManager.delete_to_trash = False" >> /tmp_home/jovyan/.jupyter/jupyter_lab_config.py

    COPY ./plugin.jupyterlab-docmanager-settings /tmp_home/jovyan/.jupyter/lab/user-settings/@jupyterlab/docmanager-extension/plugin.jupyterlab-settings
    COPY ./plugin.jupyterlab-extension-settings /tmp_home/jovyan/.jupyter/lab/user-settings/@jupyterlab/extensionmanager-extension/plugin.jupyterlab-settings

    RUN pip3 install kfp==1.8.14

    USER root
    RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A4B469963BF863CC
    RUN apt-get update
    RUN apt-get install -y libgl1-mesa-glx

    WORKDIR /tmp_home
    RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    RUN unzip awscliv2.zip
    RUN ./aws/install

    USER jovyan

    RUN jupyter labextension install jupyterlab-tabular-data-editor
    ```


Kubeflow에서 Jupyter Notebook은 가장 기본적인 Notebook 환경으로 추가적인 Annotation은 추가하지 않아도 가능

- **Jupyter Notebook에서 추가되는 사항**
    1. Delete to Trash : 데이터 삭제에 대한 옵션 설정
    2. Jupyterlab Plugin : Jupyterlab 사용 과정에서 필요한 추가적인 Plugin 설정
    3. Tabular Data Editor : CSV 파일을 위한 Tabular Editor
    4. AWS CLI : AWS 사용을 위한 AWS용 Command Line Interface 설치

### 1. Delete to Trash

Kubeflow에서 제공하는 Jupyter Notebook에서는 기본적으로 파일/디렉토리 등을 삭제하게 되면 휴지통 개념의 숨겨진 Directory로 이동 : **${HOME}/.local/Trash/files**

→ 해당 옵션이 활성화 되어 있으면 추가로 마운트했던 PVC에서 디렉토리를 찾지 못하여 문제가 발생

실제로 Delete를 수행하기 위해서는 해당 옵션을 OFF 해주어야 하는데, 이는 **${HOME}/.jupyter** 디렉토리 내부에 있는 **Jupyter_lab_config.py** Jupyter Config 파이썬 파일에서 해당 옵션을 추가해주어야 함

```python
# Trash 디렉토리로 보내는 것(mv)이 아닌 삭제(rm)하도록 설정
c.FileContentsManager.delete_to_trash = False
```

### 2. JupyterLab Setting 값 설정

Jupyter Notebook에서는 해당 노트북 환경에 대한 Extension Plugin Setting 값을 설정할 수 있는데, 경로는 **/tmp_home/jovyan/.jupyter/lab/user-settings/@jupyterlab** 하위로 설정

필요한 Plugin 설정이 있는 경우 해당 설정값이 포함된 파일을 만들고 Dockerfile 내에서 COPY 수행

- Markdown Previewer Default 설정
    - 경로 설정 : Setting Base Path + **/docmanager-extension/plugin.jupyterlab-settings**

```json
{
	"defaultViewer" : {
		"markdown" : "Markdown Preview"
	}
}
```

- Extension Manager 활성
    - 경로 설정 : Setting Base Path + **/extensionmanager-extension/plugin.jupyterlab-settings**

```json
{
    // Extension Manager
    // @jupyterlab/extensionmanager-extension:plugin
    // Extension manager settings.
    // *********************************************

    // Disclaimed Status
    // Whether the user understand that extensions managed through this interface run arbitrary code that may be dangerous
    "disclaimed": true
}
```

### 3. Tabular Data Editor

Jupyter Notebook 환경에서 CSV 파일을 Control 할 수 있는 Jupyter Extension Module

```bash
# Jupyter Lab >= 2.0
jupyter labextension install jupyterlab-tabular-data-editor
```

- JupyterLab 3.0 이상부터는 PiPy로 Install 했는데, 추후 Test 필요

### 4. Jupyter S3 Browser

Jupyter Notebook 환경에서 AWS S3 Bucket을 사용하기 위한 Jupyter Extension Module

```bash
# Jupyter S3 Browser 설치
pip3 install jupyterlab-s3-browser
```

### 4. AWS CLI Interface

> dvc 사용을 위한 AWS CLI Interface 환경 구축 중 하나
>

```bash
# JupyterLab 안에 sudo가 install 되어있거나,
# root 권한을 가진 계정이 있어야 함
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip

# 해당 부분에서 Root 권한을 요구
sudo ./aws/install

# 성공적으로 Install이 끝나면 version check
aws --version
```

## 2. R Studio Server

> R Studio Server를 생성하는 과정에서 필요한 요소들 정리
>

R Studio는 Jupyter Notebook과는 다르게 접속 URL 설정을 진행 : **Annotation**을 통해 수행

```yaml
# ...
metadata:
  # ...
  annotations:
    # R Studio를 위한 Root Path 설정 /notebook/${NAMESPACE}/${NOTEBOOK_NAME}
    notebooks.kubeflow.org/http-headers-request-set: '{"X-RStudio-Root-Path":"/notebook/${NAMESPACE}/${NOTEBOOK_NAME}"}'
    notebooks.kubeflow.org/http-rewrite-uri: /
# ...
```

- 추가 작업
    - Markdown Viewer : **R Markdown** 관련 Review
    - Project Directory Test

## 3. VS Code Web

> Kubeflow 기반 VS Code Web을 위한 작업
>

VS Code Web 역시 R Studio와 유사한데, VS Code Web을 실행하기 위한 Annotation을 추가

```yaml
# ...
metadata:
  # ...
  annotations:
    notebooks.kubeflow.org/http-rewrite-uri: /
# ...
```

- 추가 작업
    - Remote Desktop, Github 등 추가 테스트
    - Project Directory Test
    - Markdown Viewer 처리

---

## Reference.

- Notebook 중지
    - Kubernetes에서 Notebook과 연결된 Service의 Endpoint가 없어짐 (Pod가 내려갔기 때문)
    - Kubernetes에서 Pod는 사라지고, statefulset이 1/1 → 0/0 으로 변화
    - Pod가 내려갔기 때문에 설치한 Python Package는 사라짐 → 이미지에 포함시키거나 requirements.txt를 생성하여 설치
- R Studio File Browser
    - JSON RPC를 통한 List 호출

    ```yaml
    persist-auth=0;
    csrf-token=fe385809-64dd-4644-a147-82b8929cb508;
    port-token=7f4b9396e6a1;
    user-id=jovyan|Mon%2C%2020%20Feb%202023%2006%3A15%3A35%20GMT|kZUy26QMLyPX9NMWPdTTGFfZwLgsvb4s8JV3wS871ps%3D;
    user-list-id=9c16856330a7400cbbbba228392a5d83|Mon%2C%2020%20Feb%202023%2006%3A15%3A35%20GMT|Q%2BlJjxFiqdmJ75266pbRalZINJ4%2BlXNFWc7lzokDxRg%3D;
    csrftoken=sMoyBSwkItBgbYaM0lev7MKwKZd7fpINkZthwlwwX9dIjJN0WYKTjy05OgUA5Pzp;
    authservice_session=MTY3Njg2NTM5MHxOd3dBTkV4VVQwdFlWMDh5TkZwUFZqWlpUa1ZaVmpOTE5rTTJTVXd5VVRSU05WRTNUMUpMV1ZGVVFVUXlSRTAzUTA1VlQxWkpOVkU9fPWDumkMXfT-AanKwCmVmmeXJxrjkpG1JmPOXHCEAN9F
    ```


### Reference:

- [[Jupyter Notebook Swagger API Docs]](https://petstore.swagger.io/?url=https://raw.githubusercontent.com/jupyter/jupyter_server/master/jupyter_server/services/api/api.yaml#/)
- [JupyterLab Tabular Data Editor](https://github.com/jupytercalpoly/jupyterlab-tabular-data-editor)
- [JupyterLab S3 Browser](https://github.com/IBM/jupyterlab-s3-browser)
- [AWS CLI Install Guide](https://inpa.tistory.com/entry/AWS-%F0%9F%93%9A-AWS-CLI-%EC%84%A4%EC%B9%98-%EC%82%AC%EC%9A%A9%EB%B2%95-%EC%89%BD%EA%B3%A0-%EB%B9%A0%EB%A5%B4%EA%B2%8C)
