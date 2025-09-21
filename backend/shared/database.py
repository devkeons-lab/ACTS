import mysql.connector
from mysql.connector import pooling
import os
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'crypto_user'),
    'password': os.getenv('DB_PASSWORD', 'crypto_password'),
    'database': os.getenv('DB_NAME', 'crypto_trading'),
    'pool_name': 'crypto_trading_pool',
    'pool_size': 10,
    'pool_reset_session': True,
    'autocommit': True
}

# 연결 풀 생성
connection_pool = None

def create_connection_pool():
    """데이터베이스 연결 풀 생성"""
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(**DB_CONFIG)
        logger.info("✅ MySQL 연결 풀 생성 성공")
        return True
    except mysql.connector.Error as error:
        logger.error(f"❌ MySQL 연결 풀 생성 실패: {error}")
        return False

def get_connection():
    """연결 풀에서 연결 가져오기"""
    global connection_pool
    if connection_pool is None:
        create_connection_pool()
    
    try:
        return connection_pool.get_connection()
    except mysql.connector.Error as error:
        logger.error(f"데이터베이스 연결 가져오기 실패: {error}")
        raise

def test_connection() -> bool:
    """데이터베이스 연결 테스트"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        logger.info("✅ MySQL 데이터베이스 연결 테스트 성공")
        return True
    except mysql.connector.Error as error:
        logger.error(f"❌ MySQL 데이터베이스 연결 테스트 실패: {error}")
        return False

def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """쿼리 실행 (SELECT)"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as error:
        logger.error(f"쿼리 실행 오류: {error}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_query_single(query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
    """단일 행 조회"""
    result = execute_query(query, params)
    return result[0] if result else None

def execute_insert(query: str, params: Optional[tuple] = None) -> int:
    """INSERT 쿼리 실행 후 ID 반환"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as error:
        logger.error(f"INSERT 쿼리 실행 오류: {error}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """UPDATE/DELETE 쿼리 실행 후 영향받은 행 수 반환"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as error:
        logger.error(f"UPDATE/DELETE 쿼리 실행 오류: {error}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_transaction(queries: List[Dict[str, Any]]) -> None:
    """트랜잭션 실행"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 자동 커밋 비활성화
        conn.autocommit = False
        
        for query_info in queries:
            query = query_info['query']
            params = query_info.get('params')
            cursor.execute(query, params)
        
        conn.commit()
        logger.info("트랜잭션 실행 성공")
        
    except mysql.connector.Error as error:
        logger.error(f"트랜잭션 실행 오류: {error}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.autocommit = True
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def close_connection_pool():
    """연결 풀 종료"""
    global connection_pool
    if connection_pool:
        # 연결 풀의 모든 연결 종료
        logger.info("MySQL 연결 풀이 종료되었습니다.")
        connection_pool = None