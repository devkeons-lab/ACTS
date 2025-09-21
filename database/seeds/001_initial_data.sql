-- 시드 데이터: 초기 시스템 설정 및 테스트 데이터

-- 시스템 설정 데이터
INSERT IGNORE INTO system_settings (setting_key, setting_value) VALUES
('default_gpt_prompt', '당신은 고도로 숙련된 암호화폐 트레이더입니다. 제공된 BTCUSDT 1분봉 차트 데이터를 분석하여 매매 판단을 내려주세요. 응답은 반드시 JSON 형식으로 해주세요: {"action": "buy|sell|hold", "confidence": 0.0-1.0, "leverage": 1-20, "reason": "판단 근거"}'),
('max_users_per_execution', '100'),
('trading_enabled', 'true'),
('min_confidence_threshold', '0.7'),
('max_daily_trades_per_user', '50'),
('system_maintenance_mode', 'false');

-- 개발용 테스트 사용자
-- 비밀번호: testpassword123
INSERT IGNORE INTO users (email, password_hash, auto_trade_enabled, risk_level, max_leverage) VALUES
('test@crypto-trading.com', '$2b$10$K8gF7Z9X1Y2Z3A4B5C6D7E8F9G0H1I2J3K4L5M6N7O8P9Q0R1S2T3U', false, 'medium', 10),
('demo@crypto-trading.com', '$2b$10$K8gF7Z9X1Y2Z3A4B5C6D7E8F9G0H1I2J3K4L5M6N7O8P9Q0R1S2T3U', true, 'low', 5),
('admin@crypto-trading.com', '$2b$10$K8gF7Z9X1Y2Z3A4B5C6D7E8F9G0H1I2J3K4L5M6N7O8P9Q0R1S2T3U', false, 'high', 20);