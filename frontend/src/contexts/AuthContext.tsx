'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { authApi } from '@/lib/api'

interface User {
  id: number
  email: string
  auto_trade_enabled: boolean
  risk_level: string
  max_leverage: number
  has_api_key: boolean
  created_at: string
  updated_at: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // 초기 인증 상태 확인
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const response = await authApi.getMe()
      if (response.success && response.data) {
        setUser(response.data)
      }
    } catch (error) {
      // 인증 실패 시 사용자 정보 초기화
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await authApi.login(email, password)
      
      if (response.success && response.data) {
        setUser(response.data.user)
        return true
      }
      
      return false
    } catch (error) {
      console.error('로그인 실패:', error)
      return false
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('로그아웃 실패:', error)
    } finally {
      setUser(null)
    }
  }

  const refreshUser = async () => {
    try {
      const response = await authApi.getMe()
      if (response.success && response.data) {
        setUser(response.data)
      }
    } catch (error) {
      console.error('사용자 정보 새로고침 실패:', error)
      setUser(null)
    }
  }

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    refreshUser,
    isAuthenticated: !!user,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// 인증이 필요한 페이지를 위한 HOC
export function withAuth<P extends object>(
  Component: React.ComponentType<P>
) {
  return function AuthenticatedComponent(props: P) {
    const { isAuthenticated, loading } = useAuth()
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
      setMounted(true)
    }, [])

    if (!mounted || loading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      )
    }

    if (!isAuthenticated) {
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login'
      }
      return null
    }

    return <Component {...props} />
  }
}