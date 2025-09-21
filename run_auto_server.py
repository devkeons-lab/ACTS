#!/usr/bin/env python3
"""
자동매매 서버 실행 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# backend 디렉토리를 Python 경로에 추가 (shared 모듈 접근용)
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# 자동매매 서버 실행
if __name__ == "__main__":
    try:
        # 자동매매 서버 경로 추가
        auto_server_path = project_root / "backend" / "auto-server" / "src"
        sys.path.insert(0, str(auto_server_path))
        
        from main import main
        import asyncio
        asyncio.run(main())
    except ImportError as e:
        print(f"Import 오류: {e}")
        print("필요한 패키지를 설치하세요: pip install -r requirements.txt")
        print(f"Python 경로: {sys.path}")
        sys.exit(1)
    except Exception as e:
        print(f"서버 실행 오류: {e}")
        sys.exit(1)