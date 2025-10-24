
Hello, I took a look at this recently. (Sorry for the delay, by the way).

My understanding of the problem so far (with additional investigation from Jihaysse):

- The ThreadedServer calls Thread.start() [1](https://github.com/odoo/odoo/blob/850c46c641da422d42d46cab59b44e2a10c00d41/odoo/service/server.py#L596), putting the thread in the _limbo dictionary: `_limbo[self] = self`.
- Thread.start() succeeds in calling the low-level [pthread_create](https://github.com/python/cpython/blob/25243b1461e524560639ebe54bab9b689b6cc31e/Python/thread_pthread.h#L284) (call chain: Thread.start -> _start_new_thread() -> thread_PyThread_start_new_thread -> pthread_create). At this point, there is enough memory for Python to start a new thread.
- Then, the ThreadedServer waits with `self._started.wait()` [here](https://github.com/python/cpython/blob/f463d05a0979aada4fadcd43ff721b1ff081d2aa/Lib/threading.py#L999) for the new thread to signal that it has started.
- At the same time, the new thread begins execution in its C-level bootstrap function [thread_run](https://github.com/python/cpython/blob/89a79fc919419bfe817da13bc2a4437908d7fc07/Modules/_threadmodule.c#L1088). However, at this point, there is no longer enough heap memory (this can happen for various reasons, e.g., another thread allocated a lot of memory between the thread's creation and its start or just because there not enough heap memory before starting the thread) to call the Python-level bootstrap method (_bootstrap -> [_bootstrap_inner](https://github.com/python/cpython/blob/f463d05a0979aada4fadcd43ff721b1ff081d2aa/Lib/threading.py#L1064) that needs to signal the thread's startup.
- As a result, the new thread fails to signal the parent Thread, printing a weird error message: `Exception ignored in thread started by: <bound method Thread._bootstrap of ...` (the error message may change depending on which call crashes: sometimes it's `_bootstrap` or an `object repr()`). This error originates from [here](https://github.com/python/cpython/blob/89a79fc919419bfe817da13bc2a4437908d7fc07/Modules/_threadmodule.c#L1122).
- The ThreadedServer is left waiting for the [signal](https://github.com/python/cpython/blob/f463d05a0979aada4fadcd43ff721b1ff081d2aa/Lib/threading.py#L1064) that will never arrive, and the _limbo dictionary still contains this "cancelled" new thread.


I succeed to reproduce the issue from Python 3.8 => 3.15. Here there are two different scripts to reproduce the issue:
- A more deterministic one with one thread at the time: The idea is to reduce the heap limit until Python accepts to launch the new Thread but the new Thread doesn't have enough memory to finish his bootstrap. Then the serving Thread will wait forever.
```python
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
        gc.collect(2)  # Force a more determist issue by getting back heap memory
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
```
- A less deterministic one, that sometime never finishes:
```Python
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
```

=> This looks like a CPython issue to me. I still need to create an issue on the CPython repository (though I have no idea how to fix it easily, I'll try to figure it out if I have time).

Regarding this workaround, I think we can merge it. Even if the issue is confirmed (or not and that's just a limitation) by the Python developers, I'm pretty sure a fix wouldn't be backported anyway (and I don't see a reason why it would need to be).