import os
import sys
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.database import execute_query, execute_query_single
from middleware.auth_middleware import get_current_user
from shared.utils import create_api_response, log_info, log_error

# 라우터 생성
router = APIRouter(prefix="/api/logs", tags=["거래 로그"])

# 거래 로그 조회
@router.get("/")
async def get_trade_logs(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 항목 수"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """사용자의 거래 로그 조회"""
    try:
        user_id = current_user['user_id']
        offset = (page - 1) * limit

        # 총 개수 조회
        total_count_result = execute_query_single(
            "SELECT COUNT(*) as total FROM trade_logs WHERE user_id = %s",
            (user_id,)
        )
        total_count = total_count_result['total'] if total_count_result else 0

        # 거래 로그 조회
        logs_data = execute_query(
            """
            SELECT id, gpt_analysis, action, leverage, order_id, status, 
                   error_message, executed_at
            FROM trade_logs 
            WHERE user_id = %s 
            ORDER BY executed_at DESC 
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset)
        )

        # 데이터 변환
        logs = []
        for log_data in logs_data:
            try:
                import json
                gpt_analysis = json.loads(log_data['gpt_analysis']) if log_data['gpt_analysis'] else {}
            except (json.JSONDecodeError, TypeError):
                gpt_analysis = {}

            logs.append({
                "id": log_data['id'],
                "gpt_analysis": gpt_analysis,
                "action": log_data['action'],
                "leverage": float(log_data['leverage']) if log_data['leverage'] else 0,
                "order_id": log_data['order_id'],
                "status": log_data['status'],
                "error_message": log_data['error_message'],
                "executed_at": log_data['executed_at'].isoformat()
            })

        # 페이지네이션 정보
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        return create_api_response(
            success=True,
            data={
                "logs": logs,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "has_next": has_next,
                    "has_prev": has_prev,
                    "limit": limit
                }
            },
            message=f"{len(logs)}개의 거래 로그 조회 완료"
        )

    except Exception as error:
        log_error("거래 로그 조회 실패", {
            "user_id": current_user.get('user_id'),
            "error": str(error)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="거래 로그 조회 중 오류가 발생했습니다."
        )

# 특정 거래 로그 상세 조회
@router.get("/{log_id}")
async def get_trade_log_detail(
    log_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """특정 거래 로그 상세 조회"""
    try:
        user_id = current_user['user_id']

        log_data = execute_query_single(
            """
            SELECT id, gpt_analysis, action, leverage, order_id, status, 
                   error_message, executed_at
            FROM trade_logs 
            WHERE id = %s AND user_id = %s
            """,
            (log_id, user_id)
        )

        if not log_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="거래 로그를 찾을 수 없습니다."
            )

        # GPT 분석 데이터 파싱
        try:
            import json
            gpt_analysis = json.loads(log_data['gpt_analysis']) if log_data['gpt_analysis'] else {}
        except (json.JSONDecodeError, TypeError):
            gpt_analysis = {}

        log_detail = {
            "id": log_data['id'],
            "gpt_analysis": gpt_analysis,
            "action": log_data['action'],
            "leverage": float(log_data['leverage']) if log_data['leverage'] else 0,
            "order_id": log_data['order_id'],
            "status": log_data['status'],
            "error_message": log_data['error_message'],
            "executed_at": log_data['executed_at'].isoformat()
        }

        return create_api_response(
            success=True,
            data=log_detail,
            message="거래 로그 상세 조회 완료"
        )

    except HTTPException:
        raise
    except Exception as error:
        log_error("거래 로그 상세 조회 실패", {
            "user_id": current_user.get('user_id'),
            "log_id": log_id,
            "error": str(error)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="거래 로그 상세 조회 중 오류가 발생했습니다."
        )

# 거래 통계 조회
@router.get("/stats/summary")
async def get_trade_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """거래 통계 요약 조회"""
    try:
        user_id = current_user['user_id']

        # 기본 통계 조회
        stats_data = execute_query_single(
            """
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_trades,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_trades,
                SUM(CASE WHEN action = 'buy' THEN 1 ELSE 0 END) as buy_trades,
                SUM(CASE WHEN action = 'sell' THEN 1 ELSE 0 END) as sell_trades,
                SUM(CASE WHEN action = 'hold' THEN 1 ELSE 0 END) as hold_trades,
                AVG(leverage) as avg_leverage,
                MAX(executed_at) as last_trade_at
            FROM trade_logs 
            WHERE user_id = %s
            """,
            (user_id,)
        )

        if not stats_data:
            stats_data = {
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'hold_trades': 0,
                'avg_leverage': 0,
                'last_trade_at': None
            }

        # 성공률 계산
        success_rate = 0
        if stats_data['total_trades'] > 0:
            success_rate = (stats_data['successful_trades'] / stats_data['total_trades']) * 100

        stats = {
            "total_trades": stats_data['total_trades'],
            "successful_trades": stats_data['successful_trades'],
            "failed_trades": stats_data['failed_trades'],
            "success_rate": round(success_rate, 2),
            "action_distribution": {
                "buy": stats_data['buy_trades'],
                "sell": stats_data['sell_trades'],
                "hold": stats_data['hold_trades']
            },
            "avg_leverage": round(float(stats_data['avg_leverage'] or 0), 2),
            "last_trade_at": stats_data['last_trade_at'].isoformat() if stats_data['last_trade_at'] else None
        }

        return create_api_response(
            success=True,
            data=stats,
            message="거래 통계 조회 완료"
        )

    except Exception as error:
        log_error("거래 통계 조회 실패", {
            "user_id": current_user.get('user_id'),
            "error": str(error)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="거래 통계 조회 중 오류가 발생했습니다."
        )