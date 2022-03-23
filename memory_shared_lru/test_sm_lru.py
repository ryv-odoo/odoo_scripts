
from multiprocessing import Process, Manager
import traceback
import sm_lru_fp
import time
import functools
import redis
import pylibmc
import os
import traceback


# https://stackoverflow.com/questions/45959222/share-an-evolving-dict-between-processes


value = "a" * 5000
key = "a" * 2000

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

def test_concurrency(dict_like):
    def parrallele_method(dict_like):
        time.sleep(0.2)
        pid = os.getpid()
        for i in range(20):
            dict_like['u' + (str(pid) * i)] = str(pid) * 100

    nb = 100
    processes = [Process(target=parrallele_method, args=(dict_like,)) for _ in range(nb)]
    pids = []
    for p in processes:
        p.start()
        pids.append(p.pid)
    for p in processes:
        p.join()

    simulate_normal = {}
    for pid in pids:
        for i in range(20):
            simulate_normal[str(pid) * i] = str(pid) * 100

    assert len(dict_like) == len(simulate_normal), f"Not a coorect len, {len(dict_like)} != {len(simulate_normal)}"
    for pid in pids:
        assert dict_like['u' + str(pid)] == str(pid) * 100, f"{dict_like[pid]} != {str(pid) * 100}"

obj_to_test = {
    'normal_dict': {},
    'Manager().dict - no LRU': Manager().dict(),
    # 'Redis': redis.Redis(),
    # 'memcached': pylibmc.Client(["127.0.0.1"],
    #     binary=True,
    #     behaviors={"tcp_nodelay": True}
    # ),
    'current: numpy + single large shared memory': sm_lru_fp.lru_shared(4096),
    # 'shared memory_lru v1 - 3 lists: key, prev, next': sm_lru_v1.lru_shared(4096),
    # 'shared memory_lru v2 - list of (key, prev, next)': sm_lru_v2.lru_shared(4096),
    # 'shared memory_lru v3 - list of (key, prev, next) - no LRU touch on __get__': sm_lru_v3.lru_shared(4096),
    # 'shared memory_lru v4 - lock - data in sm - 13% lru touch': sm_lru_v4.lru_shared(4096),
}

def f():

    t = time.time()
    for i in range(500):
        d[key + str(i)] = value
        for j in range(i):
            d[key + str(j)]
    print('    %.6f ms/opp' % ((time.time() - t) * 1000.0 / (500 * 251)))

    t = time.time()
    for b in range(100):
        d[key + str(i)] = value
        for i in range(250):
            d[key + str(i)] = value
    print('    %.6f ms/write' % ((time.time() - t) * 1000.0 / (250 * 100)))

    t = time.time()
    for b in range(100):
        for i in range(250):
            d[key + str(i)]
    print('    %.6f ms/read' % ((time.time() - t) * 1000.0 / (100 * 250)))

    t = time.time()
    for i in range(250):
        del d[key + str(i)]
    print('    %.6f ms/delete' % ((time.time() - t) * 1000.0 / (100)))

if __name__ == '__main__':
    for test, dict_like in obj_to_test.items():
        print(f"\n- {test}:")
        d = dict_like
        try:
            test_correctness(dict_like)
        except AssertionError as e:
            print(f"Fail test for {test}: {e}")
            print(traceback.format_exc())
        except Exception as e:
            print(f"Fail for {test}: {e}")
            print(traceback.format_exc())
        else:
            print("Success Correctness")

        try:
            test_concurrency(dict_like)
        except AssertionError as e:
            print(f"Fail test for {test}: {e}")
            print(traceback.format_exc())
        except Exception as e:
            print(f"Fail for {test}: {e}")
            print(traceback.format_exc())
        else:
            print("Success concurrency")

        try:
            del dict_like
        except Exception as e:
            print(f"Fail for {test}: {e}")
            print(traceback.format_exc())
        else:
            print("Success delete")
