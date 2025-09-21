import os
import sys
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.apikey_service import ApiKeyService
from services.bybit_validator import BybitApiValidator
from middleware.auth_middleware import get_current_user
from shared.utils import create_api_response

# 라우터 생성
router = APIRouter(prefix="/api/apikey", tags=["API 키 관리"])

# 서비스 인스턴스
apikey_service = ApiKeyService()
bybit_validator = BybitApiValidator(testnet=os.getenv("NODE_ENV") == "development")

# 요청 모델
class ApiKeyRequest(BaseModel):
    api_key: str
    api_secret: str
    validate: bool = True  # 저장 전 검증 여부

class ApiKeyValidateRequest(BaseModel):
    api_key: str
    api_secret: str

# API 키 저장
@router.post("/")
async def save_api_key(
    request: ApiKeyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """API 키 저장"""
    try:
        user_id = current_user['user_id']
        
        # 검증 옵션이 활성화된 경우 먼저 검증
        if request.validate:
            validation_result = await bybit_validator.validate_api_key(
                request.api_key,
                request.api_secret,
                user_id
            )
            
            if not validation_result['valid']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="API 키 검증에 실패했습니다."
                )
        
        # API 키 저장
        result = await apikey_service.save_api_key(
            user_id,
            request.api_key,
            request.api_secret
        )
        
        return create_api_response(
            success=True,
            data=result,
            message="API 키가 성공적으로 저장되었습니다."
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 저장 중 오류가 발생했습니다."
        )

# API 키 조회
@router.get("/")
async def get_api_key(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """API 키 조회 (마스킹됨)"""
    try:
        user_id = current_user['user_id']
        
        api_key_info = await apikey_service.get_api_key(user_id, masked=True)
        
        if not api_key_info:
            return create_api_response(
                success=True,
                data=None,
                message="등록된 API 키가 없습니다."
            )
        
        return create_api_response(
            success=True,
            data=api_key_info,
            message="API 키 정보 조회 완료"
        )
        
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 조회 중 오류가 발생했습니다."
        )

# API 키 수정
@router.put("/")
async def update_api_key(
    request: ApiKeyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """API 키 수정"""
    try:
        user_id = current_user['user_id']
        
        # 검증 옵션이 활성화된 경우 먼저 검증
        if request.validate:
            validation_result = await bybit_validator.validate_api_key(
                request.api_key,
                request.api_secret,
                user_id
            )
            
            if not validation_result['valid']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="API 키 검증에 실패했습니다."
                )
        
        # API 키 수정
        result = await apikey_service.update_api_key(
            user_id,
            request.api_key,
            request.api_secret
        )
        
        return create_api_response(
            success=True,
            data=result,
            message="API 키가 성공적으로 수정되었습니다."
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 수정 중 오류가 발생했습니다."
        )#
 API 키 삭제
@router.delete("/")
async def delete_api_key(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """API 키 삭제"""
    try:
        user_id = current_user['user_id']
        
        result = await apikey_service.delete_api_key(user_id)
        
        return create_api_response(
            success=True,
            data=result,
            message="API 키가 성공적으로 삭제되었습니다."
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 삭제 중 오류가 발생했습니다."
        )

# API 키 검증
@router.post("/validate")
async def validate_api_key(
    request: ApiKeyValidateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """API 키 유효성 검증"""
    try:
        user_id = current_user['user_id']
        
        validation_result = await bybit_validator.validate_api_key(
            request.api_key,
            request.api_secret,
            user_id
        )
        
        return create_api_response(
            success=True,
            data=validation_result,
            message="API 키 검증 완료"
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 검증 중 오류가 발생했습니다."
        )

# API 키 권한 확인
@router.post("/permissions")
async def check_api_permissions(
    request: ApiKeyValidateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """API 키 권한 확인"""
    try:
        permissions_result = await bybit_validator.check_api_permissions(
            request.api_key,
            request.api_secret
        )
        
        return create_api_response(
            success=True,
            data=permissions_result,
            message="API 키 권한 확인 완료"
        )
        
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 권한 확인 중 오류가 발생했습니다."
        )

# API 키 상태 확인
@router.get("/status")
async def get_api_key_status(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """API 키 등록 상태 확인"""
    try:
        user_id = current_user['user_id']
        
        has_key = await apikey_service.has_api_key(user_id)
        
        return create_api_response(
            success=True,
            data={
                "has_api_key": has_key,
                "user_id": user_id
            },
            message="API 키 상태 확인 완료"
        )
        
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 상태 확인 중 오류가 발생했습니다."
        )