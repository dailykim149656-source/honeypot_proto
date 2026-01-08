# app/routers/auth.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.auth import create_access_token, MOCK_USERS

router = APIRouter()

# ===== 요청/응답 모델 =====

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserInfo(BaseModel):
    email: str
    name: str
    role: str
    department: str

# ===== 로그인 엔드포인트 =====

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    로그인 (Mock SSO)
    
    테스트 계정:
    - user1@company.com / password123
    - user2@company.com / password123
    - admin@company.com / admin123
    """
    email = request.email.strip().lower()
    password = request.password
    
    # 사용자 검증
    if email not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="존재하지 않는 사용자입니다."
        )
    
    user_data = MOCK_USERS[email]
    if user_data['password'] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 잘못되었습니다."
        )
    
    # 토큰 생성
    token = create_access_token(
        user_id=email.split('@'),
        user_email=email,
        user_name=user_data['name'],
        user_role=user_data['role'],
        user_dept=user_data['department']
    )
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user={
            'email': email,
            'name': user_data['name'],
            'role': user_data['role'],
            'department': user_data['department']
        }
    )

@router.get("/auth/test-accounts")
async def get_test_accounts():
    """
    테스트용 계정 목록 (개발 중에만 사용)
    """
    return {
        "accounts": [
            {
                "email": "user1@company.com",
                "password": "password123",
                "name": "김신입",
                "role": "employee"
            },
            {
                "email": "user2@company.com",
                "password": "password123",
                "name": "이팀장",
                "role": "manager"
            },
            {
                "email": "admin@company.com",
                "password": "admin123",
                "name": "관리자",
                "role": "admin"
            }
        ]
    }
