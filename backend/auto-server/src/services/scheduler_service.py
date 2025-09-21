import asyncio
import schedule
import time
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.redis_client import get_candle_data, set_system_status
from shared.database import execute_query
from shared.utils import log_info, log_error, decrypt
from .gpt_service import GPTAnalysisService
from .trading_service import BybitTradingService

class AutoTradingScheduler:
    """자동매매 스케줄러"""
    
    def __init__(self):
        self.gpt_service = GPTAnalysisService()
        self.trading_service = BybitTradingService(testnet=os.getenv('NODE_ENV') == 'development')
        self.is_running = False
        self.last_execution = None
        
    async def start_scheduler(self):
        """스케줄러 시작"""
        try:
            log_info("자동매매 스케줄러 시작")
            
            # 5분마다 실행 스케줄 등록
            schedule.every(5).minutes.do(self._schedule_trading_job)
            
            # 테스트용: 시작 시 한 번 실행 (개발 환경에서만)
            if os.getenv('NODE_ENV') == 'development':
                log_info("개발 환경: 즉시 한 번 실행")
                await self.execute_trading_cycle()
            
            self.is_running = True
            
            # 스케줄러 실행 루프
            while self.is_running:
                schedule.run_pending()
                await asyncio.sleep(1)  # 1초마다 스케줄 확인
                
        except Exception as error:
            log_error("스케줄러 실행 중 오류", {"error": str(error)})
            raise
    
    def _schedule_trading_job(self):
        """스케줄된 거래 작업 (동기 함수)"""
        # 비동기 함수를 동기 환경에서 실행
        asyncio.create_task(self.execute_trading_cycle())
    
    async def execute_trading_cycle(self):
        """거래 사이클 실행"""
        try:
            execution_start = datetime.now()
            log_info("자동매매 사이클 시작", {
                "execution_time": execution_start.isoformat()
            })
            
            # 1. 활성 사용자 조회
            active_users = await self._get_active_users()
            if not active_users:
                log_info("활성 사용자 없음 - 거래 사이클 완료")
                return
            
            log_info("거래 사이클 정보", {
                "active_users": len(active_users)
            })
            
            # 2. 각 사용자별 분석 및 거래 실행
            successful_trades = 0
            failed_trades = 0
            
            for user in active_users:
                try:
                    # 사용자별 선호 심볼의 캔들 데이터 조회
                    user_symbol = user['preferred_symbol']
                    user_interval = user['preferred_interval']
                    
                    candles = await self._get_latest_candles(user_symbol, user_interval)
                    if not candles:
                        log_error("캔들 데이터가 없어 거래를 건너뜁니다", {
                            "user_id": user['id'],
                            "symbol": user_symbol,
                            "interval": user_interval
                        })
                        failed_trades += 1
                        continue
                    
                    result = await self._process_user_trading(user, candles)
                    if result['success']:
                        successful_trades += 1
                    else:
                        failed_trades += 1
                        
                except Exception as user_error:
                    log_error("사용자 거래 처리 실패", {
                        "user_id": user.get('id'),
                        "error": str(user_error)
                    })
                    failed_trades += 1
            
            # 4. 실행 결과 기록
            execution_end = datetime.now()
            execution_time = (execution_end - execution_start).total_seconds()
            
            await self._record_execution_result({
                "execution_start": execution_start.isoformat(),
                "execution_end": execution_end.isoformat(),
                "execution_time": execution_time,
                "candles_analyzed": "per_user",
                "users_processed": len(active_users),
                "successful_trades": successful_trades,
                "failed_trades": failed_trades
            })
            
            self.last_execution = execution_end
            
            log_info("자동매매 사이클 완료", {
                "execution_time": f"{execution_time:.2f}초",
                "successful_trades": successful_trades,
                "failed_trades": failed_trades
            })
            
        except Exception as error:
            log_error("거래 사이클 실행 실패", {"error": str(error)})
            
            # 오류 상태 기록
            await self._record_execution_result({
                "execution_time": datetime.now().isoformat(),
                "error": str(error),
                "status": "failed"
            })
    
    async def _get_latest_candles(self, symbol: str = 'BTCUSDT', interval: str = '1') -> List:
        """최신 캔들 데이터 조회"""
        try:
            candles = get_candle_data(symbol, interval, 30)
            
            if not candles:
                log_error("Redis에서 캔들 데이터 조회 실패", {
                    "symbol": symbol,
                    "interval": interval
                })
                return []
            
            log_info("캔들 데이터 조회 성공", {
                "symbol": symbol,
                "interval": interval,
                "count": len(candles),
                "latest_timestamp": candles[0].timestamp if candles else None
            })
            
            return candles
            
        except Exception as error:
            log_error("캔들 데이터 조회 실패", {
                "symbol": symbol,
                "interval": interval,
                "error": str(error)
            })
            return []
    
    async def _get_active_users(self) -> List[Dict[str, Any]]:
        """자동매매 활성 사용자 조회"""
        try:
            users_data = execute_query("""
                SELECT id, email, bybit_api_key, bybit_api_secret, 
                       risk_level, max_leverage, custom_prompt,
                       preferred_symbol, preferred_interval
                FROM users 
                WHERE auto_trade_enabled = TRUE 
                  AND bybit_api_key IS NOT NULL 
                  AND bybit_api_secret IS NOT NULL
            """)
            
            active_users = []
            for user_data in users_data:
                try:
                    # API 키 복호화
                    decrypted_api_key = decrypt(user_data['bybit_api_key'])
                    decrypted_api_secret = decrypt(user_data['bybit_api_secret'])
                    
                    active_users.append({
                        'id': user_data['id'],
                        'email': user_data['email'],
                        'api_key': decrypted_api_key,
                        'api_secret': decrypted_api_secret,
                        'risk_level': user_data['risk_level'],
                        'max_leverage': user_data['max_leverage'],
                        'custom_prompt': user_data['custom_prompt'],
                        'preferred_symbol': user_data['preferred_symbol'] or 'BTCUSDT',
                        'preferred_interval': user_data['preferred_interval'] or '1'
                    })
                    
                except Exception as decrypt_error:
                    log_error("사용자 API 키 복호화 실패", {
                        "user_id": user_data['id'],
                        "error": str(decrypt_error)
                    })
                    continue
            
            log_info("활성 사용자 조회 완료", {
                "total_users": len(active_users)
            })
            
            return active_users
            
        except Exception as error:
            log_error("활성 사용자 조회 실패", {"error": str(error)})
            return []
    
    async def _process_user_trading(
        self, 
        user: Dict[str, Any], 
        candles: List
    ) -> Dict[str, Any]:
        """사용자별 거래 처리"""
        try:
            user_id = user['id']
            
            log_info("사용자 거래 처리 시작", {
                "user_id": user_id,
                "email": user['email'],
                "risk_level": user['risk_level']
            })
            
            # 1. GPT 분석 실행
            user_config = {
                'risk_level': user['risk_level'],
                'max_leverage': user['max_leverage'],
                'custom_prompt': user['custom_prompt']
            }
            
            analysis = await self.gpt_service.analyze_candles(candles, user_config)
            
            # 2. 분석 결과 검증
            validated_analysis = await self.gpt_service.validate_analysis(analysis, user_config)
            
            log_info("GPT 분석 완료", {
                "user_id": user_id,
                "action": validated_analysis.action,
                "confidence": validated_analysis.confidence,
                "leverage": validated_analysis.leverage
            })
            
            # 3. 거래 실행 여부 결정
            if validated_analysis.action == 'hold':
                log_info("거래 보류", {
                    "user_id": user_id,
                    "reason": validated_analysis.reason
                })
                
                return {
                    "success": True,
                    "action": "hold",
                    "reason": validated_analysis.reason
                }
            
            # 4. 실제 거래 실행
            trade_result = await self.trading_service.execute_trade(
                user_id,
                user['api_key'],
                user['api_secret'],
                validated_analysis,
                user['preferred_symbol']
            )
            
            log_info("거래 실행 결과", {
                "user_id": user_id,
                "success": trade_result['success'],
                "order_id": trade_result.get('order_id'),
                "error": trade_result.get('error')
            })
            
            return {
                "success": trade_result['success'],
                "action": validated_analysis.action,
                "analysis": validated_analysis.model_dump(),
                "trade_result": trade_result
            }
            
        except Exception as error:
            log_error("사용자 거래 처리 실패", {
                "user_id": user.get('id'),
                "error": str(error)
            })
            
            return {
                "success": False,
                "error": str(error)
            }
    
    async def _record_execution_result(self, result: Dict[str, Any]):
        """실행 결과 기록"""
        try:
            # Redis에 시스템 상태 업데이트
            set_system_status('auto_server_last_run', result.get('execution_end', datetime.now().isoformat()))
            set_system_status('auto_server_status', result.get('status', 'completed'))
            
            if result.get('error'):
                set_system_status('auto_server_last_error', result['error'])
            
            # 실행 통계 업데이트
            if 'successful_trades' in result:
                set_system_status('auto_server_successful_trades', str(result['successful_trades']))
                set_system_status('auto_server_failed_trades', str(result['failed_trades']))
            
            log_info("실행 결과 기록 완료", result)
            
        except Exception as error:
            log_error("실행 결과 기록 실패", {"error": str(error)})
    
    def stop_scheduler(self):
        """스케줄러 중지"""
        log_info("자동매매 스케줄러 중지")
        self.is_running = False
        schedule.clear()
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """스케줄러 상태 조회"""
        return {
            "is_running": self.is_running,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "scheduled_jobs": len(schedule.jobs),
            "next_run": schedule.next_run().isoformat() if schedule.jobs else None
        }
    
    async def manual_execution(self) -> Dict[str, Any]:
        """수동 실행 (테스트용)"""
        try:
            log_info("수동 거래 사이클 실행")
            await self.execute_trading_cycle()
            
            return {
                "success": True,
                "message": "수동 실행 완료",
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as error:
            log_error("수동 실행 실패", {"error": str(error)})
            return {
                "success": False,
                "error": str(error)
            }