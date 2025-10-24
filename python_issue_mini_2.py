import resource
import threading
import time

# Set limit to avoid crash my computer :D
resource.setrlimit(resource.RLIMIT_AS, (1_000_000_000, 1_500_000_000))

def memory_error():
    memory_issue_list = []
    while True:
        memory_issue_list.append("a" * 45000)

def handler():
    time.sleep(0.001)
    try:
        memory_error()
    except MemoryError:
        print(f"MemoryError in {threading.current_thread()}")

def serving():
    for _ in range(100):
        try:
            t = threading.Thread(target=handler)
            print(f'Start Thread: {t}')
            t.start()
        except RuntimeError:
            print('RuntimeError', {t})

print('Start Serving')
serving_thread = threading.Thread(target=serving, daemon=True)
serving_thread.start()
serving_thread.join()

