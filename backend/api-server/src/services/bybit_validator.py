import os
import sys
import httpx
import hmac
import hashlib
import time
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.utils import log_info, log_error

class BybitApiValidator:
    """Bybit API 키 검증 서비스"""
    
    def __init__(self, testnet: bool = False):
        self.base_url = (
            os.getenv('BYBIT_TESTNET_URL', 'https://api-testnet.bybit.com')
            if testnet else
            os.getenv('BYBIT_API_URL', 'https://api.bybit.com')
        )
        self.timeout = 10.0
    
    async def validate_api_key(
        self,
        api_key: str,
        api_secret: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """API 키 유효성 검증"""
        try:
            # 기본 형식 검증
            if not api_key or not api_secret:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="API 키와 시크릿 키를 모두 입력해주세요."
                )
            
            if len(api_key) < 10 or len(api_secret) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="API 키 형식이 올바르지 않습니다."
                )
            
            # Bybit API 호출로 검증
            validation_result = await self._test_api_connection(api_key, api_secret)
            
            log_info("API 키 검증 완료", {
                "user_id": user_id,
                "api_key_prefix": api_key[:8] + "...",
                "valid": validation_result['valid'],
                "permissions": validation_result.get('permissions', [])
            })
            
            return validation_result
            
        except HTTPException:
            raise
        except Exception as error:
            log_error("API 키 검증 실패", {
                "user_id": user_id,
                "api_key_prefix": api_key[:8] + "..." if api_key else None,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API 키 검증 중 오류가 발생했습니다."
            )
    
    async def _test_api_connection(
        self,
        api_key: str,
        api_secret: str
    ) -> Dict[str, Any]:
        """API 연결 테스트"""
        try:
            # 계정 정보 조회 API 호출 - UNIFIED 계정 타입 사용
            endpoint = "/v5/account/wallet-balance"
            params = {
                "accountType": "UNIFIED"
            }
            
            # 서명 생성
            timestamp = str(int(time.time() * 1000))
            signature = self._generate_signature(
                api_secret, timestamp, api_key, endpoint, params
            )
            
            headers = {
                "X-BAPI-API-KEY": api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": "5000",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    headers=headers
                )
                
                data = response.json()
                
                # API 응답 분석
                if data.get('retCode') == 0:
                    # 성공
                    return {
                        "valid": True,
                        "message": "API 키가 유효합니다.",
                        "permissions": ["spot"],  # 기본 권한
                        "account_info": {
                            "has_balance": bool(data.get('result', {}).get('list', [])),
                            "account_type": "SPOT"
                        }
                    }
                elif data.get('retCode') == 10003:
                    # 잘못된 API 키
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="API 키가 유효하지 않습니다."
                    )
                elif data.get('retCode') == 10004:
                    # 잘못된 서명
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="API 시크릿 키가 올바르지 않습니다."
                    )
                elif data.get('retCode') == 10006:
                    # 권한 없음
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="API 키에 필요한 권한이 없습니다. Spot Trading 권한을 확인해주세요."
                    )
                else:
                    # 기타 오류
                    error_msg = data.get('retMsg', '알 수 없는 오류')
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"API 키 검증 실패: {error_msg}"
                    )
                    
        except HTTPException:
            raise
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Bybit API 응답 시간이 초과되었습니다."
            )
        except httpx.HTTPError as http_error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bybit API 서버에 연결할 수 없습니다."
            )
        except Exception as error:
            log_error("API 연결 테스트 실패", {"error": str(error)})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API 연결 테스트 중 오류가 발생했습니다."
            )
    
    def _generate_signature(
        self,
        api_secret: str,
        timestamp: str,
        api_key: str,
        endpoint: str,
        params: Dict[str, Any]
    ) -> str:
        """Bybit API 서명 생성"""
        try:
            # 파라미터 정렬 및 쿼리 스트링 생성
            sorted_params = sorted(params.items())
            query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
            
            # 서명할 문자열 생성
            sign_string = timestamp + api_key + "5000" + query_string
            
            # HMAC-SHA256 서명 생성
            signature = hmac.new(
                api_secret.encode('utf-8'),
                sign_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as error:
            log_error("API 서명 생성 실패", {"error": str(error)})
            raise
    
    async def get_account_info(
        self,
        api_key: str,
        api_secret: str
    ) -> Dict[str, Any]:
        """계정 정보 조회 (추가 검증용)"""
        try:
            endpoint = "/v5/account/info"
            params = {}
            
            timestamp = str(int(time.time() * 1000))
            signature = self._generate_signature(
                api_secret, timestamp, api_key, endpoint, params
            )
            
            headers = {
                "X-BAPI-API-KEY": api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": "5000",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                )
                
                data = response.json()
                
                if data.get('retCode') == 0:
                    account_data = data.get('result', {})
                    return {
                        "uid": account_data.get('uid'),
                        "status": account_data.get('status'),
                        "unified_margin_status": account_data.get('unifiedMarginStatus'),
                        "dcpStatus": account_data.get('dcpStatus'),
                        "timeWindow": account_data.get('timeWindow')
                    }
                else:
                    raise Exception(f"계정 정보 조회 실패: {data.get('retMsg')}")
                    
        except Exception as error:
            log_error("계정 정보 조회 실패", {"error": str(error)})
            raise
    
    async def check_api_permissions(
        self,
        api_key: str,
        api_secret: str
    ) -> Dict[str, Any]:
        """API 권한 확인"""
        try:
            # 여러 엔드포인트를 테스트하여 권한 확인
            permissions = {
                "spot_read": False,
                "spot_trade": False,
                "account_read": False
            }
            
            # 1. 계정 정보 읽기 권한 테스트
            try:
                await self.get_account_info(api_key, api_secret)
                permissions["account_read"] = True
            except:
                pass
            
            # 2. Spot 잔고 읽기 권한 테스트
            try:
                await self._test_api_connection(api_key, api_secret)
                permissions["spot_read"] = True
            except:
                pass
            
            # 3. Spot 거래 권한은 실제 주문 없이는 확인하기 어려우므로
            # 계정 정보에서 추정
            if permissions["account_read"] and permissions["spot_read"]:
                permissions["spot_trade"] = True
            
            return {
                "permissions": permissions,
                "sufficient_for_trading": all([
                    permissions["spot_read"],
                    permissions["spot_trade"],
                    permissions["account_read"]
                ])
            }
            
        except Exception as error:
            log_error("API 권한 확인 실패", {"error": str(error)})
            return {
                "permissions": {
                    "spot_read": False,
                    "spot_trade": False,
                    "account_read": False
                },
                "sufficient_for_trading": False
            }