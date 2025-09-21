import asyncio
import os
import sys
import signal
from dotenv import load_dotenv

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.data_collector import DataCollector
from services.websocket_client import BybitWebSocketClient
from shared.redis_client import test_redis_connection
from shared.utils import validate_env_vars, log_info, log_error

# 환경 변수 로드
load_dotenv()

class DataServer:
    """데이터 수집 서버"""
    
    def __init__(self):
        self.collector = None
        self.websocket_client = None
        self.running = False
    
    async def start(self):
        """서버 시작"""
        try:
            log_info("데이터 수집 서버 시작")
            
            # 환경 변수 검증
            validate_env_vars()
            
            # Redis 연결 테스트
            redis_connected = test_redis_connection()
            if not redis_connected:
                raise Exception("Redis 연결에 실패했습니다.")
            
            # 데이터 수집기 초기화
            self.collector = DataCollector(
                'BTCUSDT',
                '1',
                5000,
                os.getenv('NODE_ENV') == 'development'
            )
            
            # Bybit API 연결 테스트
            bybit_connected = await self.collector.test_bybit_connection()
            if not bybit_connected:
                raise Exception("Bybit API 연결에 실패했습니다.")
            
            # 초기 데이터 수집
            await self.collector.collect_initial_data()
            
            # 수집 상태 확인
            status = await self.collector.get_collection_status()
            log_info("데이터 수집 상태", status)
            
            # WebSocket 클라이언트 초기화 및 연결
            self.websocket_client = BybitWebSocketClient(
                'BTCUSDT',
                '1',
                os.getenv('NODE_ENV') == 'development'
            )
            
            log_info("데이터 수집 서버 초기화 완료")
            self.running = True
            
            # WebSocket 연결과 서버 실행을 동시에 시작
            await asyncio.gather(
                self.websocket_client.connect(),
                self._keep_running()
            )
            
        except Exception as error:
            log_error("데이터 수집 서버 시작 실패", {'error': str(error)})
            raise
    
    async def _keep_running(self):
        """서버 실행 유지"""
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            log_info("서버 종료 신호 수신")
        finally:
            await self.stop()
    
    async def stop(self):
        """서버 종료"""
        log_info("데이터 수집 서버 종료 중...")
        self.running = False
        
        # 정리 작업
        if self.websocket_client:
            await self.websocket_client.disconnect()
        
        if self.collector:
            # 필요한 정리 작업 수행
            pass
        
        log_info("데이터 수집 서버 종료 완료")

# 전역 서버 인스턴스
server = DataServer()

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