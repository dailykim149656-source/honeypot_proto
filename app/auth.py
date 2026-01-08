# app/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# JWT 설정
JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-prod')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_HOURS = float(os.getenv('JWT_EXPIRE_HOURS', '1'))

# 교육용 사용자 데이터
MOCK_USERS = {
    'user1@company.com': {
        'password': 'password123',
        'name': '김신입',
        'role': 'employee',
        'department': 'Engineering'
    },
    'user2@company.com': {
        'password': 'password123',
        'name': '이팀장',
        'role': 'manager',
        'department': 'HR'
    },
    'admin@company.com': {
        'password': 'admin123',
        'name': '관리자',
        'role': 'admin',
        'department': 'Management'
    },
}

# ===== 토큰 관리 =====

def create_access_token(user_id: str, user_email: str, user_name: str, user_role: str, user_dept: str):
    """
    JWT 토큰 생성
    """
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    to_encode = {
        'user_id': user_id,
        'email': user_email,
        'name': user_name,
        'role': user_role,
        'department': user_dept,
        'exp': expire
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> dict:
    """
    JWT 토큰 검증
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ===== FastAPI 의존성 =====

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    현재 로그인한 사용자 정보 가져오기
    
    사용법:
    @app.get("/protected")
    def protected_route(user: dict = Depends(get_current_user)):
        return {"user": user}
    """
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

def require_role(required_role: str):
    """
    역할 기반 접근 제어
    
    사용법:
    @app.get("/admin-only")
    def admin_route(user: dict = Depends(require_role('admin'))):
        return {"user": user}
    """
    async def role_checker(user: dict = Depends(get_current_user)):
        if user.get('role') != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return role_checker
