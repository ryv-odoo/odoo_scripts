
# Cross Worker Cache

The goal is to make a long term efficient cross-worker/process cache (`key: value`), which shouldn't be invalidate (or never completely).

For now, we want to use it only for the new t-cache feature: t-cache use a unique cache key which should never be invalidate (LRU will do the job to pop no-accessible key). t-cache use the `write_date` of record in the t-cache keys, and the write_date always increases then we didn't need to invalidate manually the cache when a record change.

## Goals

This cache should:
(1) share between process/workers: use a shared memory for the data structure and the key/value should be marshable to be transparently sharable via bytes.
(2) be efficient: as a `dict` in term of complexity (hashtable), where the set/get is in O(1) (Average Case) (then the cache key should be hashable)
(3) have a removal strategy: LRU
(4) manage inter-process concurrency get/set.
(5) be fault tolerant: if a process is killed when it use the cache (set or get), the cache should be always usable by other process and coherent.

## HOW TO

### (1) Sharable
We manage the 'sharable' attributes of cache with a the https://docs.python.org/3/library/multiprocessing.shared_memory.html for data (only available in >= Python3.8) and https://docs.python.org/3.8/library/multiprocessing.html#module-multiprocessing.sharedctypes for the data structure information. This sharable memory is create/unlink by the main server (`PreforkServer` for multi-processing and the `ThreadedServer` for the multithreading). (1)

### (2) Efficiency
For efficiency, we construct a Hash Table (with linear probing: https://en.wikipedia.org/wiki/Linear_probing) on top of this Shared Memory and sharedctype. Note that, because the data (key/value) has different size, we should sometimes defragment the memory. This shared cache is limited by a fixed number of entry (we don't manage resize for now) and a fixed memory buffer. (2)

### (3) Removal Strategy
Because it doesn't grown with the number of data insert, we should get a removal strategy (constraints by the number of entry and the data taken by key/value): we use a double linked list between HashTable entry to create a LRU. (3)

In the current implementation, (1) (2) (3) works fine and seems correct to me.

### (4) Concurrency
To manage the concurrency and avoid to get corrupted data structure, we want a exclusive access for get/set (4) (we don't want a parallel access for 'get' due to its implementation complexity and it needs to write on the data structure for the LRU (3)).

### (5) Fault tolerance

Moreover, the exclusive access should be release when a process is killed (by example, killed by the PreforkServer because of timeout) when it currently acquired the access (5).
Also if a Process which is modifying the Shared Memory is killed, we should ensure that the data structure is still coherent and usable. We can easily detect this case with a simple shared boolean (`coherent`) set to False before modify and reset to True after the modification and before using the Shared Memory if the coherent is False, then we empty the all data structure.

### Current issues

Currently, the goals (4)(5) are complicate to maintain in the same time, I propose 2 different solutions:

- The first solution is to use a inter-process Lock (https://docs.python.org/3.8/library/multiprocessing.html#multiprocessing.Lock) to manage the concurrent access. It manages correctly the concurrent access, but the lock is not release if the process is killed, then the lock is locked forever. To 'solve' this issue, we can add the PID just after acquiring the lock. And when the main process detect (or kill itself) one of his child process, it can check if the PID of the lock is equals to the one killed, if it is the case, it releases the Lock. However, if the process is killed between setting his PID and acquire/release the lock, we comeback on the first situation. We can 'mitigate' this by putting a timeout if the lock is acquiring by a unknown process, and if after the timeout expire, the PID is still unknown, the lock still acquired and the last_used of the shared_memory didn't change, consider that the lock should be release.
But it is really correct to read data that can be write in the same time ? Also with a timeout we cannot ensure that during this time, a alive process didn't get enough CPU to make one operation on the Shared Cache, then the lock will be release where it shouldn't.

- A more robust solution (presented here: https://patents.google.com/patent/US7493618) uses one atomic (Compare-And-Swap operation, CAS) operation to ensure the fault-tolerant and exclusive access attributes. But there are no such operation in Python (or I didn't find ?), excepted using 'atomics' library (not standard and not use a lot). Also we cannot bind the CAS of C language (https://en.cppreference.com/w/c/atomic/atomic_compare_exchange) method with ctypes because it is not in a clib and the atomics type are not in the ctypes. But we can use CFFI library to compile on fly the atomic operation needed but it seems very touchy, weird, machine-depend and we should have a compiler C on the machine.

Open Question:
- For (4) (5), which solution the best ? None ?
- There is also out-of-the-box alternative: memcached, redis (but need more infra)?
- Alternative of the manual defragment ?
- Should we consider to increase/decrease the entry table on fly ? and the shared memory ? (the first is possible, but the seconde ones seems very complicated)

