# CI/CD 기반 Kubernetes 자동 배포 인프라 구축

## 프로젝트 개요

GitHub에 코드가 push되면 Jenkins가 이를 감지하여 Docker 이미지를 빌드하고 Docker Hub에 업로드한 뒤 Kubernetes Deployment의 이미지를 갱신하여 **Rolling Update 방식으로 애플리케이션을 자동 배포하는 CI/CD 환경을 구축**하였다.

본 프로젝트는 단순한 애플리케이션 배포가 아니라 **GitHub → Jenkins → Docker Hub → Kubernetes**로 이어지는 전체 자동 배포 파이프라인을 직접 구성하는 것을 목표로 하였다.

또한 구축 과정에서 발생한 **네트워크 문제, 권한 문제, Webhook 외부 접근 문제** 등을 분석하고 해결하며 DevOps 운영 환경에서 발생할 수 있는 이슈를 경험하는 데 중점을 두었다.

---

## 프로젝트 아키텍처

### 서비스 아키텍처

```text
Client
 ↓
NodePort Service
 ↓
Flask Web App Pod
 ↓
MySQL Service
 ↓
MySQL Pod
```

외부 사용자는 Kubernetes Node의 **NodePort Service**를 통해 Flask 애플리케이션에 접속하며, 애플리케이션은 내부 **MySQL Service**를 통해 데이터베이스와 통신한다.

Flask 애플리케이션과 MySQL은 각각 별도의 Pod로 배포되며 Kubernetes Service를 통해 연결되도록 구성하였다.

### CI/CD 파이프라인 구조

```text
Developer
   │
   │ git push
   ▼
GitHub
   │
   │ Webhook
   ▼
Cloudflare Tunnel
   │
   ▼
Jenkins
   │
   ├ Docker Image Build
   ├ Docker Hub Push
   └ Kubernetes Deployment Update
   ▼
Kubernetes Rolling Update
```

GitHub push 이벤트가 발생하면 Webhook을 통해 Jenkins Pipeline이 실행되며 다음 작업을 자동으로 수행한다.

1. GitHub repository checkout
2. Docker 이미지 빌드
3. Docker Hub 이미지 push
4. Kubernetes Deployment 이미지 업데이트
5. Rolling Update 방식으로 Pod 교체

이를 통해 **코드 변경부터 실제 서비스 반영까지의 배포 과정을 자동화하였다.**

---

## 사용 기술

### Infrastructure

- Linux (Ubuntu)
- Kubernetes

### Container

- Docker

### Application

- Flask
- MySQL

### CI/CD

- Jenkins
- GitHub Webhook

### Networking

- Cilium CNI
- Kubernetes Service (NodePort)
- Cloudflare Tunnel

### Security

- Kubernetes Secret

---

## Kubernetes 클러스터 구성

```text
master
 ├ kubectl 관리
 ├ Jenkins CI 서버
 ├ Docker build / push
 └ Kubernetes YAML 배포 관리

worker nodes (node1, node2, node3)
 ├ Flask Pod 스케줄링
 └ MySQL Pod 스케줄링

cluster network
 ├ CNI : Cilium
 ├ Service Type : NodePort
 └ Container Runtime : containerd
```

1개의 control-plane 노드와 3개의 worker 노드로 Kubernetes 클러스터를 구성하였다.

애플리케이션 Pod는 worker 노드에 스케줄링되며 master 노드에서는 Jenkins CI 서버와 클러스터 관리 작업을 수행하도록 구성하였다.

---

## 프로젝트 디렉토리 구조

```text
k8s-cicd-auto-deploy

app
 ├ app.py
 ├ requirements.txt
 └ templates
     └ index.html

docker
 └ Dockerfile

docs
 ├ troubleshooting.md
 ├ architecture.png
 └ pipeline-flow.png

jenkins
 └ Jenkinsfile

k8s
 ├ flask-deployment.yaml
 ├ flask-service.yaml
 ├ mysql-deployment.yaml
 ├ mysql-service.yaml
 └ secret.yaml

.dockerignore
.gitignore
README.md
```

---

## 프로젝트 진행 과정

### 1. 웹 애플리케이션 구현

Flask 기반 메시지 게시판 애플리케이션을 구현하고 MySQL 데이터베이스와 연동하였다.

애플리케이션은 컨테이너 환경에서 실행될 수 있도록 설계하였다.

### 2. 애플리케이션 컨테이너화

Dockerfile을 작성하여 Flask 애플리케이션을 Docker 이미지로 빌드하였다.

- Docker 이미지 생성
- 로컬 환경에서 컨테이너 실행 테스트

### 3. Kubernetes 배포

애플리케이션과 데이터베이스를 Kubernetes에 배포하였다.

- Flask Deployment / Service 작성
- MySQL Deployment / Service 작성
- Kubernetes Secret을 활용한 DB 비밀번호 관리

MySQL은 내부 통신을 위해 **ClusterIP Service**로 구성하였다.

### 4. 외부 접속 구성

Flask Service를 **NodePort 타입으로 노출**하여 외부에서 애플리케이션에 접근할 수 있도록 구성하였다.

### 5. Jenkins 기반 CI/CD 구축

GitHub push 이벤트를 기반으로 Jenkins Pipeline이 자동 실행되도록 구성하였다.

Pipeline은 다음 단계를 수행한다.

- GitHub repository checkout
- Docker 이미지 build
- Docker Hub 이미지 push
- Kubernetes Deployment 이미지 업데이트

### 6. 자동 배포 검증

코드 변경 후 GitHub에 push하여 자동 배포 동작을 확인하였다.

```bash
git add .
git commit -m "Test CI/CD auto deployment"
git push origin main
```

배포 확인

```bash
kubectl rollout status deployment/flask-app
```

Pod 교체 확인

```bash
kubectl get pods -w
```

GitHub push 이후 **이미지 빌드부터 실제 서비스 반영까지 약 30~40초 내에 완료됨을 확인하였다.**

---

## Jenkins Pipeline 코드

프로젝트에서 사용한 Jenkins Pipeline은 다음과 같다.

```groovy
pipeline {
    agent any

    environment {
        IMAGE_NAME = "seohyunkirn/k8s-cicd-auto-deploy"
        IMAGE_TAG = "${BUILD_NUMBER}"
        KUBECONFIG = "/var/lib/jenkins/.kube/config"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'git@github.com:kksshh926/k8s-cicd-auto-deploy.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE_NAME:$IMAGE_TAG -f docker/Dockerfile .'
            }
        }

        stage('Push Docker Image') {
            steps {
                sh 'docker push $IMAGE_NAME:$IMAGE_TAG'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh 'kubectl set image deployment/flask-app flask-app=$IMAGE_NAME:$IMAGE_TAG'
            }
        }
    }
}
```

Jenkins는 **빌드 번호를 이미지 태그로 사용**하여 매 배포 시 새로운 이미지를 생성하고, `kubectl set image` 명령을 통해 Kubernetes Deployment 이미지를 갱신하도록 구성하였다.

---

## 트러블슈팅

### 1. VS Code Remote SSH 접속 실패

**문제**

Remote-SSH로 Kubernetes master 노드 접속 시 연결 실패

**원인**

`known_hosts`에 저장된 기존 SSH fingerprint와 현재 서버 fingerprint가 일치하지 않아 host key mismatch 발생

**해결**

```bash
ssh-keygen -R <IP>
```

### 2. Docker permission denied

**문제**

```text
permission denied while trying to connect to the Docker daemon socket
```

**원인**

Docker socket 접근 권한이 없는 상태에서 Docker 명령을 실행하여 발생

**해결**

```bash
sudo apt install docker.io
sudo usermod -aG docker $USER
```

### 3. Kubernetes NodePort 접속 실패

**문제**

NodePort로 노출한 Flask 애플리케이션에 외부에서 접속 불가

**분석**

- Pod 상태 정상
- Service 정상
- Endpoint 정상
- 애플리케이션 로그 정상

즉 애플리케이션 문제가 아닌 **클러스터 네트워크 계층 문제**로 판단하였다.

**원인**

Cilium이 `kubeProxyReplacement=true` 상태로 동작하는 환경에서 kube-proxy 기반 Service 처리와의 정합성 문제가 발생하여 NodePort 트래픽 전달이 정상적으로 이루어지지 않았다.

**해결**

Cilium 설정 수정

```yaml
kubeProxyReplacement: false
standaloneDnsProxy:
  enabled: false
```

이후 네트워크 컴포넌트 재시작

```bash
kubectl -n kube-system rollout restart ds/cilium
kubectl -n kube-system rollout restart ds/kube-proxy
```

### 4. Jenkins Docker 권한 문제

**문제**

Jenkins Pipeline에서 Docker build 단계 실패

**원인**

`jenkins` 사용자가 docker 그룹에 포함되지 않아 Docker daemon 접근 권한이 없었음

**해결**

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### 5. Jenkins GitHub SSH 인증 실패

**문제**

Jenkins에서 GitHub repository clone 실패

**원인**

Jenkins 서비스 계정(`jenkins`) 기준 SSH key가 존재하지 않아 인증 실패

**해결**

```bash
chmod 600 /var/lib/jenkins/.ssh/id_ed25519
sudo -u jenkins ssh -T git@github.com
```

### 6. GitHub Webhook 동작 실패

**문제**

GitHub Webhook이 Jenkins로 전달되지 않음

**원인**

Jenkins 서버가 사설 IP 환경에 있어 GitHub가 직접 접근할 수 없었음

**해결**

Cloudflare Tunnel을 사용하여 외부 접근 가능한 URL 생성

```bash
cloudflared tunnel --url http://localhost:8080
```

Webhook URL 설정

```text
https://xxxxx.trycloudflare.com/github-webhook/
```

---

## 프로젝트 결과

- GitHub push 기반 Jenkins Pipeline 자동 실행
- Docker 이미지 자동 빌드 및 Docker Hub push
- Kubernetes Deployment 자동 업데이트
- Rolling Update 기반 무중단 배포 구현
- 평균 자동 배포 시간 **30~40초**

---

## 프로젝트를 통해 배운 점

- GitHub Webhook, Jenkins, Docker, Kubernetes를 연결하여 **CI/CD 자동 배포 파이프라인을 구축하는 경험**을 얻었다.
- Kubernetes 환경에서 **Deployment, Service, Rolling Update 기반 애플리케이션 배포 과정**을 실제로 운영 환경처럼 경험하였다.
- 권한 문제, SSH 인증 문제, CNI 네트워크 문제, Webhook 외부 접근 문제 등을 직접 분석하고 해결하며 **DevOps 운영 환경에서의 트러블슈팅 경험**을 얻었다.

---

## 향후 개선 사항

- Jenkins Pipeline 파일을 `Pipeline`에서 `Jenkinsfile`로 표준화
- Prometheus / Grafana 기반 모니터링 구축
- HTTPS 인증서 적용
- HPA 기반 자동 스케일링
- Terraform을 활용한 인프라 코드화
- ArgoCD 기반 GitOps 배포 구조 도입
