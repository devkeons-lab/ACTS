import os
import sys
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.settings_service import SettingsService
from middleware.auth_middleware import get_current_user
from shared.utils import create_api_response

# 라우터 생성
router = APIRouter(prefix="/api/settings", tags=["사용자 설정"])

# 서비스 인스턴스
settings_service = SettingsService()

# 요청 모델
class SettingsUpdateRequest(BaseModel):
    auto_trade_enabled: Optional[bool] = None
    risk_level: Optional[str] = Field(None, regex="^(low|medium|high)$")
    max_leverage: Optional[int] = Field(None, ge=1, le=100)
    custom_prompt: Optional[str] = Field(None, max_length=2000)

class AutoTradeToggleRequest(BaseModel):
    enabled: bool

# 설정 조회
@router.get("/")
async def get_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """사용자 설정 조회"""
    try:
        user_id = current_user['user_id']
        
        settings = await settings_service.get_user_settings(user_id)
        
        return create_api_response(
            success=True,
            data=settings,
            message="사용자 설정 조회 완료"
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 설정 조회 중 오류가 발생했습니다."
        )

# 설정 업데이트
@router.post("/")
async def update_settings(
    request: SettingsUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """사용자 설정 업데이트"""
    try:
        user_id = current_user['user_id']
        
        updated_settings = await settings_service.update_user_settings(
            user_id,
            auto_trade_enabled=request.auto_trade_enabled,
            risk_level=request.risk_level,
            max_leverage=request.max_leverage,
            custom_prompt=request.custom_prompt
        )
        
        return create_api_response(
            success=True,
            data=updated_settings,
            message="사용자 설정이 업데이트되었습니다."
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 설정 업데이트 중 오류가 발생했습니다."
        )

# 자동매매 토글
@router.post("/auto-trade/toggle")
async def toggle_auto_trade(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """자동매매 활성화/비활성화 토글"""
    try:
        user_id = current_user['user_id']
        
        updated_settings = await settings_service.toggle_auto_trade(user_id)
        
        return create_api_response(
            success=True,
            data={
                "auto_trade_enabled": updated_settings['auto_trade_enabled'],
                "settings": updated_settings
            },
            message=f"자동매매가 {'활성화' if updated_settings['auto_trade_enabled'] else '비활성화'}되었습니다."
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동매매 설정 변경 중 오류가 발생했습니다."
        )

# 자동매매 활성화/비활성화
@router.post("/auto-trade")
async def set_auto_trade(
    request: AutoTradeToggleRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """자동매매 활성화/비활성화 설정"""
    try:
        user_id = current_user['user_id']
        
        updated_settings = await settings_service.update_user_settings(
            user_id,
            auto_trade_enabled=request.enabled
        )
        
        return create_api_response(
            success=True,
            data=updated_settings,
            message=f"자동매매가 {'활성화' if request.enabled else '비활성화'}되었습니다."
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동매매 설정 변경 중 오류가 발생했습니다."
        )#
 기본 GPT 프롬프트 조회
@router.get("/gpt-prompt/default")
async def get_default_gpt_prompt():
    """기본 GPT 프롬프트 조회"""
    try:
        default_prompt = await settings_service.get_default_gpt_prompt()
        
        return create_api_response(
            success=True,
            data={
                "default_prompt": default_prompt
            },
            message="기본 GPT 프롬프트 조회 완료"
        )
        
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="기본 GPT 프롬프트 조회 중 오류가 발생했습니다."
        )

# 설정 초기화
@router.post("/reset")
async def reset_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """사용자 설정 초기화"""
    try:
        user_id = current_user['user_id']
        
        reset_settings = await settings_service.reset_settings(user_id)
        
        return create_api_response(
            success=True,
            data=reset_settings,
            message="사용자 설정이 초기화되었습니다."
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 설정 초기화 중 오류가 발생했습니다."
        )

# 자동매매 가능 여부 검증
@router.get("/validation")
async def validate_auto_trade_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """자동매매 설정 검증"""
    try:
        user_id = current_user['user_id']
        
        validation_result = await settings_service.validate_settings_for_auto_trade(user_id)
        
        return create_api_response(
            success=True,
            data=validation_result,
            message="자동매매 설정 검증 완료"
        )
        
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동매매 설정 검증 중 오류가 발생했습니다."
        )

# 위험도별 추천 설정 조회
@router.get("/recommendations/{risk_level}")
async def get_risk_level_recommendations(risk_level: str):
    """위험도별 추천 설정 조회"""
    try:
        if risk_level not in ["low", "medium", "high"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="위험도는 'low', 'medium', 'high' 중 하나여야 합니다."
            )
        
        recommendations = {
            "low": {
                "max_leverage": 3,
                "description": "안전한 거래를 위한 낮은 레버리지",
                "features": [
                    "낮은 레버리지로 안전한 거래",
                    "보수적인 매매 전략",
                    "손실 위험 최소화"
                ]
            },
            "medium": {
                "max_leverage": 10,
                "description": "균형잡힌 위험과 수익",
                "features": [
                    "적당한 레버리지로 균형잡힌 거래",
                    "중간 수준의 매매 빈도",
                    "안정적인 수익 추구"
                ]
            },
            "high": {
                "max_leverage": 20,
                "description": "높은 수익을 위한 공격적 거래",
                "features": [
                    "높은 레버리지로 공격적 거래",
                    "빈번한 매매 기회 포착",
                    "높은 수익 가능성 (높은 위험 동반)"
                ]
            }
        }
        
        return create_api_response(
            success=True,
            data={
                "risk_level": risk_level,
                "recommendations": recommendations[risk_level]
            },
            message=f"{risk_level} 위험도 추천 설정 조회 완료"
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="추천 설정 조회 중 오류가 발생했습니다."
        )