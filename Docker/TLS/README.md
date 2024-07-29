# Docker 인증서

> Docker 서버 쪽에 인증서를 발급받아서 Server, Client 쪽에 적용하는 방법

## Docker Server 인증서 작업

**Docker Server**가 있는 곳에서 아래의 작업 진행

### Public Key 및 CA 생성

```shell
# Public Key 생성
openssl genrsa -aes256 -out ca-key.pem 4096
# 이후 비밀번호를 설정하라고 하는데, 외울 수 있는 비밀번호로 설정

# CA 생성
openssl req -new -509 -days 365 -key ca-key.pem -sha56 -out ca.pem
# 국가, 도시, 이메일 등등 입력하는데, ca-key.pem 생성할 때 사용했던 비밀번호를 입력
```

### Server Key 인증 요청서 생성

```shell
# Server Key 생성
openssl genrsa -out server-key.pem 4096

# 인증 요청서 생성
openssl req -sha256 -new -key server-key.pem -out server.csr
```

### Server 인증서 생성

접속할 때 쓰일 IP 기반의 extra config 파일 생성

```shell
vi extfile.cnf
```

```shell
subjectAltName = DNS:${DNS},IP:${PRIVATE_IP},IP:${PUBLIC_IP}
extendedKeyUsage = serverAuth
```

```shell
# 인증서 생성 Public Key 생성할 때 사용한 비밀번호 입력
openssl x509 -req -days 365 -sha256 \
-in server.csr \
-CA ca.pem -CAkey ca-key.pem -CAcreateserial \
-out server-cert.pem \
-extfile extfile.cnf
```

### docker.service에 인증서 파일 적용

```shell
sudo vi /usr/lib/systemd/system/docker.service
```

- ${PATH} : 인증서 관련 파일들이 위치한 경로
- ${PRIVATE_IP} : Docker Server의 Private IP

```shell
# ...
[Service]
Type=notify
# the default is not to use systemd for cgroups because the delegate issues still
# exists and systemd currently does not support the cgroup feature set required
# for containers run by docker
ExecStart=/usr/bin/dockerd --tlsverify --tlscacert=${PATH}/ca.pem --tlscert=${PATH}/server-cert.pem --tlskey=${PATH}/server-key.pem -H fd:// --containerd=/run/containerd/containerd.sock -H tcp://${PRIVATE_IP}:2375
ExecReload=/bin/kill -s HUP $MAINPID
# ...
```

## Client 인증서 작업

Docker Server가 있는 곳에서 아래의 작업들 수행

### Key 생성

```shell
openssl genrsa -out key.pem 4096
```

### 인증 요청서 생성

```shell
openssl req -new -key key.pem -out client.csr
```

### 서버측 인증서 생성

기존의 인증서 생성하는 과정과 다른 점은 인증 요청서와 Extra Config 파일이 다름

```shell
# Extra Config 파일 생성
echo extendedKeyUsage = clientAuth &gt; extfile-client.cnf

openssl x509 -req -days 365 -sha256 -in client.csr \
-CA ca.pem -CAkey ca-key.pem -CAcreateserial \
-out cert.pem \
-extfile extfile-client.cnf
```

### Client 적용

인증서 관련 파일 생성은 끝났고, 파일들의 권한 수정 수행

```shell
# Docker Server 쪽에서 작업 수행
chmod -v 0400 ca-key.pem key.pem server-key.pem
chmod -v 0444 ca.pem server-cert.pem cert.pem
```

Docker Server에서 생성했던 인증서 관련 파일 중 다음 파일들의 내용을 Client 쪽으로 복사

- key.pem
- cert.pem
- ca.pem

위의 파일들을 Client의 ${HOME}/.docker 하위에 붙여넣고 권한 수정

```shell
chmod -v 0400 key.pem
chmod -v 0444 ca.pem cert.pem
```

## Docker 재시작

변경된 인증서를 적용하기 위해 Docker 재시작

```shell
sudo systemctl stop docker
sudo systemctl daemon-reload
sudo systemctl start docker

# Docker 상태 확인
sudo systemctl status docker
```

추가로 해당 Docker Server의 Registry를 Client 쪽에서 조회

```shell
docker images
```

---

### Ref.

- [Docker Damone에 보안 인증서 (TLS) 적용하기](https://blog.naver.com/alice_k106/220743690397)
