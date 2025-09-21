import os
import sys
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.auth_service import AuthService

# HTTP Bearer 토큰 스키마
security = HTTPBearer()

# AuthService 인스턴스
auth_service = AuthService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """현재 사용자 정보 가져오기 (인증 필수)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await auth_service.verify_token(credentials.credentials)

async def get_current_user_optional(
    request: Request
) -> Optional[Dict[str, Any]]:
    """현재 사용자 정보 가져오기 (인증 선택)"""
    try:
        # Authorization 헤더에서 토큰 추출
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        return await auth_service.verify_token(token)
        
    except Exception:
        return None

class AuthMiddleware:
    """인증 미들웨어"""
    
    @staticmethod
    async def verify_user_access(user_id: int, current_user: Dict[str, Any]) -> None:
        """사용자 접근 권한 확인"""
        if current_user['user_id'] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="접근 권한이 없습니다."
            )
    
    @staticmethod
    async def require_api_key(current_user: Dict[str, Any]) -> None:
        """API 키 등록 필수 확인"""
        if not current_user.get('has_api_key', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bybit API 키를 먼저 등록해주세요."
            )
    
    @staticmethod
    async def require_auto_trade_enabled(current_user: Dict[str, Any]) -> None:
        """자동매매 활성화 필수 확인"""
        if not current_user.get('auto_trade_enabled', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="자동매매를 먼저 활성화해주세요."
            )