import resource
import threading
import gc

def handler():
    pass

def serving():
    # These should be tweak (depending of Python version + system)
    HARD_LIMIT_START = 30_000_000
    LIMIT_REDUCTION = 5_000

    for _ in range(500_000):
        gc.collect(2)  # Force getting back memory: seems to increase the determinism of the script

        # Limit the heap size available for this process
        resource.setrlimit(resource.RLIMIT_DATA, (HARD_LIMIT_START, HARD_LIMIT_START * 2))
        try:
            handler_thread = threading.Thread(target=handler)
            print(f'Start Thread: {handler_thread} - Heap size limit : {HARD_LIMIT_START}')
            handler_thread.start()
            handler_thread.join()
            HARD_LIMIT_START -= LIMIT_REDUCTION
        except RuntimeError as r:  # If Python refused to launch a new Thread
            print(f'RuntimeError: {r} - Cannot start the thread at all => error not detected.')
            return

serving_thread = threading.Thread(target=serving)
serving_thread.start()
serving_thread.join()
