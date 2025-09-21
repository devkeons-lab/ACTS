import os
import sys
import json
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.types import CandleData, GPTAnalysis, TradeAction
from shared.utils import log_info, log_error

class GPTAnalysisService:
    """GPT 기반 매매 분석 서비스"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.model = "gpt-4"  # 또는 "gpt-3.5-turbo"
        self.max_tokens = 500
        self.temperature = 0.3  # 일관성을 위해 낮은 값
    
    async def analyze_candles(
        self,
        candles: List[CandleData],
        user_config: Dict[str, Any]
    ) -> GPTAnalysis:
        """캔들 데이터 분석"""
        try:
            # 프롬프트 생성
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(candles, user_config)
            
            log_info("GPT 분석 시작", {
                "candles_count": len(candles),
                "user_risk_level": user_config.get('risk_level', 'medium'),
                "max_leverage": user_config.get('max_leverage', 10)
            })
            
            # GPT API 호출
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # 응답 파싱
            analysis_result = self._parse_gpt_response(response.choices[0].message.content)
            
            log_info("GPT 분석 완료", {
                "action": analysis_result.action,
                "confidence": analysis_result.confidence,
                "leverage": analysis_result.leverage
            })
            
            return analysis_result
            
        except Exception as error:
            log_error("GPT 분석 실패", {
                "error": str(error),
                "candles_count": len(candles) if candles else 0
            })
            
            # 실패 시 기본 응답 (보류)
            return GPTAnalysis(
                action=TradeAction.HOLD,
                confidence=0.0,
                leverage=1,
                reason=f"GPT 분석 실패: {str(error)}"
            )
    
    def _create_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        return """당신은 고도로 숙련된 암호화폐 트레이더입니다.
제공된 BTCUSDT 1분봉 차트 데이터를 분석하여 매매 판단을 내려주세요.

분석 시 고려사항:
1. 기술적 지표 (RSI, MACD, 볼린저 밴드 등)
2. 가격 패턴 및 트렌드
3. 거래량 변화
4. 지지선과 저항선
5. 시장 모멘텀

응답은 반드시 다음 JSON 형식으로 해주세요:
{
    "action": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "leverage": 1-20,
    "reason": "판단 근거를 상세히 설명",
    "stop_loss": 0.01-0.1,
    "take_profit": 0.01-0.2,
    "indicators": {
        "rsi": "overbought|oversold|neutral",
        "macd": "bullish|bearish|neutral",
        "trend": "uptrend|downtrend|sideways"
    }
}

주의사항:
- confidence가 0.7 미만이면 hold를 권장
- 사용자의 위험도 설정을 고려하여 레버리지 조정
- 명확한 신호가 없으면 보수적으로 판단"""
    
    def _create_user_prompt(
        self,
        candles: List[CandleData],
        user_config: Dict[str, Any]
    ) -> str:
        """사용자 프롬프트 생성"""
        try:
            # 캔들 데이터를 분석용 형태로 변환
            candle_data = []
            for i, candle in enumerate(candles):
                candle_info = {
                    "index": i,
                    "timestamp": candle.timestamp,
                    "open": float(candle.open),
                    "high": float(candle.high),
                    "low": float(candle.low),
                    "close": float(candle.close),
                    "volume": float(candle.volume)
                }
                candle_data.append(candle_info)
            
            # 기본 통계 계산
            closes = [float(c.close) for c in candles]
            volumes = [float(c.volume) for c in candles]
            
            current_price = closes[-1]
            price_change = ((closes[-1] - closes[0]) / closes[0]) * 100
            avg_volume = sum(volumes) / len(volumes)
            recent_volume = volumes[-1]
            
            # 커스텀 프롬프트가 있으면 사용
            custom_prompt = user_config.get('custom_prompt', '')
            
            prompt = f"""
사용자 설정:
- 위험도: {user_config.get('risk_level', 'medium')}
- 최대 레버리지: {user_config.get('max_leverage', 10)}

시장 데이터:
- 현재 가격: ${current_price:,.2f}
- 가격 변화: {price_change:+.2f}%
- 평균 거래량: {avg_volume:,.0f}
- 최근 거래량: {recent_volume:,.0f}

캔들 데이터 (최근 {len(candles)}개):
{json.dumps(candle_data[-10:], indent=2)}  # 최근 10개만 표시

{custom_prompt if custom_prompt else ''}

위 데이터를 분석하여 매매 판단을 내려주세요.
"""
            
            return prompt
            
        except Exception as error:
            log_error("사용자 프롬프트 생성 실패", {"error": str(error)})
            return "데이터 분석을 위한 프롬프트 생성에 실패했습니다."    def
 _parse_gpt_response(self, response_content: str) -> GPTAnalysis:
        """GPT 응답 파싱"""
        try:
            # JSON 파싱
            response_data = json.loads(response_content)
            
            # 필수 필드 검증
            action = response_data.get('action', 'hold').lower()
            if action not in ['buy', 'sell', 'hold']:
                action = 'hold'
            
            confidence = float(response_data.get('confidence', 0.0))
            confidence = max(0.0, min(1.0, confidence))  # 0-1 범위로 제한
            
            leverage = int(response_data.get('leverage', 1))
            leverage = max(1, min(20, leverage))  # 1-20 범위로 제한
            
            reason = response_data.get('reason', 'GPT 분석 결과')
            
            # 선택적 필드
            stop_loss = response_data.get('stop_loss')
            if stop_loss:
                stop_loss = max(0.01, min(0.1, float(stop_loss)))
            
            take_profit = response_data.get('take_profit')
            if take_profit:
                take_profit = max(0.01, min(0.2, float(take_profit)))
            
            indicators = response_data.get('indicators', {})
            
            return GPTAnalysis(
                action=TradeAction(action),
                confidence=confidence,
                leverage=leverage,
                reason=reason,
                stop_loss=stop_loss,
                take_profit=take_profit,
                indicators=indicators
            )
            
        except json.JSONDecodeError as error:
            log_error("GPT 응답 JSON 파싱 실패", {
                "error": str(error),
                "response": response_content[:200]  # 처음 200자만 로깅
            })
            
            # JSON 파싱 실패 시 텍스트에서 키워드 추출 시도
            return self._extract_from_text(response_content)
            
        except Exception as error:
            log_error("GPT 응답 파싱 실패", {
                "error": str(error),
                "response": response_content[:200]
            })
            
            return GPTAnalysis(
                action=TradeAction.HOLD,
                confidence=0.0,
                leverage=1,
                reason=f"응답 파싱 실패: {str(error)}"
            )
    
    def _extract_from_text(self, text: str) -> GPTAnalysis:
        """텍스트에서 매매 정보 추출 (JSON 파싱 실패 시 백업)"""
        try:
            text_lower = text.lower()
            
            # 액션 추출
            action = TradeAction.HOLD
            if 'buy' in text_lower or '매수' in text_lower:
                action = TradeAction.BUY
            elif 'sell' in text_lower or '매도' in text_lower:
                action = TradeAction.SELL
            
            # 신뢰도 추출 (기본값)
            confidence = 0.5
            
            # 레버리지 추출 (기본값)
            leverage = 1
            
            reason = f"텍스트 분석 결과: {text[:100]}..."
            
            return GPTAnalysis(
                action=action,
                confidence=confidence,
                leverage=leverage,
                reason=reason
            )
            
        except Exception as error:
            log_error("텍스트 추출 실패", {"error": str(error)})
            
            return GPTAnalysis(
                action=TradeAction.HOLD,
                confidence=0.0,
                leverage=1,
                reason="분석 결과 추출 실패"
            )
    
    async def validate_analysis(self, analysis: GPTAnalysis, user_config: Dict[str, Any]) -> GPTAnalysis:
        """분석 결과 검증 및 조정"""
        try:
            # 사용자 설정에 따른 레버리지 조정
            max_leverage = user_config.get('max_leverage', 10)
            if analysis.leverage > max_leverage:
                analysis.leverage = max_leverage
            
            # 위험도에 따른 신뢰도 임계값 조정
            risk_level = user_config.get('risk_level', 'medium')
            confidence_threshold = {
                'low': 0.8,
                'medium': 0.7,
                'high': 0.6
            }.get(risk_level, 0.7)
            
            # 신뢰도가 임계값 미만이면 보류로 변경
            if analysis.confidence < confidence_threshold:
                log_info("신뢰도 부족으로 보류 처리", {
                    "original_action": analysis.action,
                    "confidence": analysis.confidence,
                    "threshold": confidence_threshold
                })
                
                analysis.action = TradeAction.HOLD
                analysis.reason += f" (신뢰도 {analysis.confidence:.2f} < 임계값 {confidence_threshold})"
            
            return analysis
            
        except Exception as error:
            log_error("분석 결과 검증 실패", {"error": str(error)})
            return analysis
    
    async def get_market_sentiment(self, candles: List[CandleData]) -> Dict[str, Any]:
        """시장 심리 분석 (추가 기능)"""
        try:
            if len(candles) < 10:
                return {"sentiment": "neutral", "reason": "데이터 부족"}
            
            # 간단한 기술적 지표 계산
            closes = [float(c.close) for c in candles]
            volumes = [float(c.volume) for c in candles]
            
            # 가격 트렌드
            recent_trend = (closes[-1] - closes[-5]) / closes[-5] * 100
            overall_trend = (closes[-1] - closes[0]) / closes[0] * 100
            
            # 거래량 트렌드
            recent_volume = sum(volumes[-3:]) / 3
            avg_volume = sum(volumes) / len(volumes)
            volume_ratio = recent_volume / avg_volume
            
            # 심리 판단
            if recent_trend > 2 and volume_ratio > 1.2:
                sentiment = "bullish"
            elif recent_trend < -2 and volume_ratio > 1.2:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            
            return {
                "sentiment": sentiment,
                "recent_trend": recent_trend,
                "overall_trend": overall_trend,
                "volume_ratio": volume_ratio,
                "reason": f"최근 트렌드: {recent_trend:.2f}%, 거래량 비율: {volume_ratio:.2f}"
            }
            
        except Exception as error:
            log_error("시장 심리 분석 실패", {"error": str(error)})
            return {"sentiment": "neutral", "reason": "분석 실패"}