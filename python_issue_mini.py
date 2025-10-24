import resource
import threading
import gc

# Set limit to avoid crash my computer in worst case if my code is incorrect some how
resource.setrlimit(resource.RLIMIT_AS, (100_000_000, 150_000_000))

def handler():
    pass

def serving():
    hard_limit = 25_000_000  # This can be change depending of the Python version.
    step_limit_reduction = 1000
    for _ in range(100_000):
        gc.collect(2)  # Force to have a more determist issue by getting back heap memory

        # Limit the heap size available for this process
        resource.setrlimit(resource.RLIMIT_DATA, (hard_limit, hard_limit))
        try:
            t = threading.Thread(target=handler)
            print(f'Start Thread: {t} - Heap size limit : {hard_limit}')
            t.start()
            t.join()
            hard_limit -= step_limit_reduction
        except RuntimeError as r:  # If we fail completly to start the new thread
            print(f'RuntimeError {t} : {r}',)
            return

print('Start Serving')
serving_thread = threading.Thread(target=serving, daemon=True)
serving_thread.start()
serving_thread.join()

