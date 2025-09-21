import os
import sys
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.database import execute_query_single, execute_insert, execute_update
from shared.types import User
from shared.utils import is_valid_email, is_valid_password, log_info, log_error

class AuthService:
    """인증 서비스"""
    
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key')
        self.jwt_algorithm = 'HS256'
        self.jwt_expiration_hours = 24
    
    async def register_user(self, email: str, password: str) -> Dict[str, Any]:
        """사용자 회원가입"""
        try:
            # 이메일 유효성 검증
            if not is_valid_email(email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효하지 않은 이메일 형식입니다."
                )
            
            # 비밀번호 강도 검증
            if not is_valid_password(password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="비밀번호는 최소 8자 이상이며, 대소문자와 숫자를 포함해야 합니다."
                )
            
            # 이메일 중복 확인
            existing_user = execute_query_single(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 등록된 이메일입니다."
                )
            
            # 비밀번호 해싱
            password_hash = self._hash_password(password)
            
            # 사용자 생성
            user_id = execute_insert(
                """
                INSERT INTO users (email, password_hash, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
                """,
                (email, password_hash)
            )
            
            log_info("새 사용자 등록", {
                "user_id": user_id,
                "email": email
            })
            
            return {
                "user_id": user_id,
                "email": email,
                "message": "회원가입이 완료되었습니다."
            }
            
        except HTTPException:
            raise
        except Exception as error:
            log_error("사용자 등록 실패", {
                "email": email,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="회원가입 처리 중 오류가 발생했습니다."
            )
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """사용자 로그인"""
        try:
            # 사용자 조회
            user_data = execute_query_single(
                """
                SELECT id, email, password_hash, auto_trade_enabled, risk_level, max_leverage
                FROM users WHERE email = %s
                """,
                (email,)
            )
            
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 올바르지 않습니다."
                )
            
            # 비밀번호 검증
            if not self._verify_password(password, user_data['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 올바르지 않습니다."
                )
            
            # JWT 토큰 생성
            token = self._create_jwt_token(user_data['id'], user_data['email'])
            
            log_info("사용자 로그인", {
                "user_id": user_data['id'],
                "email": user_data['email']
            })
            
            return {
                "token": token,
                "user": {
                    "id": user_data['id'],
                    "email": user_data['email'],
                    "auto_trade_enabled": user_data['auto_trade_enabled'],
                    "risk_level": user_data['risk_level'],
                    "max_leverage": user_data['max_leverage']
                },
                "message": "로그인이 완료되었습니다."
            }
            
        except HTTPException:
            raise
        except Exception as error:
            log_error("사용자 로그인 실패", {
                "email": email,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="로그인 처리 중 오류가 발생했습니다."
            )    asyn
c def verify_token(self, token: str) -> Dict[str, Any]:
        """JWT 토큰 검증"""
        try:
            # 토큰 디코딩
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            user_id = payload.get('user_id')
            email = payload.get('email')
            
            if not user_id or not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 토큰입니다."
                )
            
            # 사용자 존재 확인
            user_data = execute_query_single(
                """
                SELECT id, email, auto_trade_enabled, risk_level, max_leverage,
                       bybit_api_key IS NOT NULL as has_api_key
                FROM users WHERE id = %s AND email = %s
                """,
                (user_id, email)
            )
            
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            return {
                "user_id": user_data['id'],
                "email": user_data['email'],
                "auto_trade_enabled": user_data['auto_trade_enabled'],
                "risk_level": user_data['risk_level'],
                "max_leverage": user_data['max_leverage'],
                "has_api_key": user_data['has_api_key']
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 만료되었습니다."
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다."
            )
        except HTTPException:
            raise
        except Exception as error:
            log_error("토큰 검증 실패", {"error": str(error)})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰 검증 중 오류가 발생했습니다."
            )
    
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """사용자 프로필 조회"""
        try:
            user_data = execute_query_single(
                """
                SELECT id, email, auto_trade_enabled, risk_level, max_leverage,
                       custom_prompt, created_at, updated_at,
                       bybit_api_key IS NOT NULL as has_api_key
                FROM users WHERE id = %s
                """,
                (user_id,)
            )
            
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            return {
                "id": user_data['id'],
                "email": user_data['email'],
                "auto_trade_enabled": user_data['auto_trade_enabled'],
                "risk_level": user_data['risk_level'],
                "max_leverage": user_data['max_leverage'],
                "custom_prompt": user_data['custom_prompt'],
                "has_api_key": user_data['has_api_key'],
                "created_at": user_data['created_at'].isoformat(),
                "updated_at": user_data['updated_at'].isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as error:
            log_error("사용자 프로필 조회 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 정보 조회 중 오류가 발생했습니다."
            )
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해싱"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def _create_jwt_token(self, user_id: int, email: str) -> str:
        """JWT 토큰 생성"""
        payload = {
            'user_id': user_id,
            'email': email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)