# NFS Setting Guide

> Kubernetes NFS Provisioning을 위한 Setup Guide. AWS EC2 Instance 접속 방법은 생략


# 개념

NFS(Network File System) : Network 상에 연결된 다른 컴퓨터의 하드 디스크를 공유하여 사용하는 것

특징

- Network에 연결된 Linux끼리 NFS를 통해 파일 공유 가능
- 공통으로 사용되는 파일에 대해 1대의 Server에 저장하여 효율적인 공간 사용 가능
- 다른 Server에 있는 Directory를 사용하는 것이기 때문에 보안에 취약
- Network를 이용하기 때문에 속도가 느림

# 구축

- 구축 환경
    1. AWS Instance
        1. AWS EC2 Instance T2 Medium
        2. 2 Core(CPU), 4GB(Memory)
        3. Linux 환경 : RHEL 7.9

# 공통 Command

- Installation

```bash
# Package Installation Check(NFS, RPC Bind)
rpm -qa | grep nfs
rpm -qa | grep rpcbind

# NFS Package Install
sudo yum -y install nfs-utils
```

## NFS Server

- 환경 구성

```bash
# 공유 Directory 생성
cd /
sudo mkdir share

# NFS 정상 동작 테스트를 위한 Test File 생성 및 확인
sudo su
echo success nfs > /share/nfs_test
cat /share/nfs_test
```

- 공유 디렉토리 설정
    - exports 설정 옵션
        
        
        | Option | Description |
        | --- | --- |
        | ro | Read Only (읽기만 수행) |
        | rw | Read & Write (읽기 쓰기 모두 수행) |
        | sync | Write 발생 시 디스크 동기화 |
        | nosync | 일정 간격으로 동기화 |
        | root_squash | Client의 Root를 Server의 Nobody로 Mapping |
        | no_root_squash | Client의 Root를 Server의 Root로 Mapping |
        | all_squash | Root를 제외하고 Server와 Client 사용자를 동일 권한으로 설정 |
        | insecure | 인증되지 않은 접근 가능 |
        | noaccess | 지정된 Directory 접근 금지 |

```bash
# /etc/exports에서 설정
sudo vi /etc/exports
```

```bash
# /etc/exports 내용 : Read & Write, Write 발생 시 동기화, Client Root=Server Root
/share 172.31.41.244(rw,sync,no_root_squash)
/share 172.31.39.29(rw,sync,no_root_squash)
/share 172.31.47.248(rw,sync,no_root_squash)
```

- 방화벽 설정
    - **firewall-cmd** 커맨드가 동작하지 않으면 방화벽 설정 넘어감

```bash
# 방화벽 Port(111) 설정
firewall-cmd --permanent --add-service=nfs
firewall-cmd --permanent --add-port=111/tcp
firewall-cmd --permanent --add-port=111/udp
firewall-cmd --reload
```

- NFS Service Start

```bash
# NFS Service 시작
sudo systemctl start nfs
sudo systemctl enable nfs-server
sudo systemctl enable nfs-server.service

# NFS Server Start Check
sudo systemctl status nfs-server
```

- exports 내용 적용

```bash
# /etc/exports 내용 적용
sudo exportfs -ra

# 공유 설정 re-check
showmount -e
sudo exportfs -v
```

## NFS Client

- 환경 구성

```bash
# 공유할 Directory 생성
sudo mkdir /share
```

- NFS Server Mount
    - mount를 하면 일시적으로 되기 때문에 영구적으로 위해서는 추가 작업이 필요함

```bash
# NFS Server와 Mount
sudo mount -t nfs ${PRIVATE_IP}:${SERVER_DIR_PATH} ${CLIENT_DIR_PATH}

# Mount Check -> NFS Server에서 생성한 Text 파일 정상 출력 확인
cat /share/nfs_test
df

# [Optional] fstab을 통한 영구 Mount
sudo vi /etc/fstab
```

```bash
# /etc/fstab 내용
# Created by anaconda on Tue Oct  5 10:09:12 2021
#
# Accessible filesystems, by reference, are maintained under '/dev/disk'
# See man pages fstab(5), findfs(8), mount(8) and/or blkid(8) for more info
#
UUID=698f7103-6394-4a4d-b3bc-0640a0db5b82 /                       xfs     defaults        0 0
172.31.41.244:/share    /share  nfs     defaults        0 0
```

## Reference

- [NFS 환경 구축](https://it-serial.tistory.com/entry/Linux-NFS-%EC%84%9C%EB%B2%84-%EA%B0%9C%EB%85%90-%EA%B5%AC%EC%B6%95%EC%84%A4%EC%B9%98)
- [/etc/exports 옵션](https://m.blog.naver.com/PostView.naver?isHttpsRedirect=true&blogId=musalyh&logNo=220710277058)
