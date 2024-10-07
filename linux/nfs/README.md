# NFS(Network File System)

> Ubuntu NFS Server/Client 구성 방법 정리
> 

## NFS Server

- 필요 Port : **2049**

```bash
sudo apt update

sudo apt install nfs-kernel-server

# 정상 동작 확인
sudo systemctl status nfs-server

sudo mkdir ${SERVER_DIRECTORY_PATH**}** # 공유할 디렉토리 생성

# [If Required]
sudo chown -R nobody:nogroup ${SERVER_DIRECTORY_PATH}
```

### Export 수정

```bash
sudo vi /etc/exports
```

```bash
${SERVER_DIRECTORY_PATH} ${CLIENT_IP}(rw,sync,no_root_squash) # in () : Mount Rule
```

```bash
# export 파일 적용
sudo exportfs -ra

# NFS Server 재시작
sudo systemctl restart nfs-server

# Mount 확인
showmount -e
sudo exportfs -v
```

## NFS Client

```bash
sudo apt update

sudo apt install nfs-common

# 정상 동작 확인
sudo systemctl status nfs-common

# 공유 받을 디렉토리 생성
sudo mkdir -p ${CLIENT_DIRECTORY_PATH}

# NFS Mount
sudo mount -t nfs ${SERVER_IP}:${SERVER_DIRECTORY_PATH} ${CLIENT_DIRECTORY_PATH}
```

**[Optional]** Mount 해제

```bash
sudo umount ${CLIENT_DIRECTORY_PATH}
```

---

## Report

### 1. NFS Client 비정상적인 동작

```bash
sudo systemctl status nfs-common
```

```bash
○ nfs-common.service
     Loaded: masked (Reason: Unit nfs-common.service is masked.)
     Active: inactive (dead)
```

해결 방법

- /lib/systemd/system/nfs-common.service 삭제 후 NFS Client 재시작
    
    ```bash
    sudo rm /lib/systemd/system/nfs-common.service
    
    # Daemon Reload
    sudo systemctl daemon-reload
    
    # Restart NFS Client
    sudo systemctl start nfs-common
    ```
    

---

## Ref.

- [Ubuntu NFS Server & Client 구성 방법](https://dongle94.github.io/ubuntu/ubuntu-nfs-setting/)
