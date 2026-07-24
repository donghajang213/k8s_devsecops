1.패키지 설치 : uv add requests python-dotenv
2. 루트에 explore.py 같은 임시 파일 하나 (나중에 지우거나 scripts/로 옮길 예정, 지금은 그냥 눈으로 확인용)
3. python-dotenv의 load_dotenv() + os.getenv("BIZINFO_API_KEY")로 .env 값 불러오기
4. 해당 API 파라미터 확인하여 불러오기