# Dockerfile Sample
# Python 가상 환경 3.6.8에서 실행
FROM python:3.6.8

# PyPi Upgrade
RUN pip install --upgrade pip

# Server 경로 이동 및 작업 Directory 복사
WORKDIR /usr/src/${PROJECT_NAME}
COPY . .

# PyPi Requirements Install
RUN pip3 install -r requirements.txt

# Kubernetes 환경을 위한 Config Setting 작업
RUN mkdir $HOME/.kube
RUN mv config $HOME/.kube

# Manage.py를 실행하기 위해 작업 디렉토리 이동
WORKDIR ./${DIRECTORY_NAME}

# Run Server : --settings 부분 알아서 수정 (없어도 되는 부분. 참고만 할 것)
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000", "--settings=..."]

# Docker 8000 Port Open
EXPOSE 8000
