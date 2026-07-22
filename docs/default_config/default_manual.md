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

### 4. Github에 원격 저장소 만들고 git remote add origin ... + push 등등