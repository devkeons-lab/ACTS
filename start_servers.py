#!/usr/bin/env python3
"""
모든 서버를 한번에 실행하는 통합 스크립트
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 프로젝트 루트 설정
project_root = Path(__file__).parent
os.chdir(project_root)

# 환경 변수 설정
env = os.environ.copy()
env['PYTHONPATH'] = str(project_root) + os.pathsep + str(project_root / "backend")

def run_server(script_name, server_name):
    """개별 서버 실행"""
    try:
        print(f"🚀 {server_name} 시작 중...")
        
        # Python 경로를 직접 설정하여 실행
        cmd = [
            sys.executable, 
            "-c", 
            f"""
import sys
sys.path.insert(0, r'{project_root}')
sys.path.insert(0, r'{project_root / "backend"}')
exec(open(r'{project_root / script_name}').read())
"""
        ]
        
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=str(project_root)
        )
        
        print(f"✅ {server_name} 시작됨 (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ {server_name} 시작 실패: {e}")
        return None

def main():
    print("🎯 암호화폐 자동매매 시스템 시작")
    print("=" * 50)
    
    # 서버 목록
    servers = [
        ("run_data_server.py", "데이터 수집 서버"),
        ("run_api_server.py", "API 서버"),
        ("run_auto_server.py", "자동매매 서버")
    ]
    
    processes = []
    
    for script, name in servers:
        process = run_server(script, name)
        if process:
            processes.append((process, name))
        time.sleep(2)  # 서버 간 시작 간격
    
    print("\n" + "=" * 50)
    print("🎉 모든 서버가 시작되었습니다!")
    print("\n📋 실행 중인 서버:")
    for process, name in processes:
        print(f"  - {name} (PID: {process.pid})")
    
    print("\n🔗 접속 URL:")
    print("  - 웹 애플리케이션: http://localhost:3000")
    print("  - API 문서: http://localhost:3001/docs")
    print("  - phpMyAdmin: http://localhost:8080")
    
    print("\n⚠️  서버를 중지하려면 Ctrl+C를 누르세요")
    
    try:
        # 모든 프로세스가 종료될 때까지 대기
        for process, name in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\n🛑 서버 중지 중...")
        for process, name in processes:
            try:
                process.terminate()
                print(f"  - {name} 중지됨")
            except:
                pass

if __name__ == "__main__":
    main()