'use client'

import { useState, useEffect } from 'react'
import { withAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { settingsApi } from '@/lib/api'
import { getRiskLevelColor, getRiskLevelText } from '@/lib/utils'
import Link from 'next/link'

interface UserSettings {
  auto_trade_enabled: boolean
  risk_level: string
  max_leverage: number
  custom_prompt: string | null
  has_api_key: boolean
  updated_at: string
}

interface RiskRecommendation {
  max_leverage: number
  description: string
  features: string[]
}

function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [maxLeverage, setMaxLeverage] = useState<number>(10)
  const [customPrompt, setCustomPrompt] = useState<string>('')
  const [defaultPrompt, setDefaultPrompt] = useState<string>('')
  const [recommendations, setRecommendations] = useState<Record<string, RiskRecommendation>>({})
  
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // 설정 로드
  const loadSettings = async () => {
    try {
      setLoading(true)
      setError(null)

      const [settingsResponse, promptResponse] = await Promise.all([
        settingsApi.get(),
        settingsApi.getDefaultPrompt()
      ])
      
      if (settingsResponse.success && settingsResponse.data) {
        const data = settingsResponse.data
        setSettings(data)
        setMaxLeverage(data.max_leverage)
        setCustomPrompt(data.custom_prompt || '')
      }

      if (promptResponse.success && promptResponse.data) {
        setDefaultPrompt(promptResponse.data.default_prompt)
      }

      // 위험도별 추천 설정 로드
      await loadRecommendations()

    } catch (error) {
      console.error('설정 로드 실패:', error)
      setError('설정을 불러올 수 없습니다.')
    } finally {
      setLoading(false)
    }
  }

  // 위험도별 추천 설정 로드
  const loadRecommendations = async () => {
    try {
      const riskLevels = ['low', 'medium', 'high']
      const recommendationPromises = riskLevels.map(level => 
        settingsApi.getRecommendations(level)
      )

      const responses = await Promise.all(recommendationPromises)
      const newRecommendations: Record<string, RiskRecommendation> = {}

      responses.forEach((response, index) => {
        if (response.success && response.data) {
          newRecommendations[riskLevels[index]] = response.data.recommendations
        }
      })

      setRecommendations(newRecommendations)
    } catch (error) {
      console.error('추천 설정 로드 실패:', error)
    }
  }

  // 위험도 변경
  const changeRiskLevel = async (newRiskLevel: string) => {
    if (!settings) return

    try {
      setSaving(true)
      setError(null)

      const response = await settingsApi.update({
        risk_level: newRiskLevel
      })
      
      if (response.success && response.data) {
        setSettings(response.data)
        
        // 추천 레버리지로 자동 설정
        const recommendation = recommendations[newRiskLevel]
        if (recommendation) {
          setMaxLeverage(recommendation.max_leverage)
        }
        
        setSuccess(`위험도가 ${getRiskLevelText(newRiskLevel)}으로 변경되었습니다.`)
      } else {
        setError(response.error || '위험도 변경에 실패했습니다.')
      }
    } catch (error) {
      console.error('위험도 변경 실패:', error)
      setError('위험도 변경 중 오류가 발생했습니다.')
    } finally {
      setSaving(false)
    }
  }

  // 설정 저장
  const saveSettings = async () => {
    if (!settings) return

    try {
      setSaving(true)
      setError(null)

      const response = await settingsApi.update({
        max_leverage: maxLeverage,
        custom_prompt: customPrompt.trim() || null
      })
      
      if (response.success && response.data) {
        setSettings(response.data)
        setSuccess('설정이 저장되었습니다!')
      } else {
        setError(response.error || '설정 저장에 실패했습니다.')
      }
    } catch (error) {
      console.error('설정 저장 실패:', error)
      setError('설정 저장 중 오류가 발생했습니다.')
    } finally {
      setSaving(false)
    }
  }

  // 설정 초기화
  const resetSettings = async () => {
    if (!confirm('모든 설정을 초기값으로 되돌리시겠습니까?')) {
      return
    }

    try {
      setSaving(true)
      setError(null)

      const response = await settingsApi.reset()
      
      if (response.success && response.data) {
        setSettings(response.data)
        setMaxLeverage(response.data.max_leverage)
        setCustomPrompt(response.data.custom_prompt || '')
        setSuccess('설정이 초기화되었습니다.')
      } else {
        setError(response.error || '설정 초기화에 실패했습니다.')
      }
    } catch (error) {
      console.error('설정 초기화 실패:', error)
      setError('설정 초기화 중 오류가 발생했습니다.')
    } finally {
      setSaving(false)
    }
  }

  // 기본 프롬프트 사용
  const useDefaultPrompt = () => {
    setCustomPrompt(defaultPrompt)
  }

  // 초기 로드
  useEffect(() => {
    loadSettings()
  }, [])

  // 성공 메시지 자동 제거
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [success])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">자동매매 설정</h1>
              <p className="text-sm text-gray-500">위험도, 레버리지, GPT 프롬프트 설정</p>
            </div>
            
            <Link
              href="/dashboard"
              className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              ← 대시보드로
            </Link>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md text-sm">
              {success}
            </div>
          )}

          {/* 위험도 설정 */}
          <Card>
            <CardHeader>
              <CardTitle>위험도 설정</CardTitle>
              <CardDescription>
                투자 성향에 맞는 위험도를 선택하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {['low', 'medium', 'high'].map((level) => {
                  const recommendation = recommendations[level]
                  const isSelected = settings?.risk_level === level
                  
                  return (
                    <div
                      key={level}
                      className={`p-4 rounded-lg border cursor-pointer transition-all ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 bg-white hover:bg-gray-50'
                      }`}
                      onClick={() => changeRiskLevel(level)}
                    >
                      <div className="flex items-center mb-2">
                        <div className={`w-3 h-3 rounded-full mr-2 ${getRiskLevelColor(level)}`}></div>
                        <h3 className="font-medium text-gray-900">
                          {getRiskLevelText(level)}
                        </h3>
                        {isSelected && (
                          <div className="ml-auto">
                            <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                              <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {recommendation && (
                        <div>
                          <p className="text-sm text-gray-600 mb-2">
                            {recommendation.description}
                          </p>
                          <p className="text-xs text-gray-500">
                            추천 레버리지: {recommendation.max_leverage}x
                          </p>
                          <ul className="text-xs text-gray-500 mt-1 space-y-1">
                            {recommendation.features.map((feature, index) => (
                              <li key={index}>• {feature}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* 레버리지 설정 */}
          <Card>
            <CardHeader>
              <CardTitle>최대 레버리지</CardTitle>
              <CardDescription>
                자동매매에서 사용할 최대 레버리지를 설정하세요 (1-100x)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label htmlFor="leverage" className="trading-label">
                    최대 레버리지: {maxLeverage}x
                  </label>
                  <input
                    id="leverage"
                    type="range"
                    min="1"
                    max="100"
                    value={maxLeverage}
                    onChange={(e) => setMaxLeverage(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    disabled={saving}
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>1x (안전)</span>
                    <span>50x (보통)</span>
                    <span>100x (위험)</span>
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">레버리지 안내</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>• 1-5x: 안전한 거래, 낮은 위험</p>
                    <p>• 6-20x: 균형잡힌 거래, 중간 위험</p>
                    <p>• 21x 이상: 공격적 거래, 높은 위험</p>
                  </div>
                  <p className="text-xs text-red-600 mt-2">
                    높은 레버리지는 큰 수익과 함께 큰 손실의 위험도 있습니다.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* GPT 프롬프트 설정 */}
          <Card>
            <CardHeader>
              <CardTitle>GPT 프롬프트 설정</CardTitle>
              <CardDescription>
                GPT가 시장 분석 시 사용할 프롬프트를 커스터마이징하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label htmlFor="customPrompt" className="trading-label">
                    커스텀 프롬프트
                  </label>
                  <Button
                    onClick={useDefaultPrompt}
                    variant="outline"
                    size="sm"
                    disabled={saving}
                  >
                    기본값 사용
                  </Button>
                </div>
                <textarea
                  id="customPrompt"
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="GPT가 사용할 커스텀 프롬프트를 입력하세요..."
                  className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  disabled={saving}
                />
                <p className="text-xs text-gray-500 mt-1">
                  {customPrompt.length}/2000 글자
                </p>
              </div>

              {defaultPrompt && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">기본 프롬프트</h4>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">
                    {defaultPrompt}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 저장 버튼 */}
          <div className="flex justify-between">
            <Button
              onClick={resetSettings}
              variant="outline"
              disabled={saving}
            >
              설정 초기화
            </Button>

            <Button
              onClick={saveSettings}
              disabled={saving}
              className="px-8"
            >
              {saving ? '저장 중...' : '설정 저장'}
            </Button>
          </div>
        </div>
      </main>
    </div>
  )
}

export default withAuth(SettingsPage)