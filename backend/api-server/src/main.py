import os
import sys
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from datetime import datetime
from dotenv import load_dotenv

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from shared.utils import validate_env_vars, log_info, log_error, create_api_response
from shared.database import test_connection, create_connection_pool
from shared.redis_client import test_redis_connection
from routes.auth_routes import router as auth_router
from routes.apikey_routes import router as apikey_router
from routes.kline_routes import router as kline_router
from routes.settings_routes import router as settings_router
from routes.logs_routes import router as logs_router

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Crypto Trading API Server",
    description="코인 자동매매 시스템 API 서버",
    version="1.0.0",
    docs_url="/docs" if os.getenv("NODE_ENV") == "development" else None,
    redoc_url="/redoc" if os.getenv("NODE_ENV") == "development" else None
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 프론트엔드 개발 서버
        "http://127.0.0.1:3000",
        "https://your-domain.com"  # 프로덕션 도메인
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 미들웨어
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.your-domain.com"]
)

# 라우터 등록
app.include_router(auth_router)
app.include_router(apikey_router)
app.include_router(kline_router)
app.include_router(settings_router)
app.include_router(logs_router)

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    # 요청 로깅
    log_info(f"요청 시작: {request.method} {request.url}", {
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
        "timestamp": start_time.isoformat()
    })
    
    try:
        response = await call_next(request)
        
        # 응답 시간 계산
        process_time = (datetime.now() - start_time).total_seconds()
        
        # 응답 로깅
        log_info(f"요청 완료: {request.method} {request.url}", {
            "status_code": response.status_code,
            "process_time": f"{process_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        })
        
        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as error:
        # 오류 로깅
        log_error(f"요청 처리 중 오류: {request.method} {request.url}", {
            "error": str(error),
            "client_ip": request.client.host,
            "timestamp": datetime.now().isoformat()
        })
        raise

# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_error("처리되지 않은 예외 발생", {
        "error": str(exc),
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime.now().isoformat()
    })
    
    return JSONResponse(
        status_code=500,
        content=create_api_response(
            success=False,
            error="내부 서버 오류가 발생했습니다.",
            message="서버 관리자에게 문의하세요."
        )
    )

# HTTP 예외 핸들러
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=create_api_response(
            success=False,
            error=exc.detail,
            message=f"HTTP {exc.status_code} 오류"
        )
    )# 헬스체크 엔드
포인트
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    try:
        # 데이터베이스 연결 테스트
        db_status = test_connection()
        
        # Redis 연결 테스트
        redis_status = test_redis_connection()
        
        status = "healthy" if db_status and redis_status else "unhealthy"
        
        return create_api_response(
            success=True,
            data={
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "database": "connected" if db_status else "disconnected",
                    "redis": "connected" if redis_status else "disconnected"
                }
            },
            message="서버가 정상적으로 실행 중입니다."
        )
        
    except Exception as error:
        log_error("헬스체크 실패", {"error": str(error)})
        return JSONResponse(
            status_code=503,
            content=create_api_response(
                success=False,
                error="서버 상태 확인 실패",
                message=str(error)
            )
        )

# 루트 엔드포인트
@app.get("/")
async def root():
    """API 서버 정보"""
    return create_api_response(
        success=True,
        data={
            "name": "Crypto Trading API Server",
            "version": "1.0.0",
            "description": "코인 자동매매 시스템 API 서버",
            "timestamp": datetime.now().isoformat()
        },
        message="API 서버가 정상적으로 실행 중입니다."
    )

# 서버 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    try:
        log_info("API 서버 시작")
        
        # 환경 변수 검증
        validate_env_vars()
        
        # 데이터베이스 연결 풀 생성
        create_connection_pool()
        
        # 데이터베이스 연결 테스트
        if not test_connection():
            raise Exception("데이터베이스 연결 실패")
        
        # Redis 연결 테스트
        if not test_redis_connection():
            raise Exception("Redis 연결 실패")
        
        log_info("API 서버 초기화 완료")
        
    except Exception as error:
        log_error("API 서버 시작 실패", {"error": str(error)})
        raise

# 서버 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    log_info("API 서버 종료 중...")
    
    # 정리 작업
    try:
        from shared.database import close_connection_pool
        from shared.redis_client import disconnect_redis
        
        close_connection_pool()
        disconnect_redis()
        
        log_info("API 서버 종료 완료")
        
    except Exception as error:
        log_error("API 서버 종료 중 오류", {"error": str(error)})

# 개발 서버 실행
if __name__ == "__main__":
    port = int(os.getenv("API_SERVER_PORT", 3001))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("NODE_ENV") == "development",
        log_level="info"
    )