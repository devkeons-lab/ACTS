'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { settingsApi } from '@/lib/api'
import { getRiskLevelColor, getRiskLevelText } from '@/lib/utils'

interface UserSettings {
  auto_trade_enabled: boolean
  risk_level: string
  max_leverage: number
  has_api_key: boolean
  updated_at: string
}

interface GptControlPanelProps {
  onSettingsChange?: (settings: UserSettings) => void
}

export default function GptControlPanel({ onSettingsChange }: GptControlPanelProps) {
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 설정 로드
  const loadSettings = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await settingsApi.get()
      
      if (response.success && response.data) {
        setSettings(response.data)
        onSettingsChange?.(response.data)
      } else {
        setError(response.error || '설정을 불러올 수 없습니다.')
      }
    } catch (error) {
      console.error('설정 로드 실패:', error)
      setError('설정 로드 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  // 자동매매 토글
  const toggleAutoTrade = async () => {
    if (!settings) return

    try {
      setUpdating(true)
      setError(null)

      const response = await settingsApi.toggleAutoTrade()
      
      if (response.success && response.data) {
        setSettings(response.data.settings)
        onSettingsChange?.(response.data.settings)
      } else {
        setError(response.error || '설정 변경에 실패했습니다.')
      }
    } catch (error) {
      console.error('자동매매 토글 실패:', error)
      setError('설정 변경 중 오류가 발생했습니다.')
    } finally {
      setUpdating(false)
    }
  }

  // 위험도 변경
  const changeRiskLevel = async (newRiskLevel: string) => {
    if (!settings) return

    try {
      setUpdating(true)
      setError(null)

      const response = await settingsApi.update({
        risk_level: newRiskLevel
      })
      
      if (response.success && response.data) {
        setSettings(response.data)
        onSettingsChange?.(response.data)
      } else {
        setError(response.error || '위험도 변경에 실패했습니다.')
      }
    } catch (error) {
      console.error('위험도 변경 실패:', error)
      setError('위험도 변경 중 오류가 발생했습니다.')
    } finally {
      setUpdating(false)
    }
  }

  // 초기 로드
  useEffect(() => {
    loadSettings()
  }, [])

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!settings) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error || '설정을 불러올 수 없습니다.'}</p>
            <Button onClick={loadSettings} variant="outline">
              다시 시도
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>자동매매 제어</span>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            settings.auto_trade_enabled 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-800'
          }`}>
            {settings.auto_trade_enabled ? '활성화' : '비활성화'}
          </div>
        </CardTitle>
        <CardDescription>
          GPT 기반 자동매매 설정을 관리하세요
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* API 키 상태 확인 */}
        {!settings.has_api_key && (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-md text-sm">
            <p className="font-medium">API 키가 등록되지 않았습니다</p>
            <p>자동매매를 사용하려면 먼저 Bybit API 키를 등록해주세요.</p>
          </div>
        )}

        {/* 자동매매 토글 */}
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium text-gray-900">자동매매</h4>
            <p className="text-sm text-gray-500">
              GPT 분석을 통한 자동 거래 실행
            </p>
          </div>
          
          <Button
            onClick={toggleAutoTrade}
            disabled={updating || !settings.has_api_key}
            variant={settings.auto_trade_enabled ? "destructive" : "default"}
            size="sm"
          >
            {updating ? '변경 중...' : (
              settings.auto_trade_enabled ? '비활성화' : '활성화'
            )}
          </Button>
        </div>

        {/* 위험도 설정 */}
        <div>
          <h4 className="font-medium text-gray-900 mb-3">위험도 설정</h4>
          <div className="grid grid-cols-3 gap-2">
            {['low', 'medium', 'high'].map((level) => (
              <button
                key={level}
                onClick={() => changeRiskLevel(level)}
                disabled={updating}
                className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
                  settings.risk_level === level
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <div className={`w-3 h-3 rounded-full mx-auto mb-1 ${getRiskLevelColor(level)}`}></div>
                {getRiskLevelText(level)}
              </button>
            ))}
          </div>
          
          <div className="mt-2 text-xs text-gray-500">
            현재 설정: <span className="font-medium">{getRiskLevelText(settings.risk_level)}</span>
            {settings.risk_level === 'low' && ' - 안전한 거래, 낮은 레버리지'}
            {settings.risk_level === 'medium' && ' - 균형잡힌 거래, 적당한 레버리지'}
            {settings.risk_level === 'high' && ' - 공격적 거래, 높은 레버리지'}
          </div>
        </div>

        {/* 현재 설정 정보 */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">현재 설정</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">최대 레버리지:</span>
              <span className="font-medium">{settings.max_leverage}x</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">위험도:</span>
              <span className="font-medium">{getRiskLevelText(settings.risk_level)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">API 키 상태:</span>
              <span className={`font-medium ${
                settings.has_api_key ? 'text-green-600' : 'text-red-600'
              }`}>
                {settings.has_api_key ? '등록됨' : '미등록'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">마지막 업데이트:</span>
              <span className="font-medium">
                {new Date(settings.updated_at).toLocaleString('ko-KR')}
              </span>
            </div>
          </div>
        </div>

        {/* 자동매매 활성화 시 주의사항 */}
        {settings.auto_trade_enabled && (
          <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-md text-sm">
            <p className="font-medium">자동매매가 활성화되었습니다</p>
            <p>GPT가 5분마다 시장을 분석하여 자동으로 거래를 실행합니다.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}