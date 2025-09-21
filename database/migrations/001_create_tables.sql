-- 마이그레이션: 기본 테이블 생성
-- 실행 날짜: 2024-01-01

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    bybit_api_key TEXT,
    bybit_api_secret TEXT,
    max_leverage INT DEFAULT 10,
    auto_trade_enabled BOOLEAN DEFAULT FALSE,
    risk_level ENUM('low', 'medium', 'high') DEFAULT 'medium',
    custom_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_auto_trade (auto_trade_enabled),
    INDEX idx_created_at (created_at)
);

-- 거래 로그 테이블
CREATE TABLE IF NOT EXISTS trade_logs (
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
    INDEX idx_status (status),
    INDEX idx_action (action)
);

-- 시스템 설정 테이블
CREATE TABLE IF NOT EXISTS system_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_setting_key (setting_key)
);