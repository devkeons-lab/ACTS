'use client'

import { useState, useEffect } from 'react'
import { withAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiKeyApi } from '@/lib/api'
import Link from 'next/link'

interface ApiKeyInfo {
  api_key_masked: string
  has_api_secret: boolean
  updated_at: string
  error?: string
}

function ApiKeyPage() {
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [currentApiKey, setCurrentApiKey] = useState<ApiKeyInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [validating, setValidating] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [validationResult, setValidationResult] = useState<any>(null)

  // 현재 API 키 정보 로드
  const loadApiKeyInfo = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await apiKeyApi.get()
      
      if (response.success) {
        setCurrentApiKey(response.data)
      } else {
        setCurrentApiKey(null)
      }
    } catch (error) {
      console.error('API 키 정보 로드 실패:', error)
      setError('API 키 정보를 불러올 수 없습니다.')
    } finally {
      setLoading(false)
    }
  }

  // API 키 검증
  const validateApiKey = async () => {
    if (!apiKey.trim() || !apiSecret.trim()) {
      setError('API 키와 시크릿 키를 모두 입력해주세요.')
      return
    }

    try {
      setValidating(true)
      setError(null)
      setValidationResult(null)

      const response = await apiKeyApi.validate(apiKey.trim(), apiSecret.trim())
      
      if (response.success && response.data) {
        setValidationResult(response.data)
        if (response.data.valid) {
          setSuccess('API 키 검증이 완료되었습니다!')
        } else {
          setError('API 키 검증에 실패했습니다.')
        }
      } else {
        setError(response.error || 'API 키 검증 중 오류가 발생했습니다.')
      }
    } catch (error) {
      console.error('API 키 검증 실패:', error)
      setError(error instanceof Error ? error.message : 'API 키 검증 중 오류가 발생했습니다.')
    } finally {
      setValidating(false)
    }
  }

  // API 키 저장
  const saveApiKey = async () => {
    if (!apiKey.trim() || !apiSecret.trim()) {
      setError('API 키와 시크릿 키를 모두 입력해주세요.')
      return
    }

    try {
      setSaving(true)
      setError(null)
      setSuccess(null)

      const response = currentApiKey 
        ? await apiKeyApi.update(apiKey.trim(), apiSecret.trim())
        : await apiKeyApi.save(apiKey.trim(), apiSecret.trim())
      
      if (response.success) {
        setSuccess(currentApiKey ? 'API 키가 수정되었습니다!' : 'API 키가 저장되었습니다!')
        setApiKey('')
        setApiSecret('')
        setValidationResult(null)
        await loadApiKeyInfo()
      } else {
        setError(response.error || 'API 키 저장에 실패했습니다.')
      }
    } catch (error) {
      console.error('API 키 저장 실패:', error)
      setError(error instanceof Error ? error.message : 'API 키 저장 중 오류가 발생했습니다.')
    } finally {
      setSaving(false)
    }
  }

  // API 키 삭제
  const deleteApiKey = async () => {
    if (!confirm('정말로 API 키를 삭제하시겠습니까? 자동매매가 중단됩니다.')) {
      return
    }

    try {
      setDeleting(true)
      setError(null)

      const response = await apiKeyApi.delete()
      
      if (response.success) {
        setSuccess('API 키가 삭제되었습니다.')
        setCurrentApiKey(null)
        setApiKey('')
        setApiSecret('')
        setValidationResult(null)
      } else {
        setError(response.error || 'API 키 삭제에 실패했습니다.')
      }
    } catch (error) {
      console.error('API 키 삭제 실패:', error)
      setError('API 키 삭제 중 오류가 발생했습니다.')
    } finally {
      setDeleting(false)
    }
  }

  // 초기 로드
  useEffect(() => {
    loadApiKeyInfo()
  }, [])

  // 성공 메시지 자동 제거
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [success])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">API 키 관리</h1>
              <p className="text-sm text-gray-500">Bybit API 키 등록 및 관리</p>
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
          {/* 현재 API 키 상태 */}
          {!loading && (
            <Card>
              <CardHeader>
                <CardTitle>현재 상태</CardTitle>
                <CardDescription>
                  등록된 API 키 정보
                </CardDescription>
              </CardHeader>
              <CardContent>
                {currentApiKey ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
                      <div>
                        <p className="font-medium text-green-800">API 키가 등록되어 있습니다</p>
                        <p className="text-sm text-green-600">
                          API 키: {currentApiKey.api_key_masked}
                        </p>
                        <p className="text-sm text-green-600">
                          등록일: {new Date(currentApiKey.updated_at).toLocaleString('ko-KR')}
                        </p>
                      </div>
                      <Button
                        onClick={deleteApiKey}
                        disabled={deleting}
                        variant="destructive"
                        size="sm"
                      >
                        {deleting ? '삭제 중...' : '삭제'}
                      </Button>
                    </div>
                    
                    {currentApiKey.error && (
                      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-800">{currentApiKey.error}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="font-medium text-yellow-800">API 키가 등록되지 않았습니다</p>
                    <p className="text-sm text-yellow-600">
                      자동매매를 사용하려면 Bybit API 키를 등록해주세요.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* API 키 등록/수정 폼 */}
          <Card>
            <CardHeader>
              <CardTitle>
                {currentApiKey ? 'API 키 수정' : 'API 키 등록'}
              </CardTitle>
              <CardDescription>
                Bybit API 키와 시크릿 키를 입력해주세요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
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

              <div>
                <label htmlFor="apiKey" className="trading-label">
                  API Key
                </label>
                <Input
                  id="apiKey"
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Bybit API Key를 입력하세요"
                  disabled={saving || validating || deleting}
                />
              </div>

              <div>
                <label htmlFor="apiSecret" className="trading-label">
                  API Secret
                </label>
                <Input
                  id="apiSecret"
                  type="password"
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  placeholder="Bybit API Secret을 입력하세요"
                  disabled={saving || validating || deleting}
                />
              </div>

              {/* 검증 결과 */}
              {validationResult && (
                <div className={`p-4 rounded-lg border ${
                  validationResult.valid 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <p className={`font-medium ${
                    validationResult.valid ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {validationResult.valid ? '✓ 검증 성공' : '✗ 검증 실패'}
                  </p>
                  <p className={`text-sm ${
                    validationResult.valid ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {validationResult.message}
                  </p>
                  {validationResult.account_info && (
                    <div className="mt-2 text-sm text-green-600">
                      <p>계정 타입: {validationResult.account_info.account_type}</p>
                      <p>권한: {validationResult.permissions?.join(', ')}</p>
                    </div>
                  )}
                </div>
              )}

              <div className="flex space-x-4">
                <Button
                  onClick={validateApiKey}
                  disabled={!apiKey.trim() || !apiSecret.trim() || validating || saving}
                  variant="outline"
                  className="flex-1"
                >
                  {validating ? '검증 중...' : '검증하기'}
                </Button>

                <Button
                  onClick={saveApiKey}
                  disabled={!apiKey.trim() || !apiSecret.trim() || saving || validating}
                  className="flex-1"
                >
                  {saving ? '저장 중...' : (currentApiKey ? '수정하기' : '저장하기')}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* API 키 생성 가이드 */}
          <Card>
            <CardHeader>
              <CardTitle>API 키 생성 가이드</CardTitle>
              <CardDescription>
                Bybit에서 API 키를 생성하는 방법
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-sm">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">1. Bybit 계정 로그인</h4>
                  <p className="text-gray-600">
                    <a 
                      href="https://www.bybit.com" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800"
                    >
                      Bybit 웹사이트
                    </a>에 로그인하세요.
                  </p>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">2. API 관리 페이지 이동</h4>
                  <p className="text-gray-600">
                    계정 설정 → API 관리 → API 키 생성을 클릭하세요.
                  </p>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">3. 권한 설정</h4>
                  <p className="text-gray-600">
                    다음 권한을 활성화해주세요:
                  </p>
                  <ul className="list-disc list-inside mt-1 text-gray-600 space-y-1">
                    <li>Read (읽기)</li>
                    <li>Spot Trading (현물 거래)</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">4. IP 제한 (선택사항)</h4>
                  <p className="text-gray-600">
                    보안을 위해 IP 주소를 제한할 수 있습니다.
                  </p>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <strong>주의:</strong> API 키와 시크릿은 안전하게 보관하세요. 
                    다른 사람과 공유하지 마시고, 의심스러운 활동이 있으면 즉시 키를 삭제하세요.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}

export default withAuth(ApiKeyPage)