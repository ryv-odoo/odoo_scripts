import resource
import sys
import os
import threading
import time
import traceback
import gc



# To Compile Python
"""
mkdir -p /home/odoo/Documents/Pythons/py12 &&
./configure --prefix=/home/odoo/Documents/Pythons/py12 --enable-optimizations &&
make --quiet clean &&
make --quiet -j 10 &&
make --quiet altinstall
"""

"""
./configure --enable-optimizations &&
make --quiet clean &&
make --quiet -j 10
"""



"""
Current explaination:

When one `handler` Thread is killed (not enough memory) between after starting the new thread (thread_run C code) 
and before `_started.set()` Python (inside `_bootstrap_inner` or just before in the C threaded code):

Leading into deadlock situation the serving Thread wait the `_started` to be set, but 
it will never be since the specific Thread is dead... Also if this dead Thread remains in
the _limbo dictionary (small inconsistency since it will be return in case of threading.enumarate()).

When the thread is killed inside before `_started.set()`, we always get this weird error message:
"Exception ignored in thread started by: <A method>"
This comes from the `thread_run` (C code) calling `_PyErr_WriteUnraisableMsg`
At first glance, it seems that the ignored Exception is a MemoryError that skip part of the `_bootstrap_inner` method

What we tried:
- Increasing the stack_size to force Python to only accept create new Thread when more
memory is available on the stack. That's doesn't seems to work even with a hug number...
Does this method even work ?? Signature is odd and the doc is incomplete ??

- Catch the MemoryError, to sleep + gc after in order to force free memory => doesn't work better

- Biscept on stable version, but is is reproductible:
    - Python 3.8.0b1: Reproductible but seems more rare?
    - Our version 3.12.3: Reproductible
    - Python 3.12.11+: Reproductible
    - Python 3.13.7+: Reproductible
    - Python 3.14.0rc2+: Reproductible
    - Python main/3.15.0a0: Reproductible

- Find a magic solution to bypass `self._started.wait()`. The only 'working' solution is to add
a timeout (1 sec) on it that recheck the status of the Thread. But is fragile, because a timeout
is always a trade-off (after 1 sec is long and still not ensure that the Thread has been effectively
killed).


Deadlock traceback
------------------
  File "/home/odoo/Documents/Pythons/py12_11/lib/python3.12/threading.py", line 1033, in _bootstrap
    self._bootstrap_inner()
  File "/home/odoo/Documents/Pythons/py12_11/lib/python3.12/threading.py", line 1078, in _bootstrap_inner
    self.run()
  File "/home/odoo/Documents/Pythons/py12_11/lib/python3.12/threading.py", line 1013, in run
    self._target(*self._args, **self._kwargs)
  File "/home/odoo/Documents/dev/./odoo_scripts/python_issue.py", line 42, in serving
    t.start()
  File "/home/odoo/Documents/Pythons/py12_11/lib/python3.12/threading.py", line 1000, in start
    self._started.wait()
  File "/home/odoo/Documents/Pythons/py12_11/lib/python3.12/threading.py", line 655, in wait
    signaled = self._cond.wait(timeout)
  File "/home/odoo/Documents/Pythons/py12_11/lib/python3.12/threading.py", line 355, in wait
    waiter.acquire()

TODO:
- Check inside the ignored Exception with a debugger C
- Check works stack_size
- 

"""
threading.stack_size(33000)

print("PID: ", os.getpid(), " Stack Size ", threading.stack_size())

# print("Sleep 10 sec")
# time.sleep(10)

resource.setrlimit(resource.RLIMIT_AS, (1_000_000_000, 1_500_000_000))

def memory_error():
    memory_issue_list = []
    while True:
        memory_issue_list.append("a" * 150_000)

def handler():
    time.sleep(0.001)
    try:
        memory_error()
    except MemoryError:
        print(f"MemoryError in {threading.current_thread()}")
        # gc.collect()
        # time.sleep(0.1)

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


time.sleep(10)
while serving_thread.is_alive():
    for alive_thread in threading.enumerate():
        print(alive_thread, alive_thread.is_alive(), alive_thread.ident, alive_thread.native_id)
        if not alive_thread.is_alive() and serving_thread.is_alive():
            print(f"Serving thread info: {serving_thread._started=} | {serving_thread._started._flag=}")
            print(f"Alive but dead thread: {alive_thread._started=} | {alive_thread._started._flag=}")

            if serving_thread.ident in sys._current_frames():
                frames_serving_thread = sys._current_frames()[serving_thread.ident]
                traceback.print_stack(frames_serving_thread)

    time.sleep(10)
