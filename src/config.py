import os
import dotenv

dotenv.load_dotenv()

BIZINFO_API_KEY = os.getenv("BIZINFO_API_KEY")
MSS_SERVICE_KEY = os.getenv("DATA_GO_KR_SERVICE_KEY")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")