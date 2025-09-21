import os
import re
import time
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import hashlib
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 암호화 키 생성/로드
def get_encryption_key() -> bytes:
    """암호화 키 가져오기"""
    key_str = os.getenv('ENCRYPTION_KEY', 'default-32-character-key-for-dev')
    # 32바이트 키로 변환
    key_bytes = hashlib.sha256(key_str.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)

# 암호화 객체
fernet = Fernet(get_encryption_key())

def encrypt(text: str) -> str:
    """텍스트 암호화"""
    try:
        encrypted_bytes = fernet.encrypt(text.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    except Exception as error:
        logger.error(f"암호화 오류: {error}")
        raise ValueError("데이터 암호화에 실패했습니다.")

def decrypt(encrypted_text: str) -> str:
    """텍스트 복호화"""
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
    except Exception as error:
        logger.error(f"복호화 오류: {error}")
        raise ValueError("데이터 복호화에 실패했습니다.")

def mask_api_key(api_key: str) -> str:
    """API 키 마스킹"""
    if not api_key or len(api_key) < 8:
        return "****"
    
    start = api_key[:4]
    end = api_key[-4:]
    middle = "*" * (len(api_key) - 8)
    return f"{start}{middle}{end}"

def is_valid_email(email: str) -> bool:
    """이메일 유효성 검증"""
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(email_regex, email) is not None

def is_valid_password(password: str) -> bool:
    """비밀번호 강도 검증 (최소 8자, 대소문자, 숫자 포함)"""
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$'
    return re.match(password_regex, password) is not None

def is_valid_leverage(leverage: int) -> bool:
    """레버리지 유효성 검증"""
    return 1 <= leverage <= 100 and isinstance(leverage, int)

def is_valid_risk_level(risk_level: str) -> bool:
    """위험도 레벨 유효성 검증"""
    return risk_level in ['low', 'medium', 'high']

def timestamp_to_iso_string(timestamp: int) -> str:
    """타임스탬프를 ISO 문자열로 변환"""
    return datetime.fromtimestamp(timestamp / 1000).isoformat()

def iso_string_to_timestamp(iso_string: str) -> int:
    """ISO 문자열을 타임스탬프로 변환"""
    return int(datetime.fromisoformat(iso_string).timestamp() * 1000)

def round_to_decimals(num: float, decimals: int) -> float:
    """숫자를 소수점 자리수로 반올림"""
    return round(num, decimals)

def calculate_percentage(value: float, total: float) -> float:
    """퍼센트 계산"""
    if total == 0:
        return 0.0
    return round_to_decimals((value / total) * 100, 2)

async def delay(seconds: float) -> None:
    """비동기 지연 함수"""
    import asyncio
    await asyncio.sleep(seconds)

async def retry(func, max_retries: int = 3, delay_seconds: float = 1.0):
    """재시도 로직 (비동기)"""
    import asyncio
    
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except Exception as error:
            last_error = error
            
            if attempt == max_retries:
                raise last_error
            
            logger.warning(f"재시도 {attempt + 1}/{max_retries}: {error}")
            await asyncio.sleep(delay_seconds * (2 ** attempt))  # 지수 백오프
    
    raise last_error

def validate_env_vars() -> None:
    """환경 변수 검증"""
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'JWT_SECRET',
        'ENCRYPTION_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")

def log_info(message: str, meta: Optional[Dict[str, Any]] = None) -> None:
    """정보 로그"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': 'INFO',
        'message': message,
        **(meta or {})
    }
    logger.info(log_entry)

def log_error(message: str, meta: Optional[Dict[str, Any]] = None) -> None:
    """오류 로그"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': 'ERROR',
        'message': message,
        **(meta or {})
    }
    logger.error(log_entry)

def log_warning(message: str, meta: Optional[Dict[str, Any]] = None) -> None:
    """경고 로그"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': 'WARNING',
        'message': message,
        **(meta or {})
    }
    logger.warning(log_entry)

def create_api_response(
    success: bool,
    data: Any = None,
    message: Optional[str] = None,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """API 응답 생성 헬퍼"""
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error
    
    return response