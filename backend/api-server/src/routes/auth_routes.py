import os
import sys
from fastapi import APIRouter, HTTPException, status, Depends, Response
from pydantic import BaseModel, EmailStr
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.auth_service import AuthService
from middleware.auth_middleware import get_current_user
from shared.utils import create_api_response

# 라우터 생성
router = APIRouter(prefix="/api/auth", tags=["인증"])

# AuthService 인스턴스
auth_service = AuthService()

# 요청 모델
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# 회원가입
@router.post("/register")
async def register(request: RegisterRequest):
    """사용자 회원가입"""
    try:
        result = await auth_service.register_user(
            email=request.email,
            password=request.password
        )
        
        return create_api_response(
            success=True,
            data=result,
            message="회원가입이 완료되었습니다."
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다."
        )

# 로그인
@router.post("/login")
async def login(request: LoginRequest, response: Response):
    """사용자 로그인"""
    try:
        result = await auth_service.login_user(
            email=request.email,
            password=request.password
        )
        
        # JWT 토큰을 httpOnly 쿠키로 설정
        response.set_cookie(
            key="token",
            value=result["token"],
            httponly=True,
            secure=os.getenv("NODE_ENV") == "production",
            samesite="strict",
            max_age=24 * 60 * 60  # 24시간
        )
        
        # 응답에서 토큰 제거 (쿠키로만 전송)
        response_data = result.copy()
        del response_data["token"]
        
        return create_api_response(
            success=True,
            data=response_data,
            message="로그인이 완료되었습니다."
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다."
        )

# 로그아웃
@router.post("/logout")
async def logout(response: Response):
    """사용자 로그아웃"""
    try:
        # 쿠키 삭제
        response.delete_cookie(key="token")
        
        return create_api_response(
            success=True,
            message="로그아웃이 완료되었습니다."
        )
        
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그아웃 처리 중 오류가 발생했습니다."
        )

# 현재 사용자 정보
@router.get("/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    try:
        user_profile = await auth_service.get_user_profile(current_user['user_id'])
        
        return create_api_response(
            success=True,
            data=user_profile,
            message="사용자 정보 조회 완료"
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 조회 중 오류가 발생했습니다."
        )

# 토큰 검증
@router.get("/verify")
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """토큰 유효성 검증"""
    return create_api_response(
        success=True,
        data={
            "valid": True,
            "user": current_user
        },
        message="유효한 토큰입니다."
    )