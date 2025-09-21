#!/usr/bin/env python3
"""
API 서버 실행 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# API 서버 실행
if __name__ == "__main__":
    try:
        # 직접 경로 추가하여 import
        api_server_path = project_root / "backend" / "api-server" / "src"
        sys.path.insert(0, str(api_server_path))
        
        from main import app
        import uvicorn
        
        port = int(os.getenv('API_SERVER_PORT', 3001))
        uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
        
    except ImportError as e:
        print(f"Import 오류: {e}")
        print("필요한 패키지를 설치하세요: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"서버 실행 오류: {e}")
        sys.exit(1)