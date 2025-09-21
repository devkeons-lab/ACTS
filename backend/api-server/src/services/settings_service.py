import os
import sys
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.database import execute_query_single, execute_update
from shared.utils import is_valid_leverage, is_valid_risk_level, log_info, log_error
from shared.symbols import is_supported_symbol, is_supported_interval

class SettingsService:
    """사용자 설정 관리 서비스"""
    
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """사용자 설정 조회"""
        try:
            settings_data = execute_query_single(
                """
                SELECT auto_trade_enabled, risk_level, max_leverage, custom_prompt,
                       preferred_symbol, preferred_interval,
                       bybit_api_key IS NOT NULL as has_api_key,
                       updated_at
                FROM users WHERE id = %s
                """,
                (user_id,)
            )
            
            if not settings_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            return {
                "auto_trade_enabled": settings_data['auto_trade_enabled'],
                "risk_level": settings_data['risk_level'],
                "max_leverage": settings_data['max_leverage'],
                "preferred_symbol": settings_data['preferred_symbol'] or 'BTCUSDT',
                "preferred_interval": settings_data['preferred_interval'] or '1',
                "custom_prompt": settings_data['custom_prompt'],
                "has_api_key": settings_data['has_api_key'],
                "updated_at": settings_data['updated_at'].isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as error:
            log_error("사용자 설정 조회 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 설정 조회 중 오류가 발생했습니다."
            )
    
    async def update_user_settings(
        self,
        user_id: int,
        auto_trade_enabled: Optional[bool] = None,
        risk_level: Optional[str] = None,
        max_leverage: Optional[int] = None,
        preferred_symbol: Optional[str] = None,
        preferred_interval: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """사용자 설정 업데이트"""
        try:
            # 현재 설정 조회
            current_settings = await self.get_user_settings(user_id)
            
            # 업데이트할 필드 준비
            update_fields = []
            update_values = []
            
            # 자동매매 활성화 설정
            if auto_trade_enabled is not None:
                # API 키가 없으면 자동매매 활성화 불가
                if auto_trade_enabled and not current_settings['has_api_key']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="자동매매를 활성화하려면 먼저 Bybit API 키를 등록해주세요."
                    )
                
                update_fields.append("auto_trade_enabled = %s")
                update_values.append(auto_trade_enabled)
            
            # 위험도 설정
            if risk_level is not None:
                if not is_valid_risk_level(risk_level):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="위험도는 'low', 'medium', 'high' 중 하나여야 합니다."
                    )
                
                update_fields.append("risk_level = %s")
                update_values.append(risk_level)
            
            # 최대 레버리지 설정
            if max_leverage is not None:
                if not is_valid_leverage(max_leverage):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="레버리지는 1~100 사이의 정수여야 합니다."
                    )
                
                update_fields.append("max_leverage = %s")
                update_values.append(max_leverage)
            
            # 선호 심볼 설정
            if preferred_symbol is not None:
                if not is_supported_symbol(preferred_symbol):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="지원하지 않는 심볼입니다."
                    )
                
                update_fields.append("preferred_symbol = %s")
                update_values.append(preferred_symbol.upper())
            
            # 선호 캔들 간격 설정
            if preferred_interval is not None:
                if not is_supported_interval(preferred_interval):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="지원하지 않는 캔들 간격입니다."
                    )
                
                update_fields.append("preferred_interval = %s")
                update_values.append(preferred_interval)
            
            # 커스텀 프롬프트 설정
            if custom_prompt is not None:
                if len(custom_prompt.strip()) > 2000:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="커스텀 프롬프트는 2000자를 초과할 수 없습니다."
                    )
                
                update_fields.append("custom_prompt = %s")
                update_values.append(custom_prompt.strip() if custom_prompt.strip() else None)
            
            # 업데이트할 필드가 없으면 현재 설정 반환
            if not update_fields:
                return current_settings
            
            # 업데이트 실행
            update_fields.append("updated_at = NOW()")
            update_values.append(user_id)
            
            query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            
            affected_rows = execute_update(query, tuple(update_values))
            
            if affected_rows == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            # 업데이트된 설정 조회
            updated_settings = await self.get_user_settings(user_id)
            
            log_info("사용자 설정 업데이트 완료", {
                "user_id": user_id,
                "updated_fields": len(update_fields) - 1,  # updated_at 제외
                "auto_trade_enabled": updated_settings['auto_trade_enabled']
            })
            
            return updated_settings
            
        except HTTPException:
            raise
        except Exception as error:
            log_error("사용자 설정 업데이트 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 설정 업데이트 중 오류가 발생했습니다."
            )    asy
nc def toggle_auto_trade(self, user_id: int) -> Dict[str, Any]:
        """자동매매 토글"""
        try:
            current_settings = await self.get_user_settings(user_id)
            new_status = not current_settings['auto_trade_enabled']
            
            return await self.update_user_settings(
                user_id,
                auto_trade_enabled=new_status
            )
            
        except HTTPException:
            raise
        except Exception as error:
            log_error("자동매매 토글 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="자동매매 설정 변경 중 오류가 발생했습니다."
            )
    
    async def get_default_gpt_prompt(self) -> str:
        """기본 GPT 프롬프트 조회"""
        try:
            from shared.database import execute_query_single
            
            setting_data = execute_query_single(
                "SELECT setting_value FROM system_settings WHERE setting_key = 'default_gpt_prompt'"
            )
            
            if setting_data:
                return setting_data['setting_value']
            else:
                # 기본 프롬프트 반환
                return """당신은 고도로 숙련된 암호화폐 트레이더입니다. 
제공된 BTCUSDT 1분봉 차트 데이터를 분석하여 매매 판단을 내려주세요.

응답은 반드시 다음 JSON 형식으로 해주세요:
{
    "action": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "leverage": 1-20,
    "reason": "판단 근거를 상세히 설명"
}

분석 시 고려사항:
- RSI, MACD, 볼린저 밴드 등 기술적 지표
- 거래량 변화
- 지지선과 저항선
- 시장 트렌드"""
                
        except Exception as error:
            log_error("기본 GPT 프롬프트 조회 실패", {"error": str(error)})
            return "기본 프롬프트를 불러올 수 없습니다."
    
    async def reset_settings(self, user_id: int) -> Dict[str, Any]:
        """설정 초기화"""
        try:
            # 기본값으로 초기화
            return await self.update_user_settings(
                user_id,
                auto_trade_enabled=False,
                risk_level="medium",
                max_leverage=10,
                custom_prompt=None
            )
            
        except HTTPException:
            raise
        except Exception as error:
            log_error("설정 초기화 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="설정 초기화 중 오류가 발생했습니다."
            )
    
    async def validate_settings_for_auto_trade(self, user_id: int) -> Dict[str, Any]:
        """자동매매 가능 여부 검증"""
        try:
            settings = await self.get_user_settings(user_id)
            
            validation_result = {
                "can_auto_trade": True,
                "issues": []
            }
            
            # API 키 확인
            if not settings['has_api_key']:
                validation_result["can_auto_trade"] = False
                validation_result["issues"].append("Bybit API 키가 등록되지 않았습니다.")
            
            # 설정 값 확인
            if not is_valid_risk_level(settings['risk_level']):
                validation_result["can_auto_trade"] = False
                validation_result["issues"].append("위험도 설정이 올바르지 않습니다.")
            
            if not is_valid_leverage(settings['max_leverage']):
                validation_result["can_auto_trade"] = False
                validation_result["issues"].append("레버리지 설정이 올바르지 않습니다.")
            
            return validation_result
            
        except Exception as error:
            log_error("자동매매 설정 검증 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            return {
                "can_auto_trade": False,
                "issues": ["설정 검증 중 오류가 발생했습니다."]
            }