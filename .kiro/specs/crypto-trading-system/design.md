# 코인 자동 매매 시스템 설계

## 개요

코인 자동 매매 시스템은 마이크로서비스 아키텍처를 기반으로 하며, 다음 4개의 주요 컴포넌트로 구성됩니다:

1. **데이터 수집 서버** - Bybit에서 실시간 캔들 데이터 수집 및 Redis 저장
2. **자동매매 서버** - GPT 분석 기반 5분 주기 자동매매 실행
3. **API 서버** - 프론트엔드와 데이터베이스 간 인터페이스 제공
4. **프론트엔드** - Next.js 기반 웹 애플리케이션

## 아키텍처

```mermaid
graph TB
    subgraph "External Services"
        Bybit[Bybit API/WebSocket]
        GPT[OpenAI GPT API]
    end
    
    subgraph "Backend Services"
        DataServer[데이터 수집 서버<br/>Node.js]
        AutoServer[자동매매 서버<br/>Node.js + Cron]
        APIServer[API 서버<br/>Node.js + Express]
    end
    
    subgraph "Data Layer"
        Redis[(Redis<br/>캔들 데이터)]
        MySQL[(MySQL<br/>사용자 정보)]
    end
    
    subgraph "Frontend"
        NextJS[Next.js 웹앱<br/>React + Tailwind]
    end
    
    Bybit --> DataServer
    DataServer --> Redis
    
    AutoServer --> Redis
    AutoServer --> MySQL
    AutoServer --> GPT
    AutoServer --> Bybit
    
    APIServer --> Redis
    APIServer --> MySQL
    
    NextJS --> APIServer
    
    classDef server fill:#e1f5fe
    classDef database fill:#f3e5f5
    classDef external fill:#fff3e0
    classDef frontend fill:#e8f5e8
    
    class DataServer,AutoServer,APIServer server
    class Redis,MySQL database
    class Bybit,GPT external
    class NextJS frontend
```

## 컴포넌트 및 인터페이스

### 1. 데이터 수집 서버

**역할**: Bybit에서 실시간 캔들 데이터를 수집하여 Redis에 저장

**주요 기능**:
- 초기 데이터 로딩: REST API로 BTCUSDT 1분봉 5000개 수집
- 실시간 데이터 수신: WebSocket으로 새로운 캔들 수신
- Redis 데이터 관리: LPUSH/LTRIM으로 최신 5000개 유지

**기술 스택**:
- Node.js + python(백엔드) + TypeScript(프론트엔드)
- `ws` 라이브러리 (WebSocket)
- `axios` (REST API)
- `redis` 클라이언트

**Redis 데이터 구조**:
```
Key: kline:BTCUSDT:1m
Value: JSON Array of Candle Objects
[
  {
    "timestamp": 1640995200000,
    "open": "47000.5",
    "high": "47100.0",
    "low": "46900.0",
    "close": "47050.0",
    "volume": "1.234"
  },
  ...
]
```

### 2. 자동매매 서버

**역할**: 5분마다 GPT 분석을 통해 자동매매 실행

**주요 기능**:
- 주기적 실행: `node-cron`으로 5분마다 실행
- 데이터 분석: Redis에서 최신 30개 캔들 조회
- GPT 분석: 캔들 데이터를 GPT에 전송하여 매매 판단 요청
- 사용자 필터링: MySQL에서 `auto_trade_enabled=true` 사용자 조회
- 주문 실행: 각 사용자의 Bybit API로 주문 실행

**기술 스택**:
- Node.js + TypeScript
- `node-cron` (스케줄링)
- `openai` (GPT API)
- `bybit-api` (거래소 API)
- `crypto-js` (API 키 암호화/복호화)

**GPT 프롬프트 구조**:
```json
{
  "role": "system",
  "content": "당신은 고도로 숙련된 암호화폐 트레이더입니다. 제공된 BTCUSDT 1분봉 차트 데이터를 분석하여 매매 판단을 내려주세요."
},
{
  "role": "user", 
  "content": {
    "symbol": "BTCUSDT",
    "interval": "1m",
    "candles": [...30개 캔들],
    "user_risk_level": "medium",
    "max_leverage": 10
  }
}
```

**GPT 응답 형식**:
```json
{
  "action": "buy|sell|hold",
  "confidence": 0.8,
  "leverage": 5,
  "reason": "RSI 과매도 구간 진입, 지지선 터치 후 반등 신호",
  "stop_loss": 0.02,
  "take_profit": 0.05
}
```

### 3. API 서버

**역할**: 프론트엔드와 백엔드 데이터 간 인터페이스 제공

**주요 엔드포인트**:

```typescript
// 인증 관련
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me

// 캔들 데이터
GET  /api/kline?symbol=BTCUSDT&interval=1m&count=30

// API 키 관리
POST /api/apikey
GET  /api/apikey
PUT  /api/apikey
DELETE /api/apikey

// 설정 관리
GET  /api/settings
POST /api/settings

// 거래 로그 (선택사항)
GET  /api/logs?page=1&limit=20
```

**기술 스택**:
- Node.js + Express + TypeScript
- `jsonwebtoken` (JWT 인증)
- `bcrypt` (비밀번호 해싱)
- `mysql2` (MySQL 연결)
- `redis` (캔들 데이터 조회)

### 4. 프론트엔드

**역할**: 사용자 인터페이스 제공

**페이지 구조**:
```
/auth/login          - 로그인
/auth/register       - 회원가입
/dashboard           - 메인 대시보드 (차트 + 제어패널)
/dashboard/api-key   - API 키 등록/관리
/dashboard/settings  - 자동매매 설정
/dashboard/logs      - 거래 로그 (선택사항)
```

**주요 컴포넌트**:
- `Chart.tsx`: lightweight-charts 기반 실시간 차트
- `ApiKeyForm.tsx`: API 키 등록/검증 폼
- `GptControlPanel.tsx`: 자동매매 토글 및 위험도 설정
- `TradeLog.tsx`: 거래 내역 테이블

**기술 스택**:
- Next.js 14+ (App Router)
- React + TypeScript
- Tailwind CSS + shadcn/ui
- `lightweight-charts` (차트)
- `swr` 또는 `react-query` (데이터 페칭)

## 데이터 모델

### MySQL 테이블 설계

```sql
-- 사용자 테이블
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    bybit_api_key TEXT,                    -- AES256 암호화
    bybit_api_secret TEXT,                 -- AES256 암호화
    max_leverage INT DEFAULT 10,
    auto_trade_enabled BOOLEAN DEFAULT FALSE,
    risk_level ENUM('low', 'medium', 'high') DEFAULT 'medium',
    custom_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 거래 로그 테이블 (선택사항)
CREATE TABLE trade_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    gpt_analysis JSON,                     -- GPT 분석 결과
    action ENUM('buy', 'sell', 'hold'),
    leverage DECIMAL(5,2),
    order_id VARCHAR(100),                 -- Bybit 주문 ID
    status ENUM('success', 'failed', 'pending'),
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 시스템 설정 테이블
CREATE TABLE system_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Redis 데이터 구조

```
# 캔들 데이터 (List 타입)
kline:BTCUSDT:1m = [최신캔들, ..., 5000번째캔들]

# 시스템 상태 (Hash 타입)  
system:status = {
  "data_server_last_update": "2024-01-01T12:00:00Z",
  "auto_server_last_run": "2024-01-01T12:05:00Z",
  "websocket_connected": "true"
}
```

## 오류 처리

### 1. 데이터 수집 서버 오류 처리

```typescript
// WebSocket 연결 오류
websocket.on('error', (error) => {
  console.error('WebSocket error:', error);
  // 5초 후 재연결 시도
  setTimeout(() => connectWebSocket(), 5000);
});

// Redis 연결 오류
redis.on('error', (error) => {
  console.error('Redis error:', error);
  // 연결 재시도 로직
});
```

### 2. 자동매매 서버 오류 처리

```typescript
// GPT API 오류
try {
  const gptResponse = await openai.chat.completions.create(prompt);
} catch (error) {
  console.error('GPT API error:', error);
  // 다음 주기까지 대기
  return;
}

// Bybit API 오류
try {
  const orderResult = await bybitClient.placeOrder(orderParams);
} catch (error) {
  // 거래 로그에 실패 기록
  await logTradeError(userId, error.message);
}
```

### 3. API 서버 오류 처리

```typescript
// 전역 오류 핸들러
app.use((error, req, res, next) => {
  console.error('API Error:', error);
  res.status(500).json({
    success: false,
    message: 'Internal server error',
    ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
  });
});
```

## 테스팅 전략

### 1. 단위 테스트
- 각 서버의 핵심 로직 테스트
- GPT 응답 파싱 로직 테스트
- API 키 암호화/복호화 테스트

### 2. 통합 테스트
- Redis 데이터 저장/조회 테스트
- MySQL CRUD 작업 테스트
- Bybit API 연동 테스트 (테스트넷 사용)

### 3. E2E 테스트
- 프론트엔드 주요 플로우 테스트
- 회원가입 → API 키 등록 → 자동매매 설정 플로우

### 4. 성능 테스트
- Redis 캔들 데이터 조회 성능
- 동시 사용자 처리 성능
- GPT API 응답 시간 모니터링

## 보안 고려사항

### 1. API 키 보안
```typescript
// AES256 암호화
const encrypt = (text: string): string => {
  const cipher = crypto.createCipher('aes-256-cbc', process.env.ENCRYPTION_KEY);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  return encrypted;
};
```

### 2. JWT 토큰 보안
```typescript
// httpOnly 쿠키로 JWT 저장
res.cookie('token', jwt.sign(payload, process.env.JWT_SECRET), {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict',
  maxAge: 24 * 60 * 60 * 1000 // 24시간
});
```

### 3. 환경 변수 관리
```bash
# .env 파일
DATABASE_URL=mysql://user:pass@localhost:3306/crypto_trading
REDIS_URL=redis://localhost:6379
BYBIT_API_URL=https://api.bybit.com
OPENAI_API_KEY=sk-...
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

## 배포 전략

### 1. 개발 환경
- Docker Compose로 로컬 개발 환경 구성
- MySQL, Redis 컨테이너 포함

### 2. 프로덕션 환경
- AWS EC2 또는 VPS 서버 배포
- PM2로 Node.js 프로세스 관리
- Nginx 리버스 프록시
- SSL 인증서 적용

### 3. 모니터링
- 서버 상태 모니터링
- 거래 실행 로그 모니터링
- 오류 알림 시스템

이 설계는 확장 가능하고 안정적인 코인 자동매매 시스템을 구축하기 위한 기반을 제공합니다.