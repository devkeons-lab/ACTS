'use client'

import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts'
import { klineApi } from '@/lib/api'

interface CandleData {
  timestamp: number
  open: string
  high: string
  low: string
  close: string
  volume: string
}

interface ChartProps {
  symbol?: string
  interval?: string
  height?: number
}

export default function Chart({ 
  symbol = 'BTCUSDT', 
  interval = '1', 
  height = 400 
}: ChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastPrice, setLastPrice] = useState<number | null>(null)
  const [priceChange, setPriceChange] = useState<number | null>(null)

  // 차트 초기화
  useEffect(() => {
    if (!chartContainerRef.current) return

    // 차트 생성
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#cccccc',
      },
      timeScale: {
        borderColor: '#cccccc',
        timeVisible: true,
        secondsVisible: false,
      },
    })

    // 캔들스틱 시리즈 추가
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    })

    chartRef.current = chart
    candlestickSeriesRef.current = candlestickSeries

    // 리사이즈 핸들러
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (chartRef.current) {
        chartRef.current.remove()
      }
    }
  }, [height])

  // 데이터 로드
  const loadChartData = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await klineApi.get(symbol, interval, 100)
      
      if (response.success && response.data) {
        const candles = response.data.data as CandleData[]
        
        // 차트 데이터 형식으로 변환
        const chartData: CandlestickData[] = candles.map(candle => ({
          time: (candle.timestamp / 1000) as Time,
          open: parseFloat(candle.open),
          high: parseFloat(candle.high),
          low: parseFloat(candle.low),
          close: parseFloat(candle.close),
        }))

        // 시간순 정렬
        chartData.sort((a, b) => (a.time as number) - (b.time as number))

        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.setData(chartData)
          
          // 가격 정보 업데이트
          if (chartData.length > 0) {
            const latest = chartData[chartData.length - 1]
            const previous = chartData[chartData.length - 2]
            
            setLastPrice(latest.close)
            if (previous) {
              const change = ((latest.close - previous.close) / previous.close) * 100
              setPriceChange(change)
            }
          }
        }
      } else {
        setError(response.error || '차트 데이터를 불러올 수 없습니다.')
      }
    } catch (error) {
      console.error('차트 데이터 로드 실패:', error)
      setError('차트 데이터 로드 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  // 실시간 데이터 업데이트
  const updateLatestCandle = async () => {
    try {
      const response = await klineApi.getLatest(symbol, interval)
      
      if (response.success && response.data) {
        const latestCandle = response.data.candle as CandleData
        
        const newData: CandlestickData = {
          time: (latestCandle.timestamp / 1000) as Time,
          open: parseFloat(latestCandle.open),
          high: parseFloat(latestCandle.high),
          low: parseFloat(latestCandle.low),
          close: parseFloat(latestCandle.close),
        }

        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.update(newData)
          
          // 가격 정보 업데이트
          setLastPrice(newData.close)
          
          // 가격 변화 계산 (이전 캔들과 비교)
          const currentData = candlestickSeriesRef.current.data()
          if (currentData.length > 1) {
            const previous = currentData[currentData.length - 2] as CandlestickData
            const change = ((newData.close - previous.close) / previous.close) * 100
            setPriceChange(change)
          }
        }
      }
    } catch (error) {
      console.error('실시간 데이터 업데이트 실패:', error)
    }
  }

  // 초기 데이터 로드
  useEffect(() => {
    loadChartData()
  }, [symbol, interval])

  // 실시간 업데이트 (30초마다)
  useEffect(() => {
    const interval_id = setInterval(updateLatestCandle, 30000)
    return () => clearInterval(interval_id)
  }, [symbol, interval])

  if (loading) {
    return (
      <div 
        className="flex items-center justify-center bg-white rounded-lg border"
        style={{ height: `${height}px` }}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-sm text-gray-500">차트 로딩 중...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div 
        className="flex items-center justify-center bg-white rounded-lg border"
        style={{ height: `${height}px` }}
      >
        <div className="text-center">
          <p className="text-sm text-red-600 mb-2">{error}</p>
          <button
            onClick={loadChartData}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            다시 시도
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border">
      {/* 차트 헤더 */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {symbol} 차트
            </h3>
            <p className="text-sm text-gray-500">
              {interval}분봉 • 실시간 업데이트
            </p>
          </div>
          
          {lastPrice && (
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                ${lastPrice.toLocaleString()}
              </div>
              {priceChange !== null && (
                <div className={`text-sm font-medium ${
                  priceChange >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 차트 컨테이너 */}
      <div ref={chartContainerRef} className="w-full" />
    </div>
  )
}