import asyncio
import json
import os
import sys
import websockets
from typing import Optional, Dict, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.redis_client import save_candle_data, set_system_status
from shared.types import CandleData
from shared.utils import log_info, log_error, log_warning

class BybitWebSocketClient:
    """Bybit WebSocket 클라이언트"""
    
    def __init__(
        self,
        symbol: str = 'BTCUSDT',
        interval: str = '1',
        testnet: bool = False
    ):
        self.symbol = symbol
        self.interval = interval
        self.url = (
            'wss://stream-testnet.bybit.com/v5/public/spot'
            if testnet else
            'wss://stream.bybit.com/v5/public/spot'
        )
        self.websocket = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5.0
        self.is_connecting = False
        self.ping_task = None
        self.running = False
    
    async def connect(self) -> None:
        """WebSocket 연결"""
        if self.is_connecting or (self.websocket and not self.websocket.closed):
            return
        
        self.is_connecting = True
        
        try:
            log_info("Bybit WebSocket 연결 시도", {
                'url': self.url,
                'symbol': self.symbol,
                'interval': self.interval
            })
            
            self.websocket = await websockets.connect(
                self.url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            log_info("Bybit WebSocket 연결 성공")
            self.is_connecting = False
            self.reconnect_attempts = 0
            self.running = True
            
            # 구독 요청
            await self._subscribe()
            
            # Ping 작업 시작
            self._start_ping()
            
            # 시스템 상태 업데이트
            await self._update_system_status('connected')
            
            # 메시지 수신 루프
            await self._message_loop()
            
        except Exception as error:
            log_error("Bybit WebSocket 연결 실패", {'error': str(error)})
            self.is_connecting = False
            await self._update_system_status('error')
            await self._schedule_reconnect()
    
    async def _subscribe(self) -> None:
        """구독 요청"""
        if not self.websocket or self.websocket.closed:
            return
        
        subscribe_message = {
            'op': 'subscribe',
            'args': [f'kline.{self.interval}.{self.symbol}']
        }
        
        await self.websocket.send(json.dumps(subscribe_message))
        
        log_info("Bybit WebSocket 구독 요청", {
            'topic': f'kline.{self.interval}.{self.symbol}'
        })
    
    async def _message_loop(self) -> None:
        """메시지 수신 루프"""
        try:
            async for message in self.websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            log_warning("WebSocket 연결이 종료되었습니다")
            await self._update_system_status('disconnected')
            await self._schedule_reconnect()
        except Exception as error:
            log_error("WebSocket 메시지 루프 오류", {'error': str(error)})
            await self._update_system_status('error')
            await self._schedule_reconnect()
    
    async def _handle_message(self, message: str) -> None:
        """메시지 처리"""
        try:
            data = json.loads(message)
            
            # 구독 확인 메시지
            if data.get('op') == 'subscribe' and data.get('success'):
                log_info("Bybit WebSocket 구독 성공", {
                    'ret_msg': data.get('ret_msg')
                })
                return
            
            # Kline 데이터 메시지
            if data.get('topic') and data['topic'].startswith('kline.'):
                await self._process_kline_data(data)
                return
            
            # Pong 응답
            if data.get('op') == 'pong':
                log_info("Bybit WebSocket pong 수신")
                return
                
        except json.JSONDecodeError as error:
            log_error("WebSocket 메시지 JSON 파싱 오류", {
                'error': str(error),
                'message': message
            })
        except Exception as error:
            log_error("WebSocket 메시지 처리 오류", {
                'error': str(error),
                'message': message
            })
    
    async def _process_kline_data(self, message: Dict[str, Any]) -> None:
        """Kline 데이터 처리"""
        try:
            if not message.get('data'):
                return
            
            for kline_data in message['data']:
                # 확정된 캔들만 저장 (confirm: true)
                if not kline_data.get('confirm', False):
                    continue
                
                candle = CandleData(
                    timestamp=kline_data['start'],
                    open=kline_data['open'],
                    high=kline_data['high'],
                    low=kline_data['low'],
                    close=kline_data['close'],
                    volume=kline_data['volume']
                )
                
                # Redis에 저장
                save_candle_data(self.symbol, self.interval, candle)
                
                log_info("실시간 캔들 데이터 저장", {
                    'symbol': self.symbol,
                    'timestamp': datetime.fromtimestamp(candle.timestamp / 1000).isoformat(),
                    'close': candle.close,
                    'volume': candle.volume
                })
            
            # 시스템 상태 업데이트
            await self._update_system_status('active')
            
        except Exception as error:
            log_error("Kline 데이터 처리 오류", {'error': str(error)})
    
    def _start_ping(self) -> None:
        """Ping 작업 시작"""
        async def ping_loop():
            while self.running and self.websocket and not self.websocket.closed:
                try:
                    ping_message = {'op': 'ping'}
                    await self.websocket.send(json.dumps(ping_message))
                    log_info("Bybit WebSocket ping 전송")
                    await asyncio.sleep(20)  # 20초마다 ping
                except Exception as error:
                    log_error("Ping 전송 오류", {'error': str(error)})
                    break
        
        self.ping_task = asyncio.create_task(ping_loop())
    
    def _stop_ping(self) -> None:
        """Ping 작업 중지"""
        if self.ping_task and not self.ping_task.done():
            self.ping_task.cancel()
    
    async def _schedule_reconnect(self) -> None:
        """재연결 스케줄링"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            log_error("WebSocket 최대 재연결 시도 횟수 초과", {
                'attempts': self.reconnect_attempts
            })
            return
        
        self.reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))  # 지수 백오프
        
        log_info("WebSocket 재연결 예정", {
            'attempt': self.reconnect_attempts,
            'delay': f"{delay}초"
        })
        
        await asyncio.sleep(delay)
        await self.connect()
    
    async def _update_system_status(self, status: str) -> None:
        """시스템 상태 업데이트"""
        try:
            set_system_status('websocket_status', status)
            set_system_status('websocket_last_update', datetime.now().isoformat())
        except Exception as error:
            log_error("시스템 상태 업데이트 실패", {'error': str(error)})
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.websocket is not None and not self.websocket.closed
    
    async def disconnect(self) -> None:
        """연결 종료"""
        self.running = False
        self._stop_ping()
        
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        
        log_info("Bybit WebSocket 연결 종료")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """연결 상태 정보"""
        return {
            'connected': self.is_connected(),
            'reconnect_attempts': self.reconnect_attempts,
            'symbol': self.symbol,
            'interval': self.interval,
            'running': self.running
        }