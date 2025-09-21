# 코인 자동 매매 시스템

GPT 기반 AI 판단을 통해 Bybit 거래소에서 자동 매매를 수행하는 시스템입니다.

## 시스템 구성

- **데이터 수집 서버**: Bybit에서 실시간 캔들 데이터를 수집하여 Redis에 저장
- **자동매매 서버**: GPT 분석을 통해 5분마다 자동 매매 실행
- **API 서버**: 프론트엔드와 데이터베이스 간 인터페이스 제공
- **프론트엔드**: Next.js 기반 웹 애플리케이션

## 기술 스택

### 백엔드
- Python + FastAPI
- Redis (캔들 데이터 저장)
- MySQL (사용자 정보)
- OpenAI GPT API
- Bybit API

### 프론트엔드
- Next.js 14 (App Router)
- React + TypeScript
- Tailwind CSS + shadcn/ui
- lightweight-charts

## 개발 환경 설정

### 1. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 API 키들을 설정하세요
```

### 2. Docker로 데이터베이스 실행
```bash
docker-compose up -d
```

### 3. 의존성 설치 및 서버 실행

#### 데이터 수집 서버 (Python)
```bash
cd backend/data-server
pip install -r requirements.txt
python src/main.py
```

#### 자동매매 서버 (Python)
```bash
cd backend/auto-server
pip install -r requirements.txt
python src/main.py
```

#### API 서버 (Python)
```bash
cd backend/api-server
pip install -r requirements.txt
python src/main.py
```

#### 프론트엔드 (Next.js)
```bash
cd frontend
npm install
npm run dev
```

## 서비스 포트

- 프론트엔드: http://localhost:3000
- API 서버: http://localhost:3001
- 데이터 수집 서버: http://localhost:3002
- 자동매매 서버: http://localhost:3003
- MySQL: localhost:3306
- Redis: localhost:6379
- phpMyAdmin: http://localhost:8080

## 주요 기능

1. **사용자 인증**: 이메일/비밀번호 기반 JWT 인증
2. **API 키 관리**: Bybit API 키 등록 및 검증
3. **실시간 차트**: BTCUSDT 1분봉 실시간 차트
4. **자동매매 설정**: 위험도, 레버리지, GPT 프롬프트 설정
5. **자동매매 실행**: 5분마다 GPT 분석 후 자동 거래
6. **거래 로그**: GPT 판단 결과 및 거래 내역 조회

## 보안 고려사항

- API 키는 AES256 암호화하여 저장
- JWT 토큰은 httpOnly 쿠키로 관리
- 모든 통신은 HTTPS 사용 (프로덕션)
- Redis는 내부 네트워크만 접근 가능

## 라이선스

MIT License