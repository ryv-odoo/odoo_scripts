#from multiprocessing.managers import SharedMemoryManager
import itertools
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import RLock
import numpy
import marshal
import functools


class lru_shared(object):
    def __init__(self, size=32):
        assert size > 0 and (size & (size - 1) == 0), "LRU size must be an exponantiel of 2"
        self.mask = size - 1
        self.size = size
        byte_size = size * 4096

        self.sm = SharedMemory(name="odoo_sm_lru_shared", size=byte_size, create=True)
        self.sm.buf[:] = b'\x00' * byte_size
        data = [
            ('head', numpy.int32, (3,)),     # Contains root, length and free_len : 12 bytes
            ('ht', numpy.int64, (size,)),    # hash array: size * 8 bytes = 32768 bytes
            ('prev', numpy.int32, (size,)),  # previous index array (of the linked list), if == -1, this index is empty: 4 bytes * size
            ('nxt', numpy.int32, (size,)),   # next index array (of the linked list), if == -1, this index is empty : 4 bytes * size
            ('data_idx', numpy.uint64, (size, 2)),  # data (position, size) array
            ('data_free', numpy.uint64, (size + 9, 2))
        ]
        start = 0
        for (name, dtype, sz) in data:
            end = start + dtype().nbytes * functools.reduce(lambda x,y: x*y, sz, 1)
            setattr(self, name, numpy.ndarray(sz, dtype=dtype, buffer=self.sm.buf[start:end]))
            start = end

        self.data = self.sm.buf[end: byte_size]
        self.data_free[0] = [0, (byte_size) - end]
        self.lock = RLock()

        self.touch = 1        # used to touch the lru periodically, not 100% of the time
        self.root = -1        # stored at end of self.prev
        self.length = 0       # stored at end of self.nxt
        self.free_len = 1     # size of self.data_free

    root = property(lambda self: self.head[0], lambda self, x: self.head.__setitem__(0, x))
    length = property(lambda self: self.head[1], lambda self, x: self.head.__setitem__(1, x))
    free_len = property(lambda self: self.head[2], lambda self, x: self.head.__setitem__(2, x))

    def _malloc(self, index, data):
        data = marshal.dumps(data)
        size = len(data)
        for pos in range(self.free_len):
            if self.data_free[pos,1] >= size:
                break
        else:
            raise "no memory"

        mem_pos = int(self.data_free[pos,0])
        self.data[mem_pos:(mem_pos+size)] = data
        self.data_idx[index] = (mem_pos, size)
        self.data_free[pos, 1] -= size
        self.data_free[pos, 0] += size
        return True

    def _mprint(self):
        print('free: ', self.data_free[:self.free_len])

    def _free(self, index):
        last = self.free_len
        self.data_free[last] = self.data_idx[index]
        size = last + 1
        self.free_len = size

        if size >= self.size: # or not self.touch:
            # TODO: optimize this code
            mems = self.data_free[self.data_free[:size, 0].argsort()]
            pos = 0
            while pos < len(mems)-1:
                if mems[pos][0] + mems[pos][1] == mems[pos+1][0]:
                    mems[pos][1] += mems[pos+1][1]
                    mems = numpy.delete(mems, pos+1, 0)
                else:
                    pos += 1
            self.free_len = len(mems)
            mems = self.data_free[:len(mems)] = mems[mems[:, 1].argsort()[::-1]]

    def mset(self, index, key, prev, nxt):
        self.prev[index] = prev
        self.nxt[index] = nxt
        self.ht[index] = key

    def mget(self, index):
        return (self.ht[index], self.prev[index], self.nxt[index])

    def index_get(self, hash_):
        for i in range(self.size):
            yield (hash_ + i) & self.mask

    def data_get(self, index):
        return marshal.loads(self.data[self.data_idx[index, 0]:])

    def lookup(self, key_, hash_):
        for index in self.index_get(hash_):
            key, prev, nxt = self.mget(index)
            if not key:
                return (index, key, prev, nxt, None)
            if key == hash_:
                (key_full, val) = self.data_get(index)
                if key_full == key_:
                    return (index, key, prev, nxt, val)
        raise "memory full means bug"

    def __getitem__(self, key_):
        have_lock = self.lock.acquire(block=False)
        if not have_lock:  # Or block ?
            raise KeyError("Lock cannot be acquire")
        index, key, prev, nxt, val = self.lookup(key_, hash(key_))
        self.lock.release()
        if val is None:
            raise KeyError(f"{key_} doesn't not exist")
        self.touch = (self.touch + 1) & 7
        if not self.touch:   # lru touch every 8th reads: not sure about this optim?
            if self.lock.acquire(block=False):
                try:
                    self.lru_touch(index, key, prev, nxt)
                finally:
                    self.lock.release()
        return val

    def __setitem__(self, key, value):
        hash_ = hash(key)
        with self.lock:
            index, key_, prev, nxt, val = self.lookup(key, hash_)
            if val is None:
                self.length += 1
            else:  # Shouldn't happen, there should ba always a place
                self._free(index)
            self.ht[index] = hash_
            self.lru_touch(index, hash_, None, None)
            self._malloc(index, (key, value))
            while self.length > (self.size >> 1):
                self.lru_pop()

    def lru_pop(self):
        root = self.root
        if root == -1:
            return False
        _, prev_index, _ = self.mget(root)
        self._del_index(prev_index, *self.mget(prev_index))

    def lru_touch(self, index, key, prev, nxt):
        root = self.root
        if root == -1:
            self.root = index
            self.mset(index, key, index, index)
            return True

        if prev is not None:
            self.prev[nxt] = prev
            self.nxt[prev] = nxt

        rprev = self.prev[root]
        self.prev[index] = rprev
        self.nxt[index] = root

        self.prev[root] = index
        self.nxt[rprev] = index
        self.root = index

    # NOTE: delete the keys that are between this element, and the next free spot, having
    #       an index lower or equal to the position we delete. (conflicts handling) or
    #       move them by 1 position left
    def _del_index(self, index, key, prev, nxt):

        if prev == index:
            self.root = -1
        else:
            self.prev[nxt] = prev
            self.nxt[prev] = nxt
            if self.root == index:
                self.root = nxt

        self._free(index)
        self.mset(index, 0, 0, 0)
        self.length -= 1

        def change_index(old_index, new_index):
            print(f"Move index {old_index} -> {new_index}")
            key_i, prev_i, next_i = self.mget(old_index)
            self.nxt[prev_i] = new_index
            self.prev[next_i] = new_index
            self.mset(new_index, key_i, prev_i, next_i)
            self.mset(old_index, 0, 0, 0)
            self.data_idx[new_index] = self.data_idx[old_index]
            self.data_idx[old_index] = (0, 0)
            print(old_index, self.mget(old_index))

        # move next entry who share the same hash & mask
        entry_empty = index
        for i in itertools.chain(range(index + 1, self.size), range(0, index)) :
            if self.ht[i]:
                if (self.ht[i] & self.mask) == (key & self.mask):
                    change_index(i, entry_empty)
                    entry_empty = i
                else:
                    pass # not a empty, continue to search
            else:
                break

    def __del__(self):
        del self.head
        del self.ht
        del self.prev
        del self.nxt
        del self.data_idx
        del self.data_free
        del self.data
        self.sm.close()
        self.sm.unlink()

    def __len__(self):
        return self.length

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        return True

    def __delitem__(self, key):
        print("Try to delete key=", key)
        hash_ = hash(key)
        index, key, prev, nxt, val = self.lookup(key, hash_)
        if val is None:
            KeyError(f"{key} doesn't not exist, cannot delete it")
        self._del_index(index, key, prev, nxt)

    def __str__(self):
        if self.root == -1:
            return '[]'

        node = self.root
        result = []
        while True:
            key, prev, nxt = self.mget(node)
            data = self.data_get(node)
            result.append(f'{data[0]} (hash & mask: {key & self.mask}, index: {node}, hash: {key:+}): {data[1]}')
            node = nxt
            if node == self.root:
                return f'hashtable size: {self.size}, mask: {self.mask}, len: {str(self.length)}\n' + '\n'.join(result)


if __name__=="__main__":
    lru = lru_shared(4)
    lru["hello"] = "Bonjour!"
    print(lru)
    lru["bye"] = "Au revoir!"
    print(lru)
    lru["hello"]
    print(lru)
    lru["I"] = "Je"
    print(lru)
    lru["you"] = "Tu"
    print(lru)
    lru["have"] = "as"
    print(lru)
    del lru
