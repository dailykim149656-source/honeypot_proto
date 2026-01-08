# test_login.py 생성 후:
import requests
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"email":"user1@company.com","password":"password123"}
)
print(response.json())
