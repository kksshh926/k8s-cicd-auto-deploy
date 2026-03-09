# Troubleshooting

이 문서는 Kubernetes 기반 CI/CD 프로젝트를 진행하면서 발생한 주요 문제와 해결 과정을 정리한 문서이다.

---

## 1. VS Code Remote-SSH 접속 실패

문제  
VS Code Remote-SSH를 통해 Kubernetes master node에 접속하려 할 때 SSH 연결이 실패하였다.

원인  
SSH host key mismatch 문제로 known_hosts에 저장된 fingerprint와 현재 서버의 fingerprint가 일치하지 않아 발생하였다.

해결  

기존 host key 제거 후 재접속

ssh-keygen -R <IP>

이후 VS Code Remote-SSH로 정상 접속 가능하였다.

---

## 2. Docker Permission Denied

문제  
Docker 명령 실행 시 permission denied 오류 발생

permission denied while trying to connect to the Docker daemon socket

원인  
docker daemon 서비스가 정상적으로 설치되지 않았고  
docker.sock 파일 권한이 root로 설정되어 일반 사용자가 접근할 수 없었다.

해결  

snap으로 설치된 Docker 제거

sudo snap remove docker

docker.io 패키지로 Docker 재설치

sudo apt install docker.io

docker 그룹에 사용자 추가

sudo usermod -aG docker $USER

로그아웃 후 재접속하여 정상 동작 확인.

---

## 3. Jenkins Docker Build 실패

문제  
Jenkins Pipeline 실행 중 Docker build 단계에서 오류 발생

permission denied while trying to connect to docker.sock

원인  
Jenkins 서비스 계정이 docker 그룹에 포함되지 않아 Docker daemon 접근 권한이 없었다.

해결  

jenkins 사용자 docker 그룹 추가

sudo usermod -aG docker jenkins

Jenkins 재시작

sudo systemctl restart jenkins

---

## 4. Kubernetes NodePort 접속 실패

문제  
NodePort로 Flask 애플리케이션 접근 불가

원인  
Cilium이 kube-proxy replacement 모드로 동작하면서 NodePort 트래픽 처리 충돌 발생.

해결  

Cilium 설정 수정

kubeProxyReplacement: false

kube-proxy 재시작

kubectl rollout restart ds/kube-proxy -n kube-system

---

## 5. GitHub Webhook 동작 실패

문제  
GitHub Webhook이 Jenkins로 전달되지 않았다.

원인  
Jenkins 서버가 사설 IP 환경(10.x.x.x)에 있어 GitHub에서 직접 접근할 수 없었다.

해결  

Cloudflare Tunnel을 사용하여 Jenkins 서버를 외부에서 접근 가능하도록 설정하였다.

cloudflared tunnel 실행

cloudflared tunnel --url http://localhost:8080

GitHub Webhook URL

https://xxxxx.trycloudflare.com/github-webhook/

이후 GitHub push 시 Jenkins Pipeline이 자동으로 실행되었다.

---