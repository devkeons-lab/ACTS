'use client'

import { useState } from 'react'
import { withAuth } from '@/contexts/AuthContext'
import Chart from '@/components/Chart'
import GptControlPanel from '@/components/GptControlPanel'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

interface UserSettings {
  auto_trade_enabled: boolean
  risk_level: string
  max_leverage: number
  has_api_key: boolean
  updated_at: string
}

function DashboardPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null)

  const handleSettingsChange = (newSettings: UserSettings) => {
    setSettings(newSettings)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
              <p className="text-sm text-gray-500">실시간 차트 및 자동매매 제어</p>
            </div>
            
            <nav className="flex space-x-4">
              <Link
                href="/dashboard/api-key"
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                API 키 관리
              </Link>
              <Link
                href="/dashboard/settings"
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                설정
              </Link>
              <Link
                href="/dashboard/logs"
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                거래 로그
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 차트 영역 */}
          <div className="lg:col-span-2">
            <Chart height={500} />
          </div>

          {/* 제어 패널 영역 */}
          <div className="space-y-6">
            {/* 자동매매 제어 패널 */}
            <GptControlPanel onSettingsChange={handleSettingsChange} />

            {/* 빠른 액션 카드 */}
            <Card>
              <CardHeader>
                <CardTitle>빠른 액션</CardTitle>
                <CardDescription>
                  자주 사용하는 기능들
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Link href="/dashboard/api-key" className="block">
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    disabled={settings?.has_api_key}
                  >
                    {settings?.has_api_key ? '✓ API 키 등록됨' : 'API 키 등록'}
                  </Button>
                </Link>
                
                <Link href="/dashboard/settings" className="block">
                  <Button variant="outline" className="w-full justify-start">
                    고급 설정
                  </Button>
                </Link>
                
                <Link href="/dashboard/logs" className="block">
                  <Button variant="outline" className="w-full justify-start">
                    거래 내역 보기
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* 시스템 상태 카드 */}
            <Card>
              <CardHeader>
                <CardTitle>시스템 상태</CardTitle>
                <CardDescription>
                  현재 시스템 운영 상태
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">차트 데이터:</span>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      <span className="text-green-600 font-medium">정상</span>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">자동매매 서버:</span>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      <span className="text-green-600 font-medium">정상</span>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">API 연결:</span>
                    <div className="flex items-center">
                      <div className={`w-2 h-2 rounded-full mr-2 ${
                        settings?.has_api_key ? 'bg-green-500' : 'bg-gray-400'
                      }`}></div>
                      <span className={`font-medium ${
                        settings?.has_api_key ? 'text-green-600' : 'text-gray-500'
                      }`}>
                        {settings?.has_api_key ? '연결됨' : '미연결'}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* 하단 정보 섹션 */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">실시간 차트</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                BTCUSDT 1분봉 차트를 실시간으로 확인하고 시장 동향을 파악하세요.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">GPT 분석</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                AI가 5분마다 시장을 분석하여 최적의 매매 타이밍을 찾아드립니다.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">자동 실행</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                설정한 위험도에 따라 자동으로 매매를 실행하여 24시간 거래가 가능합니다.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}

export default withAuth(DashboardPage)