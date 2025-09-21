// 공통 타입 정의

// 사용자 관련 타입
export interface User {
  id: number;
  email: string;
  password_hash: string;
  bybit_api_key?: string;
  bybit_api_secret?: string;
  max_leverage: number;
  auto_trade_enabled: boolean;
  risk_level: 'low' | 'medium' | 'high';
  custom_prompt?: string;
  created_at: Date;
  updated_at: Date;
}

export interface UserSettings {
  max_leverage: number;
  auto_trade_enabled: boolean;
  risk_level: 'low' | 'medium' | 'high';
  custom_prompt?: string;
}

// 거래 로그 관련 타입
export interface TradeLog {
  id: number;
  user_id: number;
  gpt_analysis: GPTAnalysis;
  action: 'buy' | 'sell' | 'hold';
  leverage: number;
  order_id?: string;
  status: 'success' | 'failed' | 'pending';
  error_message?: string;
  executed_at: Date;
}

// GPT 분석 결과 타입
export interface GPTAnalysis {
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  leverage: number;
  reason: string;
  stop_loss?: number;
  take_profit?: number;
  indicators?: {
    rsi?: number;
    macd?: string;
    bollinger?: string;
    volume?: string;
  };
}

// 캔들 데이터 타입
export interface CandleData {
  timestamp: number;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
}

// API 응답 타입
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// Bybit API 키 타입
export interface BybitApiKey {
  api_key: string;
  api_secret: string;
  testnet?: boolean;
}

// 시스템 설정 타입
export interface SystemSetting {
  id: number;
  setting_key: string;
  setting_value: string;
  updated_at: Date;
}

// 자동매매 설정 타입
export interface AutoTradeConfig {
  user_id: number;
  risk_level: 'low' | 'medium' | 'high';
  max_leverage: number;
  custom_prompt?: string;
  enabled: boolean;
}

// Redis 키 타입
export type RedisKey = 
  | `kline:${string}:${string}`  // kline:BTCUSDT:1m
  | `system:status`
  | `user:${number}:settings`;

// 환경 변수 타입
export interface EnvConfig {
  NODE_ENV: 'development' | 'production' | 'test';
  DATABASE_URL: string;
  REDIS_URL: string;
  BYBIT_API_URL: string;
  OPENAI_API_KEY: string;
  JWT_SECRET: string;
  ENCRYPTION_KEY: string;
  DATA_SERVER_PORT: number;
  AUTO_SERVER_PORT: number;
  API_SERVER_PORT: number;
}