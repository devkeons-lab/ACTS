import os
import sys
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.database import execute_query_single, execute_update
from shared.utils import encrypt, decrypt, mask_api_key, log_info, log_error

class ApiKeyService:
    """API 키 관리 서비스"""
    
    async def save_api_key(
        self,
        user_id: int,
        api_key: str,
        api_secret: str
    ) -> Dict[str, Any]:
        """API 키 저장"""
        try:
            # API 키 유효성 기본 검증
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
            
            # API 키 암호화
            encrypted_api_key = encrypt(api_key)
            encrypted_api_secret = encrypt(api_secret)
            
            # 데이터베이스에 저장
            affected_rows = execute_update(
                """
                UPDATE users 
                SET bybit_api_key = %s, bybit_api_secret = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (encrypted_api_key, encrypted_api_secret, user_id)
            )
            
            if affected_rows == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            log_info("API 키 저장 완료", {
                "user_id": user_id,
                "api_key_masked": mask_api_key(api_key)
            })
            
            return {
                "message": "API 키가 안전하게 저장되었습니다.",
                "api_key_masked": mask_api_key(api_key),
                "saved_at": "now"
            }
            
        except HTTPException:
            raise
        except Exception as error:
            log_error("API 키 저장 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API 키 저장 중 오류가 발생했습니다."
            )
    
    async def get_api_key(self, user_id: int, masked: bool = True) -> Optional[Dict[str, Any]]:
        """API 키 조회"""
        try:
            user_data = execute_query_single(
                """
                SELECT bybit_api_key, bybit_api_secret, updated_at
                FROM users WHERE id = %s
                """,
                (user_id,)
            )
            
            if not user_data or not user_data['bybit_api_key']:
                return None
            
            if masked:
                # 마스킹된 API 키 반환
                try:
                    decrypted_api_key = decrypt(user_data['bybit_api_key'])
                    return {
                        "api_key_masked": mask_api_key(decrypted_api_key),
                        "has_api_secret": bool(user_data['bybit_api_secret']),
                        "updated_at": user_data['updated_at'].isoformat()
                    }
                except Exception:
                    # 복호화 실패 시 (키가 손상된 경우)
                    return {
                        "api_key_masked": "****",
                        "has_api_secret": False,
                        "updated_at": user_data['updated_at'].isoformat(),
                        "error": "API 키가 손상되었습니다. 다시 등록해주세요."
                    }
            else:
                # 실제 API 키 반환 (내부 사용)
                try:
                    decrypted_api_key = decrypt(user_data['bybit_api_key'])
                    decrypted_api_secret = decrypt(user_data['bybit_api_secret'])
                    
                    return {
                        "api_key": decrypted_api_key,
                        "api_secret": decrypted_api_secret,
                        "updated_at": user_data['updated_at'].isoformat()
                    }
                except Exception as error:
                    log_error("API 키 복호화 실패", {
                        "user_id": user_id,
                        "error": str(error)
                    })
                    return None
                    
        except Exception as error:
            log_error("API 키 조회 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API 키 조회 중 오류가 발생했습니다."
            ) 
   async def update_api_key(
        self,
        user_id: int,
        api_key: str,
        api_secret: str
    ) -> Dict[str, Any]:
        """API 키 수정"""
        return await self.save_api_key(user_id, api_key, api_secret)
    
    async def delete_api_key(self, user_id: int) -> Dict[str, Any]:
        """API 키 삭제"""
        try:
            affected_rows = execute_update(
                """
                UPDATE users 
                SET bybit_api_key = NULL, bybit_api_secret = NULL, updated_at = NOW()
                WHERE id = %s
                """,
                (user_id,)
            )
            
            if affected_rows == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            log_info("API 키 삭제 완료", {"user_id": user_id})
            
            return {
                "message": "API 키가 삭제되었습니다.",
                "deleted_at": "now"
            }
            
        except HTTPException:
            raise
        except Exception as error:
            log_error("API 키 삭제 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API 키 삭제 중 오류가 발생했습니다."
            )
    
    async def has_api_key(self, user_id: int) -> bool:
        """API 키 존재 여부 확인"""
        try:
            user_data = execute_query_single(
                "SELECT bybit_api_key FROM users WHERE id = %s",
                (user_id,)
            )
            
            return bool(user_data and user_data['bybit_api_key'])
            
        except Exception as error:
            log_error("API 키 존재 여부 확인 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            return False
    
    async def get_users_with_api_keys(self, auto_trade_only: bool = True) -> list[Dict[str, Any]]:
        """API 키가 있는 사용자 목록 조회 (자동매매 서버용)"""
        try:
            query = """
                SELECT id, email, bybit_api_key, bybit_api_secret, 
                       risk_level, max_leverage, custom_prompt
                FROM users 
                WHERE bybit_api_key IS NOT NULL AND bybit_api_secret IS NOT NULL
            """
            
            if auto_trade_only:
                query += " AND auto_trade_enabled = TRUE"
            
            users_data = execute_query(query)
            
            result = []
            for user_data in users_data:
                try:
                    # API 키 복호화
                    decrypted_api_key = decrypt(user_data['bybit_api_key'])
                    decrypted_api_secret = decrypt(user_data['bybit_api_secret'])
                    
                    result.append({
                        "user_id": user_data['id'],
                        "email": user_data['email'],
                        "api_key": decrypted_api_key,
                        "api_secret": decrypted_api_secret,
                        "risk_level": user_data['risk_level'],
                        "max_leverage": user_data['max_leverage'],
                        "custom_prompt": user_data['custom_prompt']
                    })
                    
                except Exception as decrypt_error:
                    log_error("사용자 API 키 복호화 실패", {
                        "user_id": user_data['id'],
                        "error": str(decrypt_error)
                    })
                    continue
            
            log_info("API 키 보유 사용자 조회 완료", {
                "total_users": len(result),
                "auto_trade_only": auto_trade_only
            })
            
            return result
            
        except Exception as error:
            log_error("API 키 보유 사용자 조회 실패", {
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 목록 조회 중 오류가 발생했습니다."
            )