import httpx
import asyncio
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.types import CandleData
from shared.utils import log_info, log_error, retry

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BybitApiClient:
    """Bybit REST API 클라이언트"""
    
    def __init__(self, testnet: bool = False):
        self.base_url = (
            os.getenv('BYBIT_TESTNET_URL', 'https://api-testnet.bybit.com')
            if testnet else
            os.getenv('BYBIT_API_URL', 'https://api.bybit.com')
        )
        self.timeout = 30.0
        
    async def get_kline_data(
        self,
        symbol: str = 'BTCUSDT',
        interval: str = '1',
        limit: int = 1000,
        start: Optional[int] = None,
        end: Optional[int] = None
    ) -> List[CandleData]:
        """Kline 데이터 조회"""
        try:
            params = {
                'category': 'spot',
                'symbol': symbol,
                'interval': interval,
                'limit': min(limit, 1000)  # Bybit 최대 1000개 제한
            }
            
            if start:
                params['start'] = start
            if end:
                params['end'] = end
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/v5/market/kline",
                    params=params,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'crypto-trading-system/1.0'
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                if data.get('retCode') != 0:
                    raise Exception(f"Bybit API 오류: {data.get('retMsg')}")
                
                # 캔들 데이터 변환
                candles = []
                for item in data['result']['list']:
                    candle = CandleData(
                        timestamp=int(item[0]),
                        open=item[1],
                        high=item[2],
                        low=item[3],
                        close=item[4],
                        volume=item[5]
                    )
                    candles.append(candle)
                
                # 타임스탬프 기준 오름차순 정렬
                candles.sort(key=lambda x: x.timestamp)
                
                log_info(f"Kline 데이터 조회 완료", {
                    'symbol': symbol,
                    'interval': interval,
                    'count': len(candles),
                    'start_time': datetime.fromtimestamp(candles[0].timestamp / 1000).isoformat() if candles else None,
                    'end_time': datetime.fromtimestamp(candles[-1].timestamp / 1000).isoformat() if candles else None
                })
                
                return candles
                
        except Exception as error:
            log_error(f"Kline 데이터 조회 실패", {
                'symbol': symbol,
                'interval': interval,
                'limit': limit,
                'error': str(error)
            })
            raise    async def get_bulk_kline_data(
        self,
        symbol: str = 'BTCUSDT',
        interval: str = '1',
        total_count: int = 5000
    ) -> List[CandleData]:
        """대량 Kline 데이터 조회 (5000개)"""
        try:
            log_info(f"대량 Kline 데이터 조회 시작", {
                'symbol': symbol,
                'interval': interval,
                'total_count': total_count
            })
            
            all_candles = []
            batch_size = 1000  # Bybit API 한 번에 최대 1000개
            end_time = int(datetime.now().timestamp() * 1000)  # 현재 시간부터 역순으로 조회
            
            while len(all_candles) < total_count:
                remaining_count = total_count - len(all_candles)
                current_batch_size = min(batch_size, remaining_count)
                
                # 재시도 로직 적용
                candles = await retry(
                    lambda: self.get_kline_data(symbol, interval, current_batch_size, None, end_time),
                    max_retries=3,
                    delay_seconds=1.0
                )
                
                if not candles:
                    log_info("더 이상 조회할 Kline 데이터가 없습니다.")
                    break
                
                # 중복 제거
                new_candles = [
                    candle for candle in candles
                    if not any(existing.timestamp == candle.timestamp for existing in all_candles)
                ]
                
                all_candles = new_candles + all_candles  # 앞쪽에 추가 (시간순 정렬 유지)
                
                # 다음 배치를 위해 end_time 업데이트
                if candles:
                    end_time = candles[0].timestamp - 1
                
                log_info(f"배치 조회 완료", {
                    'batch_size': len(new_candles),
                    'total_collected': len(all_candles),
                    'progress': f"{round((len(all_candles) / total_count) * 100)}%"
                })
                
                # API 레이트 리미트 방지
                await asyncio.sleep(0.1)
            
            # 최종 정렬 및 개수 제한
            all_candles.sort(key=lambda x: x.timestamp)
            result = all_candles[-total_count:] if len(all_candles) > total_count else all_candles
            
            log_info(f"대량 Kline 데이터 조회 완료", {
                'symbol': symbol,
                'interval': interval,
                'total_count': len(result),
                'start_time': datetime.fromtimestamp(result[0].timestamp / 1000).isoformat() if result else None,
                'end_time': datetime.fromtimestamp(result[-1].timestamp / 1000).isoformat() if result else None
            })
            
            return result
            
        except Exception as error:
            log_error(f"대량 Kline 데이터 조회 실패", {
                'symbol': symbol,
                'interval': interval,
                'total_count': total_count,
                'error': str(error)
            })
            raise
    
    async def get_server_time(self) -> int:
        """서버 시간 조회"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/v5/market/time")
                response.raise_for_status()
                data = response.json()
                
                if data.get('retCode') != 0:
                    raise Exception(f"Bybit API 오류: {data.get('retMsg')}")
                
                return int(data['result']['timeSecond']) * 1000  # 밀리초로 변환
                
        except Exception as error:
            log_error(f"Bybit 서버 시간 조회 실패: {error}")
            raise
    
    async def test_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            await self.get_server_time()
            log_info("Bybit API 연결 테스트 성공")
            return True
        except Exception as error:
            log_error(f"Bybit API 연결 테스트 실패: {error}")
            return False
    
    async def get_symbol_info(self, symbol: str = 'BTCUSDT') -> Dict[str, Any]:
        """심볼 정보 조회"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/v5/market/instruments-info",
                    params={
                        'category': 'spot',
                        'symbol': symbol
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                if data.get('retCode') != 0:
                    raise Exception(f"Bybit API 오류: {data.get('retMsg')}")
                
                return data['result']['list'][0] if data['result']['list'] else {}
                
        except Exception as error:
            log_error(f"심볼 정보 조회 실패", {
                'symbol': symbol,
                'error': str(error)
            })
            raise