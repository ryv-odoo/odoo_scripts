


from multiprocessing import Process
import os
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import RLock, Lock
from multiprocessing.sharedctypes import RawArray, RawValue, Value
from time import sleep
from ctypes import Structure, c_int64, c_size_t, c_ssize_t




b = Lock()
val = Value(c_int64, 1, lock=b)
nor = 1
pid = os.fork()
if pid == 0:  # child
    print("Child:", b, val.value, nor, hash("a"))
    print("child val * 2")
    val.value = val.value * 2
    nor *= 2
    print("Child:", b, val.value, nor)
    sleep(3)
    val.value = val.value * 2
    print("Child:", b, val.value, nor)
    sleep(1)
    val.value = val.value * 2
    print("Child:", b, val.value, nor)

    print("Child will close in 5 sec")
    sleep(5)
else:
    print("Parent:", b, val.value, nor, hash("a"))
    print("parent val * 2")
    val.value = val.value * 2
    nor *= 2
    print("Parent:", b, val.value, nor)
    print("Parent sleep(0)")
    sleep(0)

    print("Parent will close in 1 sec")
    sleep(1)