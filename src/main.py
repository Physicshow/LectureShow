import threading
import atexit
import logging

# 애플리케이션 시작 부분에 추가
def thread_excepthook(*args):
    """스레드 예외 처리"""
    logging.error(f"Thread exception: {args}")

threading.excepthook = thread_excepthook

def cleanup_threads():
    """애플리케이션 종료 시 스레드 정리"""
    for thread in threading.enumerate():
        if thread is not threading.main_thread():
            logging.debug(f"Waiting for thread {thread.name} to finish")
            if thread.is_alive():
                # 중요: 강제로 조인하지 않음 - 데드락 방지
                pass

atexit.register(cleanup_threads) 