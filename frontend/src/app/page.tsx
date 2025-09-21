import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Crypto Trading
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            GPT 기반 자동매매 시스템
          </p>
        </div>

        <div className="space-y-4">
          <Link
            href="/auth/login"
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            로그인
          </Link>
          
          <Link
            href="/auth/register"
            className="w-full flex justify-center py-3 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            회원가입
          </Link>
        </div>

        <div className="mt-8 text-center">
          <div className="text-sm text-gray-500">
            <p className="mb-2">주요 기능</p>
            <ul className="space-y-1">
              <li>• 실시간 BTCUSDT 차트</li>
              <li>• GPT 기반 매매 분석</li>
              <li>• 자동매매 설정</li>
              <li>• 거래 내역 조회</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}