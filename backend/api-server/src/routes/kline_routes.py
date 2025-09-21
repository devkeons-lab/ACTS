import os
import sys
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.redis_client import get_candle_data, get_candle_count, get_system_status
from shared.types import CandleData
from shared.utils import create_api_response, log_info, log_error
from shared.symbols import (
    is_supported_symbol, 
    is_supported_interval, 
    get_symbol_info,
    get_supported_symbols,
    get_supported_intervals,
    SUPPORTED_SYMBOLS
)

# 라우터 생성
router = APIRouter(prefix="/api/kline", tags=["캔들 데이터"])

# 응답 모델
class KlineResponse(BaseModel):
    symbol: str
    interval: str
    count: int
    data: List[CandleData]

class KlineStatusResponse(BaseModel):
    symbol: str
    interval: str
    total_count: int
    last_update: Optional[str]
    websocket_status: Optional[str]

# 캔들 데이터 조회
@router.get("/")
async def get_kline_data(
    symbol: str = Query(default="BTCUSDT", description="거래 심볼"),
    interval: str = Query(default="1", description="캔들 간격 (1분)"),
    count: int = Query(default=30, ge=1, le=1000, description="조회할 캔들 개수")
):
    """캔들 데이터 조회"""
    try:
        # 파라미터 검증
        if not is_supported_symbol(symbol):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 심볼입니다. 지원 심볼: {', '.join(SUPPORTED_SYMBOLS[:10])}..."
            )
        
        if not is_supported_interval(interval):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 캔들 간격입니다. 지원 간격: {', '.join(get_supported_intervals())}"
            )
        
        # Redis에서 캔들 데이터 조회
        candles = get_candle_data(symbol.upper(), interval, count)
        
        if not candles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="캔들 데이터를 찾을 수 없습니다."
            )
        
        log_info("캔들 데이터 API 조회", {
            "symbol": symbol,
            "interval": interval,
            "requested_count": count,
            "returned_count": len(candles)
        })
        
        return create_api_response(
            success=True,
            data={
                "symbol": symbol.upper(),
                "interval": interval,
                "count": len(candles),
                "data": [candle.model_dump() for candle in candles]
            },
            message=f"{len(candles)}개의 캔들 데이터 조회 완료"
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        log_error("캔들 데이터 조회 실패", {
            "symbol": symbol,
            "interval": interval,
            "count": count,
            "error": str(error)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="캔들 데이터 조회 중 오류가 발생했습니다."
        )

# 캔들 데이터 상태 조회
@router.get("/status")
async def get_kline_status(
    symbol: str = Query(default="BTCUSDT", description="거래 심볼"),
    interval: str = Query(default="1", description="캔들 간격")
):
    """캔들 데이터 상태 조회"""
    try:
        # 총 캔들 개수 조회
        total_count = get_candle_count(symbol.upper(), interval)
        
        # 시스템 상태 조회
        system_status = get_system_status()
        
        last_update = None
        websocket_status = None
        
        if isinstance(system_status, dict):
            last_update = system_status.get('data_server_last_update')
            websocket_status = system_status.get('websocket_status')
        
        return create_api_response(
            success=True,
            data={
                "symbol": symbol.upper(),
                "interval": interval,
                "total_count": total_count,
                "last_update": last_update,
                "websocket_status": websocket_status,
                "data_available": total_count > 0
            },
            message="캔들 데이터 상태 조회 완료"
        )
        
    except Exception as error:
        log_error("캔들 데이터 상태 조회 실패", {
            "symbol": symbol,
            "interval": interval,
            "error": str(error)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="캔들 데이터 상태 조회 중 오류가 발생했습니다."
        )# 최신
 캔들 데이터 조회
@router.get("/latest")
async def get_latest_candle(
    symbol: str = Query(default="BTCUSDT", description="거래 심볼"),
    interval: str = Query(default="1", description="캔들 간격")
):
    """최신 캔들 데이터 조회"""
    try:
        # 최신 1개 캔들 조회
        candles = get_candle_data(symbol.upper(), interval, 1)
        
        if not candles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="최신 캔들 데이터를 찾을 수 없습니다."
            )
        
        latest_candle = candles[0]
        
        return create_api_response(
            success=True,
            data={
                "symbol": symbol.upper(),
                "interval": interval,
                "candle": latest_candle.model_dump(),
                "timestamp_iso": latest_candle.timestamp,
                "price": {
                    "open": float(latest_candle.open),
                    "high": float(latest_candle.high),
                    "low": float(latest_candle.low),
                    "close": float(latest_candle.close)
                },
                "volume": float(latest_candle.volume)
            },
            message="최신 캔들 데이터 조회 완료"
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        log_error("최신 캔들 데이터 조회 실패", {
            "symbol": symbol,
            "interval": interval,
            "error": str(error)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="최신 캔들 데이터 조회 중 오류가 발생했습니다."
        )

# 캔들 데이터 범위 조회
@router.get("/range")
async def get_kline_range(
    symbol: str = Query(default="BTCUSDT", description="거래 심볼"),
    interval: str = Query(default="1", description="캔들 간격"),
    start_index: int = Query(default=0, ge=0, description="시작 인덱스"),
    end_index: int = Query(default=29, ge=0, description="종료 인덱스")
):
    """캔들 데이터 범위 조회"""
    try:
        # 인덱스 검증
        if start_index > end_index:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시작 인덱스는 종료 인덱스보다 작아야 합니다."
            )
        
        if end_index - start_index > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="한 번에 최대 1000개까지만 조회할 수 있습니다."
            )
        
        # 필요한 캔들 개수 계산
        count_needed = end_index + 1
        
        # Redis에서 캔들 데이터 조회
        all_candles = get_candle_data(symbol.upper(), interval, count_needed)
        
        if not all_candles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="캔들 데이터를 찾을 수 없습니다."
            )
        
        # 범위에 해당하는 캔들 추출
        if end_index >= len(all_candles):
            end_index = len(all_candles) - 1
        
        if start_index >= len(all_candles):
            range_candles = []
        else:
            range_candles = all_candles[start_index:end_index + 1]
        
        return create_api_response(
            success=True,
            data={
                "symbol": symbol.upper(),
                "interval": interval,
                "start_index": start_index,
                "end_index": end_index,
                "count": len(range_candles),
                "data": [candle.model_dump() for candle in range_candles]
            },
            message=f"범위 캔들 데이터 조회 완료 ({start_index}-{end_index})"
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        log_error("범위 캔들 데이터 조회 실패", {
            "symbol": symbol,
            "interval": interval,
            "start_index": start_index,
            "end_index": end_index,
            "error": str(error)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="범위 캔들 데이터 조회 중 오류가 발생했습니다."
        )

# 지원 심볼 목록 조회
@router.get("/symbols")
async def get_supported_symbols_list():
    """지원하는 심볼 목록 조회"""
    try:
        symbols_with_info = []
        
        for symbol in get_supported_symbols():
            info = get_symbol_info(symbol)
            symbols_with_info.append({
                "symbol": symbol,
                "name": info.get('name', symbol),
                "description": info.get('description', symbol),
                "base_asset": symbol.replace('USDT', ''),
                "quote_asset": "USDT"
            })
        
        return create_api_response(
            success=True,
            data={
                "symbols": symbols_with_info,
                "total_count": len(symbols_with_info),
                "supported_intervals": get_supported_intervals()
            },
            message=f"{len(symbols_with_info)}개의 지원 심볼 조회 완료"
        )
        
    except Exception as error:
        log_error("지원 심볼 목록 조회 실패", {"error": str(error)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="지원 심볼 목록 조회 중 오류가 발생했습니다."
        )

# 심볼 정보 조회
@router.get("/symbol/{symbol}")
async def get_symbol_details(symbol: str):
    """특정 심볼 정보 조회"""
    try:
        symbol = symbol.upper()
        
        if not is_supported_symbol(symbol):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="지원하지 않는 심볼입니다."
            )
        
        info = get_symbol_info(symbol)
        
        # 캔들 데이터 상태 확인
        total_count = get_candle_count(symbol, "1")  # 1분봉 기준
        
        return create_api_response(
            success=True,
            data={
                "symbol": symbol,
                "name": info.get('name', symbol),
                "description": info.get('description', symbol),
                "base_asset": symbol.replace('USDT', ''),
                "quote_asset": "USDT",
                "data_available": total_count > 0,
                "candle_count": total_count,
                "supported_intervals": get_supported_intervals()
            },
            message=f"{symbol} 심볼 정보 조회 완료"
        )
        
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        log_error("심볼 정보 조회 실패", {
            "symbol": symbol,
            "error": str(error)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="심볼 정보 조회 중 오류가 발생했습니다."
        )