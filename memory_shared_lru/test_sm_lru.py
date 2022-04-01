
from multiprocessing import Process, Manager
from multiprocessing.managers import BaseManager, DictProxy
from random import random
import traceback
import sm_lru_fp
import time
import functools
import redis
import pylibmc
import os
import traceback
from my_sm_lru import LruDict


# https://stackoverflow.com/questions/45959222/share-an-evolving-dict-between-processes


value = "a" * 1000
key = "a" * 240

# def a_method():
#     return "blublu"

def test_correctness(dict_like):

    dict_like['key_test'] = "blabla"
    assert dict_like['key_test'] == "blabla", f"{dict_like['key_test']} != blabla"
    assert len(dict_like) == 1


    # dict_like['key_test'] = a_method
    # assert dict_like['key_test']() == "blublu"
    # assert len(dict_like) == 2

    del dict_like['key_test']
    assert len(dict_like) == 0

    try:
        dict_like['key_test']
        assert False, f"Should fail, {dict_like['key_test']}"
    except KeyError:
        pass
    except:
        assert False, "Should raise KeyError"

    for i in range(50000):
        # 16_777_216 bytes = 16 MB
        dict_like[str(i)] = "a" * 100
    if hasattr(dict_like, 'max_length'):
        assert len(dict_like) == dict_like.max_length, f"{len(dict_like)} instead of {len(dict_like.max_length)}"

    s = 0
    for i in range(50000):
        if str(i) in dict_like:
            s += 1
            before_l = len(dict_like)
            del dict_like[str(i)]
            if before_l == len(dict_like) - 1:
                print(before_l, len(dict_like) - 1, " Whut ??")
                raise AssertionError("Fail len")
    if len(dict_like) != 0:
        print(dict_like)
        print("delete only:", s)
        print("h",[(i,h) for i,h in enumerate(dict_like.ht) if h])
        print("nex",[(i,h) for i,h in enumerate(dict_like.nxt) if h])
        print("prev", [(i,h) for i,h in enumerate(dict_like.prev) if h])
        print("root", dict_like.root)

    assert len(dict_like) == 0, f"{len(dict_like)} instead of 0"


def test_concurrency(dict_like):
    nb_write = 3000
    nb_read = 30000
    nb_process = 8
    def parrallele_method(dict_like):
        time.sleep(random())
        pid = os.getpid()
        for i in range(nb_write):
            dict_like[str(pid) + str(i)] = str(pid) * 20
        for i in range(nb_read):
            dict_like.get(str(pid) + str(i % nb_write))

    processes = [Process(target=parrallele_method, args=(dict_like,)) for _ in range(nb_process)]
    pids = []
    start = time.time()
    for p in processes:
        p.start()
        pids.append(p.pid)
    for p in processes:
        p.join()
    print(f'Finish concurrent in {((time.time() - start) * 1000):.3f} sec (for {nb_process} process making {nb_write} write and {nb_read} read)')

    simulate_normal = {}
    for pid in pids:
        for i in range(nb_write):
            simulate_normal[str(pid) + str(i)] = str(pid) * 20

    if hasattr(dict_like, 'max_length'):
        assert len(dict_like) == min(len(simulate_normal), dict_like.max_length), f"Not a coorect len, {len(dict_like)} != {min(len(simulate_normal), dict_like.max_length)}"
    # for pid in pids:
    #     assert dict_like[str(pid) + "1"] == str(pid) * 20, f"{dict_like[pid]} != {str(pid) * 20}"

BaseManager.register('LruDict', LruDict, DictProxy)
manager = BaseManager()
manager.start()

obj_to_test = {
    # 'normal_dict': {},
    'Manager().dict - no LRU': Manager().dict(),
    'My Manager LruDict': manager.LruDict(10000),
    'Redis': redis.Redis(),
    'memcached': pylibmc.Client(["127.0.0.1"],
        binary=True,
        behaviors={"tcp_nodelay": True}
    ),
    'current: numpy + single large shared memory': sm_lru_fp.lru_shared(),
    # 'shared memory_lru v1 - 3 lists: key, prev, next': sm_lru_v1.lru_shared(4096),
    # 'shared memory_lru v2 - list of (key, prev, next)': sm_lru_v2.lru_shared(4096),
    # 'shared memory_lru v3 - list of (key, prev, next) - no LRU touch on __get__': sm_lru_v3.lru_shared(4096),
    # 'shared memory_lru v4 - lock - data in sm - 13% lru touch': sm_lru_v4.lru_shared(4096),
}

def f(d):

    t = time.time()
    for i in range(3000): # little more than the size of memory
        d[key + str(i)] = value
        for _ in range(100):
            d[key + str(i)]
    print('    %.6f ms/opp (100 * read for one write)' % ((time.time() - t) * 1000.0 / (3000 * 100)))

    t = time.time()
    for b in range(5000):
        d[key + str(i)] = value
    print('    %.6f ms/write' % ((time.time() - t) * 1000.0 / 5000))

    t = time.time()
    for b in range(3000, 5000):
        d[key + str(i)]
    print('    %.6f ms/read (hit only)' % ((time.time() - t) * 1000.0 / (2000)))

    t = time.time()
    for b in range(2500):
        try:
            d[key + str(i)]
        except KeyError:
            pass
    print('    %.6f ms/read (miss only)' % ((time.time() - t) * 1000.0 / (2500)))
    # t = time.time()
    # for b in range(3000, 5000):
    #     del d[key + str(i)]
    # print('    %.6f ms/delete' % ((time.time() - t) * 1000.0 / (2000)))

if __name__ == '__main__':
    for test, dict_like in obj_to_test.items():
        print(f"\n- {test}:")
        # try:
        #     test_correctness(dict_like)
        # except AssertionError as e:
        #     print(f"Fail test for {test}: {e}")
        #     print(traceback.format_exc())
        # except Exception as e:
        #     print(f"Fail for {test}: {e}")
        #     print(traceback.format_exc())
        # else:
        #     print("Success Correctness")

        try:
            test_concurrency(dict_like)
        except AssertionError as e:
            print(f"Fail concurrency test for {test}: {e}")
            print(traceback.format_exc())
        except Exception as e:
            print(f"Fail concurrency for {test}: {e}")
            print(traceback.format_exc())
        else:
            print("Success concurrency")

        # f(dict_like)
        # try:
        #     del dict_like
        # except Exception as e:
        #     print(f"Fail for {test}: {e}")
        #     print(traceback.format_exc())
        # else:
        #     print("Success delete")

        del dict_like
