import os
import sys
import httpx
import hmac
import hashlib
import time
from typing import Dict, Any, Optional
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.types import GPTAnalysis, TradeAction
from shared.database import execute_insert
from shared.utils import log_info, log_error

class BybitTradingService:
    """Bybit 거래 실행 서비스"""
    
    def __init__(self, testnet: bool = False):
        self.base_url = (
            os.getenv('BYBIT_TESTNET_URL', 'https://api-testnet.bybit.com')
            if testnet else
            os.getenv('BYBIT_API_URL', 'https://api.bybit.com')
        )
        self.timeout = 30.0
        self.testnet = testnet
    
    async def execute_trade(
        self,
        user_id: int,
        api_key: str,
        api_secret: str,
        analysis: GPTAnalysis,
        symbol: str = 'BTCUSDT'
    ) -> Dict[str, Any]:
        """거래 실행"""
        try:
            log_info("거래 실행 시작", {
                "user_id": user_id,
                "symbol": symbol,
                "action": analysis.action,
                "leverage": analysis.leverage
            })
            
            # 1. 계정 잔고 확인
            balance_info = await self._get_account_balance(api_key, api_secret)
            if not balance_info['sufficient']:
                return {
                    "success": False,
                    "error": "잔고 부족",
                    "balance_info": balance_info
                }
            
            # 2. 현재 가격 조회
            current_price = await self._get_current_price(symbol)
            if not current_price:
                return {
                    "success": False,
                    "error": "현재 가격 조회 실패"
                }
            
            # 3. 주문 수량 계산
            order_qty = self._calculate_order_quantity(
                balance_info['available_balance'],
                current_price,
                analysis.leverage
            )
            
            if order_qty <= 0:
                return {
                    "success": False,
                    "error": "주문 수량이 최소 단위 미만"
                }
            
            # 4. 주문 실행
            order_result = await self._place_order(
                api_key,
                api_secret,
                symbol,
                analysis.action,
                order_qty,
                current_price,
                analysis
            )
            
            # 5. 거래 로그 저장
            await self._save_trade_log(
                user_id,
                analysis,
                order_result,
                current_price,
                order_qty
            )
            
            log_info("거래 실행 완료", {
                "user_id": user_id,
                "order_id": order_result.get('order_id'),
                "status": order_result.get('status')
            })
            
            return order_result
            
        except Exception as error:
            log_error("거래 실행 실패", {
                "user_id": user_id,
                "error": str(error)
            })
            
            # 실패 로그 저장
            await self._save_trade_log(
                user_id,
                analysis,
                {"success": False, "error": str(error)},
                0,
                0
            )
            
            return {
                "success": False,
                "error": str(error)
            }
    
    async def _get_account_balance(
        self,
        api_key: str,
        api_secret: str
    ) -> Dict[str, Any]:
        """계정 잔고 조회 - Bybit API v5"""
        try:
            endpoint = "/v5/account/wallet-balance"
            params = {"accountType": "UNIFIED"}  # SPOT 대신 UNIFIED 사용
            
            timestamp = str(int(time.time() * 1000))
            signature = self._generate_signature(
                api_secret, timestamp, api_key, endpoint, params
            )
            
            headers = {
                "X-BAPI-API-KEY": api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": "5000",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    headers=headers
                )
                
                data = response.json()
                
                if data.get('retCode') == 0:
                    # USDT 잔고 찾기
                    usdt_balance = 0
                    available_balance = 0
                    
                    wallet_list = data.get('result', {}).get('list', [])
                    
                    for wallet in wallet_list:
                        for coin in wallet.get('coin', []):
                            if coin.get('coin') == 'USDT':
                                usdt_balance = float(coin.get('walletBalance', 0))
                                available_balance = float(coin.get('availableToWithdraw', 0))
                                break
                    
                    return {
                        "sufficient": available_balance > 10,  # 최소 10 USDT 필요
                        "available_balance": available_balance,
                        "total_balance": usdt_balance,
                        "currency": "USDT"
                    }
                else:
                    raise Exception(f"잔고 조회 실패: {data.get('retMsg')}")
                    
        except Exception as error:
            log_error("잔고 조회 실패", {"error": str(error)})
            return {
                "sufficient": False,
                "available_balance": 0,
                "error": str(error)
            }    async 
def _get_current_price(self, symbol: str) -> Optional[float]:
        """현재 가격 조회"""
        try:
            endpoint = "/v5/market/tickers"
            params = {
                "category": "spot",
                "symbol": symbol
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    params=params
                )
                
                data = response.json()
                
                if data.get('retCode') == 0:
                    ticker_list = data.get('result', {}).get('list', [])
                    if ticker_list:
                        return float(ticker_list[0].get('lastPrice', 0))
                
                raise Exception(f"가격 조회 실패: {data.get('retMsg')}")
                
        except Exception as error:
            log_error("현재 가격 조회 실패", {
                "symbol": symbol,
                "error": str(error)
            })
            return None
    
    def _calculate_order_quantity(
        self,
        available_balance: float,
        current_price: float,
        leverage: int
    ) -> float:
        """주문 수량 계산"""
        try:
            # 사용 가능한 잔고의 80%만 사용 (안전 마진)
            usable_balance = available_balance * 0.8
            
            # 레버리지 적용하지 않음 (Spot 거래)
            # 실제로는 레버리지는 선물 거래에서만 사용
            order_value = usable_balance
            
            # 주문 수량 계산 (BTC 기준)
            order_qty = order_value / current_price
            
            # 최소 주문 단위로 반올림 (Bybit BTCUSDT 최소 단위: 0.000001)
            min_qty = 0.000001
            order_qty = round(order_qty / min_qty) * min_qty
            
            log_info("주문 수량 계산", {
                "available_balance": available_balance,
                "usable_balance": usable_balance,
                "current_price": current_price,
                "calculated_qty": order_qty
            })
            
            return order_qty
            
        except Exception as error:
            log_error("주문 수량 계산 실패", {"error": str(error)})
            return 0
    
    async def _place_order(
        self,
        api_key: str,
        api_secret: str,
        symbol: str,
        action: TradeAction,
        qty: float,
        price: float,
        analysis: GPTAnalysis
    ) -> Dict[str, Any]:
        """주문 실행 - Bybit API v5"""
        try:
            endpoint = "/v5/order/create"
            
            # 주문 타입 결정
            side = "Buy" if action == TradeAction.BUY else "Sell"
            
            # 시장가 주문으로 실행 (Spot 거래)
            order_data = {
                "category": "spot",
                "symbol": symbol,
                "side": side,
                "orderType": "Market",
                "qty": str(qty),
                "timeInForce": "IOC",  # Immediate or Cancel
                "orderLinkId": f"auto_trade_{user_id}_{int(time.time())}"  # 주문 추적용 ID
            }
            
            timestamp = str(int(time.time() * 1000))
            
            # POST 요청용 서명 생성
            signature = self._generate_post_signature(
                api_secret, timestamp, api_key, order_data
            )
            
            headers = {
                "X-BAPI-API-KEY": api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": "5000",
                "Content-Type": "application/json"
            }
            
            # 테스트넷에서는 실제 주문 대신 시뮬레이션
            if self.testnet or os.getenv('NODE_ENV') == 'development':
                log_info("테스트 모드: 주문 시뮬레이션", {
                    "symbol": symbol,
                    "side": side,
                    "qty": qty,
                    "price": price
                })
                
                return {
                    "success": True,
                    "order_id": f"test_{int(time.time())}",
                    "status": "Filled",
                    "side": side,
                    "qty": qty,
                    "price": price,
                    "simulated": True
                }
            
            # 실제 주문 실행
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=order_data,
                    headers=headers
                )
                
                data = response.json()
                
                if data.get('retCode') == 0:
                    result = data.get('result', {})
                    return {
                        "success": True,
                        "order_id": result.get('orderId'),
                        "order_link_id": result.get('orderLinkId'),
                        "status": "Submitted",
                        "side": side,
                        "qty": qty,
                        "price": price
                    }
                else:
                    raise Exception(f"주문 실행 실패: {data.get('retMsg')}")
                    
        except Exception as error:
            log_error("주문 실행 실패", {
                "symbol": symbol,
                "action": action,
                "qty": qty,
                "error": str(error)
            })
            
            return {
                "success": False,
                "error": str(error)
            }
    
    def _generate_signature(
        self,
        api_secret: str,
        timestamp: str,
        api_key: str,
        endpoint: str,
        params: Dict[str, Any]
    ) -> str:
        """GET 요청용 서명 생성"""
        try:
            sorted_params = sorted(params.items())
            query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
            
            sign_string = timestamp + api_key + "5000" + query_string
            
            signature = hmac.new(
                api_secret.encode('utf-8'),
                sign_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as error:
            log_error("서명 생성 실패", {"error": str(error)})
            raise
    
    def _generate_post_signature(
        self,
        api_secret: str,
        timestamp: str,
        api_key: str,
        order_data: Dict[str, Any]
    ) -> str:
        """POST 요청용 서명 생성"""
        try:
            import json
            
            json_str = json.dumps(order_data, separators=(',', ':'))
            sign_string = timestamp + api_key + "5000" + json_str
            
            signature = hmac.new(
                api_secret.encode('utf-8'),
                sign_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as error:
            log_error("POST 서명 생성 실패", {"error": str(error)})
            raise
    
    async def _save_trade_log(
        self,
        user_id: int,
        analysis: GPTAnalysis,
        order_result: Dict[str, Any],
        price: float,
        qty: float
    ) -> None:
        """거래 로그 저장"""
        try:
            status = "success" if order_result.get('success') else "failed"
            error_message = order_result.get('error') if not order_result.get('success') else None
            
            execute_insert(
                """
                INSERT INTO trade_logs 
                (user_id, gpt_analysis, action, leverage, order_id, status, error_message, executed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    user_id,
                    analysis.model_dump_json(),
                    analysis.action.value,
                    float(analysis.leverage),
                    order_result.get('order_id'),
                    status,
                    error_message
                )
            )
            
            log_info("거래 로그 저장 완료", {
                "user_id": user_id,
                "status": status,
                "order_id": order_result.get('order_id')
            })
            
        except Exception as error:
            log_error("거래 로그 저장 실패", {
                "user_id": user_id,
                "error": str(error)
            })
    
    async def get_order_status(
        self,
        api_key: str,
        api_secret: str,
        order_id: str,
        symbol: str = 'BTCUSDT'
    ) -> Dict[str, Any]:
        """주문 상태 조회"""
        try:
            endpoint = "/v5/order/realtime"
            params = {
                "category": "spot",
                "symbol": symbol,
                "orderId": order_id
            }
            
            timestamp = str(int(time.time() * 1000))
            signature = self._generate_signature(
                api_secret, timestamp, api_key, endpoint, params
            )
            
            headers = {
                "X-BAPI-API-KEY": api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": "5000",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    headers=headers
                )
                
                data = response.json()
                
                if data.get('retCode') == 0:
                    order_list = data.get('result', {}).get('list', [])
                    if order_list:
                        order = order_list[0]
                        return {
                            "success": True,
                            "order_id": order.get('orderId'),
                            "status": order.get('orderStatus'),
                            "side": order.get('side'),
                            "qty": order.get('qty'),
                            "executed_qty": order.get('cumExecQty'),
                            "avg_price": order.get('avgPrice'),
                            "created_time": order.get('createdTime'),
                            "updated_time": order.get('updatedTime')
                        }
                    else:
                        return {"success": False, "error": "주문을 찾을 수 없습니다"}
                else:
                    raise Exception(f"주문 상태 조회 실패: {data.get('retMsg')}")
                    
        except Exception as error:
            log_error("주문 상태 조회 실패", {
                "order_id": order_id,
                "error": str(error)
            })
            return {"success": False, "error": str(error)}
    
    async def get_trade_history(
        self,
        api_key: str,
        api_secret: str,
        symbol: str = 'BTCUSDT',
        limit: int = 50
    ) -> Dict[str, Any]:
        """거래 내역 조회"""
        try:
            endpoint = "/v5/execution/list"
            params = {
                "category": "spot",
                "symbol": symbol,
                "limit": str(limit)
            }
            
            timestamp = str(int(time.time() * 1000))
            signature = self._generate_signature(
                api_secret, timestamp, api_key, endpoint, params
            )
            
            headers = {
                "X-BAPI-API-KEY": api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": "5000",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    headers=headers
                )
                
                data = response.json()
                
                if data.get('retCode') == 0:
                    executions = data.get('result', {}).get('list', [])
                    trades = []
                    
                    for execution in executions:
                        trades.append({
                            "execution_id": execution.get('execId'),
                            "order_id": execution.get('orderId'),
                            "symbol": execution.get('symbol'),
                            "side": execution.get('side'),
                            "qty": execution.get('execQty'),
                            "price": execution.get('execPrice'),
                            "fee": execution.get('execFee'),
                            "exec_time": execution.get('execTime')
                        })
                    
                    return {
                        "success": True,
                        "trades": trades,
                        "total_count": len(trades)
                    }
                else:
                    raise Exception(f"거래 내역 조회 실패: {data.get('retMsg')}")
                    
        except Exception as error:
            log_error("거래 내역 조회 실패", {
                "symbol": symbol,
                "error": str(error)
            })
            return {"success": False, "error": str(error)}
    
    async def cancel_order(
        self,
        api_key: str,
        api_secret: str,
        order_id: str,
        symbol: str = 'BTCUSDT'
    ) -> Dict[str, Any]:
        """주문 취소"""
        try:
            endpoint = "/v5/order/cancel"
            
            order_data = {
                "category": "spot",
                "symbol": symbol,
                "orderId": order_id
            }
            
            timestamp = str(int(time.time() * 1000))
            signature = self._generate_post_signature(
                api_secret, timestamp, api_key, order_data
            )
            
            headers = {
                "X-BAPI-API-KEY": api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": "5000",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=order_data,
                    headers=headers
                )
                
                data = response.json()
                
                if data.get('retCode') == 0:
                    result = data.get('result', {})
                    return {
                        "success": True,
                        "order_id": result.get('orderId'),
                        "status": "Cancelled"
                    }
                else:
                    raise Exception(f"주문 취소 실패: {data.get('retMsg')}")
                    
        except Exception as error:
            log_error("주문 취소 실패", {
                "order_id": order_id,
                "error": str(error)
            })
            return {"success": False, "error": str(error)}