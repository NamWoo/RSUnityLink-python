#!/usr/bin/env python3
"""
RealSense D435i Unity Link 서버 종료 스크립트
실행 중인 서버를 안전하게 종료합니다.
"""

import os
import sys
import signal
import time
import psutil

def find_python_process():
    """실행 중인 main.py 프로세스 찾기"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'main.py' in ' '.join(proc.info['cmdline']):
                processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def kill_process_tree(pid):
    """프로세스와 모든 자식 프로세스 종료"""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        print(f"프로세스 {pid}와 {len(children)}개 자식 프로세스 종료 중...")
        
        # 자식 프로세스들 먼저 종료
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        
        # 부모 프로세스 종료
        parent.terminate()
        
        # 10초 대기 후 강제 종료
        gone, alive = psutil.wait_procs([parent] + children, timeout=10)
        
        if alive:
            print("일부 프로세스가 응답하지 않아 강제 종료합니다...")
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
        
        return True
    except psutil.NoSuchProcess:
        return False

def main():
    """메인 함수"""
    print("=== RealSense D435i Unity Link 서버 종료 ===")
    
    # 실행 중인 프로세스 찾기
    processes = find_python_process()
    
    if not processes:
        print("실행 중인 서버 프로세스를 찾을 수 없습니다.")
        return
    
    print(f"발견된 서버 프로세스: {len(processes)}개")
    for proc in processes:
        print(f"  - PID: {proc.pid}, 시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(proc.create_time()))}")
    
    # 사용자 확인
    if len(processes) > 1:
        response = input(f"\n{len(processes)}개의 서버 프로세스가 실행 중입니다. 모두 종료하시겠습니까? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("서버 종료를 취소했습니다.")
            return
    
    # 프로세스 종료
    for proc in processes:
        print(f"\n프로세스 {proc.pid} 종료 중...")
        if kill_process_tree(proc.pid):
            print(f"프로세스 {proc.pid}가 성공적으로 종료되었습니다.")
        else:
            print(f"프로세스 {proc.pid} 종료에 실패했습니다.")
    
    # 종료 확인
    time.sleep(1)
    remaining = find_python_process()
    if remaining:
        print(f"\n경고: {len(remaining)}개의 프로세스가 여전히 실행 중입니다.")
        for proc in remaining:
            print(f"  - PID: {proc.pid}")
    else:
        print("\n모든 서버 프로세스가 성공적으로 종료되었습니다.")

if __name__ == "__main__":
    main() 