import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Optional, Dict, Any
from datetime import datetime
from .bybit_api import BybitApiClient
from shared.redis_client import save_candle_data, get_candle_count, set_system_status
from shared.types import CandleData
from shared.utils import log_info, log_error

class DataCollector:
    """데이터 수집기 클래스"""
    
    def __init__(
        self,
        symbol: str = 'BTCUSDT',
        interval: str = '1',
        target_count: int = 5000,
        testnet: bool = False
    ):
        self.bybit_client = BybitApiClient(testnet)
        self.symbol = symbol
        self.interval = interval
        self.target_count = target_count
    
    async def collect_initial_data(self) -> None:
        """초기 데이터 수집"""
        try:
            log_info("초기 데이터 수집 시작", {
                'symbol': self.symbol,
                'interval': self.interval,
                'target_count': self.target_count
            })
            
            # 현재 Redis에 저장된 캔들 개수 확인
            current_count = get_candle_count(self.symbol, self.interval)
            
            if current_count >= self.target_count:
                log_info("이미 충분한 데이터가 존재합니다", {
                    'current_count': current_count,
                    'target_count': self.target_count
                })
                return
            
            # 부족한 데이터 수집
            need_count = self.target_count - current_count
            log_info(f"{need_count}개의 추가 데이터가 필요합니다")
            
            candles = await self.bybit_client.get_bulk_kline_data(
                self.symbol,
                self.interval,
                need_count
            )
            
            # Redis에 저장
            await self._save_candles(candles)
            
            # 시스템 상태 업데이트
            set_system_status('data_server_last_update', datetime.now().isoformat())
            set_system_status('initial_data_collected', 'true')
            
            log_info("초기 데이터 수집 완료", {
                'symbol': self.symbol,
                'interval': self.interval,
                'collected_count': len(candles),
                'total_count': get_candle_count(self.symbol, self.interval)
            })
            
        except Exception as error:
            log_error("초기 데이터 수집 실패", {
                'symbol': self.symbol,
                'interval': self.interval,
                'error': str(error)
            })
            raise
    
    async def _save_candles(self, candles: list[CandleData]) -> None:
        """캔들 데이터를 Redis에 저장"""
        try:
            log_info(f"{len(candles)}개의 캔들 데이터 저장 시작")
            
            # 배치 저장을 위해 역순으로 저장 (최신 데이터가 앞쪽에 오도록)
            reversed_candles = list(reversed(candles))
            
            for candle in reversed_candles:
                save_candle_data(self.symbol, self.interval, candle)
            
            log_info("캔들 데이터 저장 완료", {
                'count': len(candles),
                'symbol': self.symbol,
                'interval': self.interval
            })
            
        except Exception as error:
            log_error("캔들 데이터 저장 실패", {'error': str(error)})
            raise
    
    async def collect_latest_candle(self) -> Optional[CandleData]:
        """최신 캔들 데이터 수집 (1개)"""
        try:
            candles = await self.bybit_client.get_kline_data(
                self.symbol,
                self.interval,
                1
            )
            
            if not candles:
                log_info("최신 캔들 데이터가 없습니다")
                return None
            
            latest_candle = candles[0]
            
            # Redis에 저장
            save_candle_data(self.symbol, self.interval, latest_candle)
            
            log_info("최신 캔들 데이터 수집 완료", {
                'timestamp': datetime.fromtimestamp(latest_candle.timestamp / 1000).isoformat(),
                'close': latest_candle.close
            })
            
            return latest_candle
            
        except Exception as error:
            log_error("최신 캔들 데이터 수집 실패", {'error': str(error)})
            raise
    
    async def get_collection_status(self) -> Dict[str, Any]:
        """데이터 수집 상태 확인"""
        try:
            current_count = get_candle_count(self.symbol, self.interval)
            last_update = set_system_status('data_server_last_update', '')
            
            return {
                'symbol': self.symbol,
                'interval': self.interval,
                'current_count': current_count,
                'target_count': self.target_count,
                'is_complete': current_count >= self.target_count,
                'last_update': last_update if isinstance(last_update, str) else None
            }
            
        except Exception as error:
            log_error("데이터 수집 상태 확인 실패", {'error': str(error)})
            raise
    
    async def test_bybit_connection(self) -> bool:
        """Bybit API 연결 테스트"""
        return await self.bybit_client.test_connection()