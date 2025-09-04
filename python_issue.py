import sys
import threading
import time
import traceback


def handler():
    time.sleep(0.001)
    memory_issue_list = []
    while True:
        memory_issue_list.append("a" * 10_000)

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
        print(alive_thread, alive_thread.is_alive(), alive_thread.ident)
        if not alive_thread.is_alive() and serving_thread.is_alive():
            print("Check why serving_thread is doesn't create anymore Thread")
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



# ./configure --prefix=/home/odoo/Documents/Pythons/py14 --enable-optimizations

# Python 3.8.0b1: Reproductible but seems more rare?

# Our version 3.12.3: Reproductible

# Python 3.12.11+: Reproductible
# Python 3.13.7+: Reproductible
# Python 3.14.0rc2+: Reproductible

# Python main/3.15.0a0: Reproductible

