import redis
import json
import os
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv
from .types import CandleData

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis 클라이언트
redis_client = None

def connect_redis():
    """Redis 연결"""
    global redis_client
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # 연결 테스트
        redis_client.ping()
        logger.info("✅ Redis 연결 성공")
        return redis_client
        
    except redis.RedisError as error:
        logger.error(f"❌ Redis 연결 실패: {error}")
        raise

def get_redis_client():
    """Redis 클라이언트 가져오기"""
    global redis_client
    if redis_client is None:
        connect_redis()
    return redis_client

def test_redis_connection() -> bool:
    """Redis 연결 테스트"""
    try:
        client = get_redis_client()
        client.ping()
        logger.info("✅ Redis 연결 테스트 성공")
        return True
    except redis.RedisError as error:
        logger.error(f"❌ Redis 연결 테스트 실패: {error}")
        return False

def save_candle_data(symbol: str, interval: str, candle: CandleData) -> None:
    """캔들 데이터 저장 (LPUSH + LTRIM)"""
    try:
        client = get_redis_client()
        key = f"kline:{symbol}:{interval}"
        candle_json = candle.model_dump_json()
        
        # 새로운 캔들을 리스트 앞쪽에 추가
        client.lpush(key, candle_json)
        
        # 최신 5000개만 유지
        client.ltrim(key, 0, 4999)
        
        logger.info(f"캔들 데이터 저장 완료: {symbol} {interval} at {candle.timestamp}")
        
    except redis.RedisError as error:
        logger.error(f"캔들 데이터 저장 오류: {error}")
        raise

def get_candle_data(symbol: str, interval: str, count: int = 30) -> List[CandleData]:
    """캔들 데이터 조회 (LRANGE)"""
    try:
        client = get_redis_client()
        key = f"kline:{symbol}:{interval}"
        
        # 최신 count개 캔들 조회
        candle_strings = client.lrange(key, 0, count - 1)
        
        candles = []
        for candle_str in candle_strings:
            try:
                candle_dict = json.loads(candle_str)
                candle = CandleData(**candle_dict)
                candles.append(candle)
            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.error(f"캔들 데이터 파싱 오류: {parse_error}")
                continue
        
        logger.info(f"캔들 데이터 조회 완료: {symbol} {interval} {len(candles)}개")
        return candles
        
    except redis.RedisError as error:
        logger.error(f"캔들 데이터 조회 오류: {error}")
        raise

def get_candle_count(symbol: str, interval: str) -> int:
    """캔들 데이터 개수 확인"""
    try:
        client = get_redis_client()
        key = f"kline:{symbol}:{interval}"
        count = client.llen(key)
        return count
    except redis.RedisError as error:
        logger.error(f"캔들 데이터 개수 조회 오류: {error}")
        raise

def set_system_status(key: str, value: str) -> None:
    """시스템 상태 저장"""
    try:
        client = get_redis_client()
        client.hset('system:status', key, value)
    except redis.RedisError as error:
        logger.error(f"시스템 상태 저장 오류: {error}")
        raise

def get_system_status(key: Optional[str] = None) -> Optional[str] | Dict[str, str]:
    """시스템 상태 조회"""
    try:
        client = get_redis_client()
        
        if key:
            return client.hget('system:status', key)
        else:
            return client.hgetall('system:status')
            
    except redis.RedisError as error:
        logger.error(f"시스템 상태 조회 오류: {error}")
        raise

def delete_key(key: str) -> None:
    """Redis 키 삭제"""
    try:
        client = get_redis_client()
        client.delete(key)
        logger.info(f"Redis 키 삭제 완료: {key}")
    except redis.RedisError as error:
        logger.error(f"Redis 키 삭제 오류: {error}")
        raise

def get_redis_info() -> str:
    """Redis 메모리 사용량 조회"""
    try:
        client = get_redis_client()
        return client.info('memory')
    except redis.RedisError as error:
        logger.error(f"Redis 정보 조회 오류: {error}")
        raise

def disconnect_redis() -> None:
    """Redis 연결 종료"""
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None
        logger.info("Redis 연결이 종료되었습니다.")