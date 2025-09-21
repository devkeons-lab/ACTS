# 지원하는 암호화폐 심볼 목록

# 주요 암호화폐 심볼 (Bybit Spot 거래 지원)
SUPPORTED_SYMBOLS = [
    # 메이저 코인
    'BTCUSDT',   # 비트코인
    'ETHUSDT',   # 이더리움
    'BNBUSDT',   # 바이낸스 코인
    'ADAUSDT',   # 카르다노
    'XRPUSDT',   # 리플
    'SOLUSDT',   # 솔라나
    'DOTUSDT',   # 폴카닷
    'DOGEUSDT',  # 도지코인
    'AVAXUSDT',  # 아발란체
    'SHIBUSDT',  # 시바이누
    
    # 알트코인
    'MATICUSDT', # 폴리곤
    'LINKUSDT',  # 체인링크
    'LTCUSDT',   # 라이트코인
    'BCHUSDT',   # 비트코인 캐시
    'UNIUSDT',   # 유니스왑
    'ATOMUSDT',  # 코스모스
    'VETUSDT',   # 비체인
    'FILUSDT',   # 파일코인
    'TRXUSDT',   # 트론
    'ETCUSDT',   # 이더리움 클래식
    
    # DeFi 토큰
    'AAVEUSDT',  # 아베
    'MKRUSDT',   # 메이커
    'COMPUSDT',  # 컴파운드
    'YFIUSDT',   # 이어닷파이낸스
    'SUSHIUSDT', # 스시스왑
    'CRVUSDT',   # 커브
    '1INCHUSDT', # 1인치
    
    # 레이어1 블록체인
    'NEARUSDT',  # 니어 프로토콜
    'ALGOUSDT',  # 알고랜드
    'EGLDUSDT',  # 멀티버스X
    'FTMUSDT',   # 팬텀
    'HBARUSDT',  # 헤데라
    'FLOWUSDT',  # 플로우
    'ICPUSDT',   # 인터넷 컴퓨터
    
    # 메타버스/게임
    'MANAUSDT',  # 디센트럴랜드
    'SANDUSDT',  # 샌드박스
    'AXSUSDT',   # 액시 인피니티
    'ENJUSDT',   # 엔진코인
    'GALAUSDT',  # 갈라
    
    # 기타 인기 코인
    'APTUSDT',   # 앱토스
    'OPUSDT',    # 옵티미즘
    'ARBUSDT',   # 아비트럼
    'LDOUSDT',   # 리도 DAO
    'STXUSDT',   # 스택스
]

# 지원하는 캔들 간격
SUPPORTED_INTERVALS = [
    '1',    # 1분
    '3',    # 3분
    '5',    # 5분
    '15',   # 15분
    '30',   # 30분
    '60',   # 1시간
    '120',  # 2시간
    '240',  # 4시간
    '360',  # 6시간
    '720',  # 12시간
    'D',    # 1일
    'W',    # 1주
    'M',    # 1월
]

# 심볼 정보 (표시명, 설명)
SYMBOL_INFO = {
    'BTCUSDT': {'name': 'Bitcoin', 'description': '비트코인'},
    'ETHUSDT': {'name': 'Ethereum', 'description': '이더리움'},
    'BNBUSDT': {'name': 'BNB', 'description': '바이낸스 코인'},
    'ADAUSDT': {'name': 'Cardano', 'description': '카르다노'},
    'XRPUSDT': {'name': 'XRP', 'description': '리플'},
    'SOLUSDT': {'name': 'Solana', 'description': '솔라나'},
    'DOTUSDT': {'name': 'Polkadot', 'description': '폴카닷'},
    'DOGEUSDT': {'name': 'Dogecoin', 'description': '도지코인'},
    'AVAXUSDT': {'name': 'Avalanche', 'description': '아발란체'},
    'SHIBUSDT': {'name': 'Shiba Inu', 'description': '시바이누'},
    'MATICUSDT': {'name': 'Polygon', 'description': '폴리곤'},
    'LINKUSDT': {'name': 'Chainlink', 'description': '체인링크'},
    'LTCUSDT': {'name': 'Litecoin', 'description': '라이트코인'},
    'BCHUSDT': {'name': 'Bitcoin Cash', 'description': '비트코인 캐시'},
    'UNIUSDT': {'name': 'Uniswap', 'description': '유니스왑'},
    'ATOMUSDT': {'name': 'Cosmos', 'description': '코스모스'},
    'VETUSDT': {'name': 'VeChain', 'description': '비체인'},
    'FILUSDT': {'name': 'Filecoin', 'description': '파일코인'},
    'TRXUSDT': {'name': 'TRON', 'description': '트론'},
    'ETCUSDT': {'name': 'Ethereum Classic', 'description': '이더리움 클래식'},
}

def is_supported_symbol(symbol: str) -> bool:
    """심볼이 지원되는지 확인"""
    return symbol.upper() in SUPPORTED_SYMBOLS

def is_supported_interval(interval: str) -> bool:
    """캔들 간격이 지원되는지 확인"""
    return interval in SUPPORTED_INTERVALS

def get_symbol_info(symbol: str) -> dict:
    """심볼 정보 조회"""
    return SYMBOL_INFO.get(symbol.upper(), {
        'name': symbol.upper(),
        'description': symbol.upper()
    })

def get_supported_symbols() -> list:
    """지원하는 심볼 목록 반환"""
    return SUPPORTED_SYMBOLS.copy()

def get_supported_intervals() -> list:
    """지원하는 캔들 간격 목록 반환"""
    return SUPPORTED_INTERVALS.copy()