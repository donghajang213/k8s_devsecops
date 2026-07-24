### 1. uv
1. pip install uv
2. uv init -- pyproject.toml, python-version, main.py 등 프로젝트 만듦, 
   주의 : uv init은 기본적으로 git 저장소가 없으면 자동으로 git init까지 같이 해버림.
3. uv venv
4. .venv\Scripts\activate

### 2. .gitignore -- 해당 프로젝트 특성상 최소 들어가야할 것
.venv/, __pycache__/, *.pyc
.env, *.tfvars (시크릿/자격증명 — DevSecOps 프로젝트에서 특히 중요)
.terraform/, *.tfstate, *.tfstate.backup
kubeconfig, *.kubeconfig (있다면)

### 3. 첫 커밋 (git add, git commit)

1. git config (이 프로젝트에만 적용하려면 --local, 전역이면 --global)

git config --local user.name "본인이름 또는 GitHub 아이디"
git config --local user.email "alja4097@gmail.com"

***전역 설정이 이미 되어있는지 먼저 확인하려면***
git config --global user.name
git config --global user.email

2. 첫 커밋
git commit -m "chore: initial project setup with uv"

3. Github 원격 저장소 만들기
gh CLI 있으면 (로그인 여부 확인: gh auth status):
gh repo create k8s_devsecops --public --source=. --remote=origin
(--private로 바꾸면 비공개. --source=.는 현재 디렉토리를 그 repo로 연결)

gh 없이 웹에서 만들었다면:
git remote add origin https://github.com/<아이디>/k8s_devsecops.git

4. push
git branch -M main
git push -u origin main

git remote -v 로 origin 확인 
