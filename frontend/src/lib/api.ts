// API 기본 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

// API 응답 타입
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  timestamp: string
}

// API 클라이언트 클래스
class ApiClient {
  private baseURL: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // 쿠키 포함
    }

    const config = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || data.message || `HTTP ${response.status}`)
      }

      return data
    } catch (error) {
      console.error('API 요청 실패:', error)
      throw error
    }
  }

  // GET 요청
  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  // POST 요청
  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // PUT 요청
  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // DELETE 요청
  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

// API 클라이언트 인스턴스
export const api = new ApiClient()

// 인증 관련 API
export const authApi = {
  register: (email: string, password: string) =>
    api.post('/api/auth/register', { email, password }),
  
  login: (email: string, password: string) =>
    api.post('/api/auth/login', { email, password }),
  
  logout: () =>
    api.post('/api/auth/logout'),
  
  getMe: () =>
    api.get('/api/auth/me'),
  
  verifyToken: () =>
    api.get('/api/auth/verify'),
}

// API 키 관련 API
export const apiKeyApi = {
  save: (apiKey: string, apiSecret: string, validate: boolean = true) =>
    api.post('/api/apikey', { api_key: apiKey, api_secret: apiSecret, validate }),
  
  get: () =>
    api.get('/api/apikey'),
  
  update: (apiKey: string, apiSecret: string, validate: boolean = true) =>
    api.put('/api/apikey', { api_key: apiKey, api_secret: apiSecret, validate }),
  
  delete: () =>
    api.delete('/api/apikey'),
  
  validate: (apiKey: string, apiSecret: string) =>
    api.post('/api/apikey/validate', { api_key: apiKey, api_secret: apiSecret }),
  
  getStatus: () =>
    api.get('/api/apikey/status'),
}

// 캔들 데이터 관련 API
export const klineApi = {
  get: (symbol: string = 'BTCUSDT', interval: string = '1', count: number = 30) =>
    api.get(`/api/kline?symbol=${symbol}&interval=${interval}&count=${count}`),
  
  getLatest: (symbol: string = 'BTCUSDT', interval: string = '1') =>
    api.get(`/api/kline/latest?symbol=${symbol}&interval=${interval}`),
  
  getStatus: (symbol: string = 'BTCUSDT', interval: string = '1') =>
    api.get(`/api/kline/status?symbol=${symbol}&interval=${interval}`),
  
  getSymbols: () =>
    api.get('/api/kline/symbols'),
  
  getSymbolInfo: (symbol: string) =>
    api.get(`/api/kline/symbol/${symbol}`),
}

// 설정 관련 API
export const settingsApi = {
  get: () =>
    api.get('/api/settings'),
  
  update: (settings: {
    auto_trade_enabled?: boolean
    risk_level?: string
    max_leverage?: number
    preferred_symbol?: string
    preferred_interval?: string
    custom_prompt?: string
  }) =>
    api.post('/api/settings', settings),
  
  toggleAutoTrade: () =>
    api.post('/api/settings/auto-trade/toggle'),
  
  setAutoTrade: (enabled: boolean) =>
    api.post('/api/settings/auto-trade', { enabled }),
  
  getDefaultPrompt: () =>
    api.get('/api/settings/gpt-prompt/default'),
  
  reset: () =>
    api.post('/api/settings/reset'),
  
  validate: () =>
    api.get('/api/settings/validation'),
  
  getRecommendations: (riskLevel: string) =>
    api.get(`/api/settings/recommendations/${riskLevel}`),
}

// 거래 로그 관련 API
export const tradeLogsApi = {
  get: (page: number = 1, limit: number = 20) =>
    api.get(`/api/logs?page=${page}&limit=${limit}`),
  
  getById: (id: number) =>
    api.get(`/api/logs/${id}`),
}