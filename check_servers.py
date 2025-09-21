#!/usr/bin/env python3
"""
서버 상태 확인 스크립트
"""

import requests
import socket
from datetime import datetime

def check_port(host, port):
    """포트가 열려있는지 확인"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_api_server():
    """API 서버 상태 확인"""
    try:
        response = requests.get("http://localhost:3001/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🔍 서버 상태 확인 중...")
    print(f"⏰ 확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # 포트 확인
    servers = [
        ("API 서버", "localhost", 3001),
        ("데이터 수집 서버", "localhost", 3002),
        ("자동매매 서버", "localhost", 3003),
    ]
    
    for name, host, port in servers:
        status = "🟢 실행 중" if check_port(host, port) else "🔴 중지됨"
        print(f"{name:15} (포트 {port}): {status}")
    
    print("-" * 50)
    
    # API 서버 HTTP 응답 확인
    api_status = "🟢 정상" if check_api_server() else "🔴 오류"
    print(f"API 서버 HTTP 응답: {api_status}")
    
    # Docker 컨테이너 확인
    print("\n🐳 Docker 컨테이너 상태:")
    import subprocess
    try:
        result = subprocess.run(
            ["docker-compose", "ps"], 
            capture_output=True, 
            text=True, 
            cwd="."
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # 헤더 제외
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        container_name = parts[0]
                        status = "🟢 실행 중" if "Up" in line else "🔴 중지됨"
                        print(f"  {container_name:25}: {status}")
        else:
            print("  Docker Compose 상태 확인 실패")
    except:
        print("  Docker가 설치되지 않았거나 실행되지 않음")

if __name__ == "__main__":
    main()