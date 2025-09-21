import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPrice(price: number | string): string {
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numPrice)
}

export function formatPercentage(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

export function formatVolume(volume: number | string): string {
  const numVolume = typeof volume === 'string' ? parseFloat(volume) : volume
  
  if (numVolume >= 1000000) {
    return `${(numVolume / 1000000).toFixed(1)}M`
  } else if (numVolume >= 1000) {
    return `${(numVolume / 1000).toFixed(1)}K`
  }
  
  return numVolume.toFixed(2)
}

export function formatTimestamp(timestamp: number): string {
  return new Date(timestamp).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function getRiskLevelColor(riskLevel: string): string {
  switch (riskLevel) {
    case 'low':
      return 'text-green-600 bg-green-100'
    case 'medium':
      return 'text-yellow-600 bg-yellow-100'
    case 'high':
      return 'text-red-600 bg-red-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

export function getRiskLevelText(riskLevel: string): string {
  switch (riskLevel) {
    case 'low':
      return '낮음'
    case 'medium':
      return '보통'
    case 'high':
      return '높음'
    default:
      return '알 수 없음'
  }
}