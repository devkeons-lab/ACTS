-- 코인 자동매매 시스템 데이터베이스 초기화 스크립트

USE crypto_trading;

-- 사용자 테이블
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    bybit_api_key TEXT,
    bybit_api_secret TEXT,
    max_leverage INT DEFAULT 10,
    auto_trade_enabled BOOLEAN DEFAULT FALSE,
    risk_level ENUM('low', 'medium', 'high') DEFAULT 'medium',
    preferred_symbol VARCHAR(20) DEFAULT 'BTCUSDT',
    preferred_interval VARCHAR(10) DEFAULT '1',
    custom_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_auto_trade (auto_trade_enabled),
    INDEX idx_preferred_symbol (preferred_symbol)
);

-- 거래 로그 테이블
CREATE TABLE trade_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    gpt_analysis JSON,
    action ENUM('buy', 'sell', 'hold'),
    leverage DECIMAL(5,2),
    order_id VARCHAR(100),
    status ENUM('success', 'failed', 'pending'),
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_executed_at (executed_at),
    INDEX idx_status (status)
);

-- 시스템 설정 테이블
CREATE TABLE system_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_setting_key (setting_key)
);

-- 초기 시스템 설정 데이터
INSERT INTO system_settings (setting_key, setting_value) VALUES
('default_gpt_prompt', '당신은 고도로 숙련된 암호화폐 트레이더입니다. 제공된 BTCUSDT 1분봉 차트 데이터를 분석하여 매매 판단을 내려주세요.'),
('max_users_per_execution', '100'),
('trading_enabled', 'true');

-- 테스트 사용자 생성 (개발용)
-- 비밀번호: testpassword (bcrypt 해시)
INSERT INTO users (email, password_hash, auto_trade_enabled, risk_level, max_leverage) VALUES
('test@example.com', '$2b$10$K8gF7Z9X1Y2Z3A4B5C6D7E8F9G0H1I2J3K4L5M6N7O8P9Q0R1S2T3U', false, 'medium', 10),
('demo@example.com', '$2b$10$K8gF7Z9X1Y2Z3A4B5C6D7E8F9G0H1I2J3K4L5M6N7O8P9Q0R1S2T3U', true, 'low', 5);

-- 샘플 거래 로그 데이터 (개발용)
INSERT INTO trade_logs (user_id, gpt_analysis, action, leverage, status, executed_at) VALUES
(1, '{"confidence": 0.7, "reason": "RSI 과매도 구간, 지지선 터치", "indicators": {"rsi": 25, "macd": "bullish"}}', 'buy', 3.00, 'success', DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(1, '{"confidence": 0.8, "reason": "저항선 돌파, 거래량 증가", "indicators": {"rsi": 65, "macd": "bearish"}}', 'sell', 2.50, 'success', DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
(2, '{"confidence": 0.6, "reason": "횡보 구간, 명확한 신호 없음", "indicators": {"rsi": 50, "macd": "neutral"}}', 'hold', 0.00, 'success', DATE_SUB(NOW(), INTERVAL 15 MINUTE));