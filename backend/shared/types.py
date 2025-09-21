from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

# 위험도 레벨 Enum
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# 거래 액션 Enum
class TradeAction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

# 거래 상태 Enum
class TradeStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"

# 사용자 모델
class User(BaseModel):
    id: int
    email: str
    password_hash: str
    bybit_api_key: Optional[str] = None
    bybit_api_secret: Optional[str] = None
    max_leverage: int = 10
    auto_trade_enabled: bool = False
    risk_level: RiskLevel = RiskLevel.MEDIUM
    custom_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# 사용자 설정 모델
class UserSettings(BaseModel):
    max_leverage: int
    auto_trade_enabled: bool
    risk_level: RiskLevel
    custom_prompt: Optional[str] = None

# 캔들 데이터 모델
class CandleData(BaseModel):
    timestamp: int
    open: str
    high: str
    low: str
    close: str
    volume: str

# GPT 분석 결과 모델
class GPTAnalysis(BaseModel):
    action: TradeAction
    confidence: float
    leverage: int
    reason: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    indicators: Optional[Dict[str, Any]] = None

# 거래 로그 모델
class TradeLog(BaseModel):
    id: int
    user_id: int
    gpt_analysis: GPTAnalysis
    action: TradeAction
    leverage: float
    order_id: Optional[str] = None
    status: TradeStatus
    error_message: Optional[str] = None
    executed_at: datetime

# API 응답 모델
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.now()

# Bybit API 키 모델
class BybitApiKey(BaseModel):
    api_key: str
    api_secret: str
    testnet: bool = False

# 시스템 설정 모델
class SystemSetting(BaseModel):
    id: int
    setting_key: str
    setting_value: str
    updated_at: datetime

# 자동매매 설정 모델
class AutoTradeConfig(BaseModel):
    user_id: int
    risk_level: RiskLevel
    max_leverage: int
    custom_prompt: Optional[str] = None
    enabled: bool