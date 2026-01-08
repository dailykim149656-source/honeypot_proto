# app/routers/auth.py - 고급 보안 기능 완성본
# CSRF Token + Rate Limiting + 보안 헤더

from fastapi import APIRouter, HTTPException, status, Header, Request
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from typing import Optional
import secrets
from collections import defaultdict
from time import time

load_dotenv()

# ===== JWT 설정 =====
JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-prod')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_HOURS = float(os.getenv('JWT_EXPIRE_HOURS', '1'))
JWT_REFRESH_EXPIRE_HOURS = float(os.getenv('JWT_REFRESH_EXPIRE_HOURS', '24'))

# ===== 보안 설정 =====
CSRF_TOKEN_EXPIRE_MINUTES = 30
RATE_LIMIT_LOGIN = 10  # 1분당 10회 요청 제한
RATE_LIMIT_WINDOW = 60  # 60초

# ===== 토큰 저장소 =====
ISSUED_REFRESH_TOKENS = {}  # {refresh_token: {email, exp, created_at}}
ISSUED_CSRF_TOKENS = {}  # {csrf_token: {email, exp, used: False}}
LOGIN_ATTEMPTS = defaultdict(list)  # {ip_address: [timestamp1, timestamp2, ...]}

# ===== 교육용 사용자 데이터 =====
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

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ===== Request/Response Models =====

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_email: str
    user_name: str
    user_role: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    csrf_token: str  # ← 추가!
    csrf_expires_in: int  # ← 추가!

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class LogoutRequest(BaseModel):
    refresh_token: str

# ===== Rate Limiting Functions =====

def check_rate_limit(ip_address: str) -> bool:
    """
    Rate Limiting 체크 (로그인)
    1분당 10회 이상 요청 시 차단
    """
    current_time = time()
    
    # 만료된 타임스탬프 제거 (1분 초과)
    LOGIN_ATTEMPTS[ip_address] = [
        timestamp for timestamp in LOGIN_ATTEMPTS[ip_address]
        if current_time - timestamp < RATE_LIMIT_WINDOW
    ]
    
    # 요청 수 확인
    if len(LOGIN_ATTEMPTS[ip_address]) >= RATE_LIMIT_LOGIN:
        return False  # 차단!
    
    # 새 요청 기록
    LOGIN_ATTEMPTS[ip_address].append(current_time)
    return True  # 통과

def get_client_ip(request: Request) -> str:
    """클라이언트 IP 추출"""
    return request.client.host or "unknown"

# ===== CSRF Token Functions =====

def create_csrf_token(email: str) -> str:
    """
    CSRF Token 생성
    - UUID 기반 토큰
    - 30분 유효
    """
    token = secrets.token_urlsafe(32)
    expire = datetime.utcnow() + timedelta(minutes=CSRF_TOKEN_EXPIRE_MINUTES)
    
    ISSUED_CSRF_TOKENS[token] = {
        'email': email,
        'exp': expire,
        'used': False,
        'created_at': datetime.utcnow()
    }
    
    return token

def verify_csrf_token(token: str, email: str) -> bool:
    """
    CSRF Token 검증
    - 토큰 존재 확인
    - 만료 확인
    - 이메일 일치 확인
    """
    if token not in ISSUED_CSRF_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="유효하지 않은 CSRF Token입니다."
        )
    
    csrf_data = ISSUED_CSRF_TOKENS[token]
    
    # 만료 확인
    if datetime.utcnow() > csrf_data['exp']:
        del ISSUED_CSRF_TOKENS[token]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF Token이 만료되었습니다."
        )
    
    # 이메일 일치 확인
    if csrf_data['email'] != email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF Token이 일치하지 않습니다."
        )
    
    return True

def invalidate_csrf_token(token: str):
    """CSRF Token 사용 후 무효화"""
    if token in ISSUED_CSRF_TOKENS:
        del ISSUED_CSRF_TOKENS[token]

# ===== JWT Token Functions =====

def create_access_token(email: str, name: str, role: str):
    """JWT Access Token 생성"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    to_encode = {
        'email': email,
        'name': name,
        'role': role,
        'exp': expire
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(email: str) -> str:
    """Refresh Token 생성"""
    expire = datetime.utcnow() + timedelta(hours=JWT_REFRESH_EXPIRE_HOURS)
    to_encode = {
        'email': email,
        'type': 'refresh',
        'exp': expire
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    ISSUED_REFRESH_TOKENS[encoded_jwt] = {
        'email': email,
        'exp': expire,
        'created_at': datetime.utcnow()
    }
    
    return encoded_jwt

def verify_token(token: str) -> dict:
    """JWT Token 검증"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다. 다시 로그인해주세요.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ===== API Endpoints =====

@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_request: LoginRequest):
    """
    로그인 엔드포인트 (CSRF + Rate Limiting 적용)
    
    테스트 계정:
    - user1@company.com / password123
    - user2@company.com / password123
    - admin@company.com / admin123
    
    보안 기능:
    - Rate Limiting: 1분당 10회 제한
    - CSRF Token: 모든 로그인 응답에 포함
    """
    # ===== 1️⃣ Rate Limiting 체크 =====
    client_ip = get_client_ip(request)
    
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"너무 많은 요청이 발생했습니다. {RATE_LIMIT_WINDOW}초 후 다시 시도해주세요.",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )
    
    # ===== 2️⃣ 사용자 검증 =====
    if login_request.email not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 일치하지 않습니다."
        )
    
    user = MOCK_USERS[login_request.email]
    
    if user['password'] != login_request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 일치하지 않습니다."
        )
    
    # ===== 3️⃣ 토큰 생성 =====
    access_token = create_access_token(
        email=login_request.email,
        name=user['name'],
        role=user['role']
    )
    
    refresh_token = create_refresh_token(login_request.email)
    
    # ===== 4️⃣ CSRF Token 생성 =====
    csrf_token = create_csrf_token(login_request.email)
    
    # ===== 5️⃣ 응답 반환 =====
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_email=login_request.email,
        user_name=user['name'],
        user_role=user['role'],
        expires_in=JWT_EXPIRE_HOURS * 3600,
        refresh_token=refresh_token,
        refresh_expires_in=JWT_REFRESH_EXPIRE_HOURS * 3600,
        csrf_token=csrf_token,
        csrf_expires_in=CSRF_TOKEN_EXPIRE_MINUTES * 60,
    )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(request: RefreshTokenRequest):
    """Refresh Token으로 새 Access Token 발급"""
    refresh_token = request.refresh_token
    
    if refresh_token not in ISSUED_REFRESH_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 Refresh Token입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("email")
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 토큰 타입입니다."
            )
        
    except jwt.ExpiredSignatureError:
        del ISSUED_REFRESH_TOKENS[refresh_token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token이 만료되었습니다. 다시 로그인해주세요.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 Refresh Token입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if email not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다."
        )
    
    user = MOCK_USERS[email]
    
    new_access_token = create_access_token(
        email=email,
        name=user['name'],
        role=user['role']
    )
    
    return RefreshTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRE_HOURS * 3600
    )

@router.post("/logout")
async def logout(request: LogoutRequest):
    """로그아웃 - Refresh Token 무효화"""
    refresh_token = request.refresh_token
    
    if refresh_token in ISSUED_REFRESH_TOKENS:
        del ISSUED_REFRESH_TOKENS[refresh_token]
    
    return {"message": "로그아웃 되었습니다."}

@router.get("/me")
async def get_me(authorization: Optional[str] = Header(None)):
    """현재 사용자 정보 조회"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    return {
        "email": payload.get("email"),
        "name": payload.get("name"),
        "role": payload.get("role")
    }

@router.post("/validate-token")
async def validate_token(authorization: Optional[str] = Header(None)):
    """토큰 유효성 검사"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 없습니다."
        )
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    exp_timestamp = payload.get("exp")
    if exp_timestamp:
        remaining_seconds = int(exp_timestamp - datetime.utcnow().timestamp())
        return {
            "valid": True,
            "remaining_seconds": max(0, remaining_seconds),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="토큰 검증 실패"
    )

# ===== CSRF 검증 데코레이터 (POST/PUT/DELETE 요청용) =====

def verify_csrf_header(csrf_token_from_header: Optional[str] = Header(None), 
                      email: Optional[str] = None) -> bool:
    """
    CSRF Token 헤더 검증
    사용: @verify_csrf_header 데코레이터 사용
    """
    if not csrf_token_from_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF Token이 필요합니다."
        )
    
    verify_csrf_token(csrf_token_from_header, email)
    invalidate_csrf_token(csrf_token_from_header)
    return True