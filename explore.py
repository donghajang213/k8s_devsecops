# import os
# import requests
# import dotenv

# dotenv.load_dotenv()

# ### 기업마당

# BIZINFO_API_KEY = os.getenv("BIZINFO_API_KEY")

# url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"

# params={
#     "crtfcKey" : BIZINFO_API_KEY,
#     "dataType" : "json",
#     "pageUnit" : 10,
#     "pageIndex" : 1
# }

# response = requests.get(url, params=params)
# print(response.status_code)
# print(response.json())

# ### 공공데이터 포털

# DATA_GO_KR_SERVICE_KEY = os.getenv("DATA_GO_KR_SERVICE_KEY")

# url = "https://apis.data.go.kr/1421000/mssBizService_v2/getbizList_v2"

# params={
#     "serviceKey" : DATA_GO_KR_SERVICE_KEY,
#     "pageNo" : 1,
#     "numOfRows" : 10
# }

# response = requests.get(url, params=params)
# print(response.status_code)
# print(response.text)

from src.clients.bizinfo import fetch_bizinfo_data, bizinfo_to_program
from src.clients.mss import fetch_mss_data, mss_to_program

biz_raw = fetch_bizinfo_data()
print(bizinfo_to_program(biz_raw[0]))

mss_raw = fetch_mss_data()
print(mss_to_program(mss_raw[0]))
