#!/usr/bin/env python3
"""
RealSense D435i Unity Link 서버 실행 래퍼
안정적인 시작과 종료를 위한 스크립트
"""

import os
import sys
import signal
import subprocess
import time
import psutil

def find_python_process():
    """실행 중인 main.py 프로세스 찾기"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'main.py' in ' '.join(proc.info['cmdline']):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def kill_process_tree(pid):
    """프로세스와 모든 자식 프로세스 종료"""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # 자식 프로세스들 먼저 종료
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        
        # 부모 프로세스 종료
        parent.terminate()
        
        # 5초 대기 후 강제 종료
        gone, alive = psutil.wait_procs([parent] + children, timeout=5)
        
        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass
                
        return True
    except psutil.NoSuchProcess:
        return False

def signal_handler(signum, frame):
    """시그널 핸들러"""
    print(f"\n시그널 {signum} 수신, 서버 종료 중...")
    
    # 실행 중인 프로세스 찾기
    proc = find_python_process()
    if proc:
        print(f"프로세스 {proc.pid} 종료 중...")
        kill_process_tree(proc.pid)
        print("서버가 종료되었습니다.")
    else:
        print("실행 중인 서버 프로세스를 찾을 수 없습니다.")
    
    sys.exit(0)

def main():
    """메인 함수"""
    # 시그널 핸들러 설정
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 현재 디렉토리 확인
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(script_dir, 'main.py')
    
    if not os.path.exists(main_py):
        print("main.py 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    # 이미 실행 중인 프로세스 확인
    existing_proc = find_python_process()
    if existing_proc:
        print(f"이미 서버가 실행 중입니다. (PID: {existing_proc.pid})")
        response = input("기존 서버를 종료하고 새로 시작하시겠습니까? (y/N): ")
        if response.lower() in ['y', 'yes']:
            kill_process_tree(existing_proc.pid)
            time.sleep(2)
        else:
            print("서버 시작을 취소했습니다.")
            sys.exit(0)
    
    print("=== RealSense D435i Unity Link 서버 시작 ===")
    print("종료하려면 Ctrl+C를 누르세요.")
    print("=" * 50)
    
    try:
        # main.py 실행
        process = subprocess.Popen([sys.executable, main_py], 
                                 cwd=script_dir,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 universal_newlines=True,
                                 bufsize=1)
        
        # 실시간으로 출력
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # 프로세스 종료 코드 확인
        return_code = process.poll()
        if return_code != 0:
            print(f"서버가 비정상 종료되었습니다. (종료 코드: {return_code})")
            sys.exit(return_code)
            
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
        if process:
            kill_process_tree(process.pid)
    except Exception as e:
        print(f"서버 실행 중 오류 발생: {str(e)}")
        if process:
            kill_process_tree(process.pid)
        sys.exit(1)

if __name__ == "__main__":
    main() 