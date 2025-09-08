import sys
import os
import threading
import time
import traceback
import gc

"""
Current explaination:

When one `handler` Thread is hard kill between after `_start_new_thread` and before `_started.set()` (inside `_bootstrap_inner`):
Two issues happens
- The first issue, is that `threading.enumerate` returns it, but it shouldn't since it is not alive:
That's because `_limbo` is not clean if hard kill (finally clause of `_bootstrap_inner` is bypass). Weird but not blocking

- The Thread of `serving` is stuck waiting that self._started of the killed Thread becomes free, but it will never be ...

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

Because the Thread is hard kill by the OS, should it release his lock and then setting _started ??? 


"""






print("PID: ", os.getpid())
print("Sleep 10 sec")
time.sleep(1)



#




def memory_error():
    memory_issue_list = []
    while True:
        memory_issue_list.append("a" * 10_000)

def handler():
    try:
        memory_error()
    except MemoryError:
        print("MemoryError - stop")
        # gc.collect()


def serving():
    for _ in range(100):
        t = threading.Thread(target=handler)
        print('Start Sub-Thread')
        t.start()

print('Start Serving')
serving_thread = threading.Thread(target=serving, daemon=True)
serving_thread.start()

while serving_thread.is_alive():
    time.sleep(2)
    for alive_thread in threading.enumerate():
        print(alive_thread, alive_thread.is_alive(), alive_thread.ident, alive_thread.native_id)
        if not alive_thread.is_alive() and serving_thread.is_alive():
            print(f"Serving thread info: {serving_thread._started=} | {serving_thread._started._flag=}")
            print(f"Alive but dead thread: {alive_thread._started=} | {alive_thread._started._flag=}")

            frames_serving_thread = sys._current_frames()[serving_thread.ident]
            traceback.print_stack(frames_serving_thread)

#   File "/home/odoo/Documents/Pythons/py14/lib/python3.14/threading.py", line 1043, in _bootstrap
#     self._bootstrap_inner()
#   File "/home/odoo/Documents/Pythons/py14/lib/python3.14/threading.py", line 1081, in _bootstrap_inner
#     self._context.run(self.run)
#   File "/home/odoo/Documents/Pythons/py14/lib/python3.14/threading.py", line 1023, in run
#     self._target(*self._args, **self._kwargs)
#   File "/home/odoo/Documents/dev/./odoo_scripts/python_issue.py", line 17, in serving
#     t.start()
#   File "/home/odoo/Documents/Pythons/py14/lib/python3.14/threading.py", line 1010, in start
#     self._started.wait()  # Will set ident and native_id
#   File "/home/odoo/Documents/Pythons/py14/lib/python3.14/threading.py", line 669, in wait
#     signaled = self._cond.wait(timeout)
#   File "/home/odoo/Documents/Pythons/py14/lib/python3.14/threading.py", line 369, in wait
#     waiter.acquire()


"""
git checkout main &&
mkdir -p /home/odoo/Documents/Pythons/pymain &&
make --quiet clean &&
./configure --prefix=/home/odoo/Documents/Pythons/pymain --enable-optimizations &&
make --quiet -j 10 &&
make --quiet altinstall
"""

"""
make --quiet clean &&
./configure --enable-optimizations &&
make --quiet -j 10
"""



# ./configure --prefix=/home/odoo/Documents/Pythons/py14 --enable-optimizations

# Python 3.8.0b1: Reproductible but seems more rare?

# Our version 3.12.3: Reproductible

# Python 3.12.11+: Reproductible
# Python 3.13.7+: Reproductible
# Python 3.14.0rc2+: Reproductible

# Python main/3.15.0a0: Reproductible

