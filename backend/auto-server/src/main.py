import asyncio
import os
import sys
import signal
from dotenv import load_dotenv

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.scheduler_service import AutoTradingScheduler
from shared.database import test_connection, create_connection_pool
from shared.redis_client import test_redis_connection
from shared.utils import validate_env_vars, log_info, log_error

# 환경 변수 로드
load_dotenv()

class AutoTradingServer:
    """자동매매 서버"""
    
    def __init__(self):
        self.scheduler = AutoTradingScheduler()
        self.running = False
    
    async def start(self):
        """서버 시작"""
        try:
            log_info("자동매매 서버 시작")
            
            # 환경 변수 검증
            validate_env_vars()
            
            # 추가 환경 변수 확인
            required_vars = ['OPENAI_API_KEY']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
            
            # 데이터베이스 연결 테스트
            create_connection_pool()
            if not test_connection():
                raise Exception("데이터베이스 연결에 실패했습니다.")
            
            # Redis 연결 테스트
            if not test_redis_connection():
                raise Exception("Redis 연결에 실패했습니다.")
            
            log_info("자동매매 서버 초기화 완료")
            self.running = True
            
            # 스케줄러 시작
            await self.scheduler.start_scheduler()
            
        except Exception as error:
            log_error("자동매매 서버 시작 실패", {'error': str(error)})
            raise
    
    async def stop(self):
        """서버 종료"""
        log_info("자동매매 서버 종료 중...")
        self.running = False
        
        # 스케줄러 중지
        if self.scheduler:
            self.scheduler.stop_scheduler()
        
        # 정리 작업
        try:
            from shared.database import close_connection_pool
            from shared.redis_client import disconnect_redis
            
            close_connection_pool()
            disconnect_redis()
            
            log_info("자동매매 서버 종료 완료")
            
        except Exception as error:
            log_error("자동매매 서버 종료 중 오류", {'error': str(error)})

# 전역 서버 인스턴스
server = AutoTradingServer()

def signal_handler(signum, frame):
    """시그널 핸들러"""
    log_info(f"종료 신호 수신: {signum}")
    asyncio.create_task(server.stop())

async def main():
    """메인 함수"""
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        log_info("키보드 인터럽트로 서버 종료")
    except Exception as error:
        log_error("서버 실행 중 오류 발생", {'error': str(error)})
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())