#from multiprocessing.managers import SharedMemoryManager
from contextlib import contextmanager
from fcntl import lockf, LOCK_EX, LOCK_SH, LOCK_UN, LOCK_NB
import itertools
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import Lock
import numpy
import marshal
import functools


class RWLock:
    def __init__(self, name) -> None:
        self.f = open(name, 'r+')

    def release(self):
        lockf(self.f, LOCK_UN)

    def acquire_write_lazy(self):
        cmd = LOCK_EX | LOCK_NB
        try:
            lockf(self.f, cmd)
            return True
        except OSError:
            return False

    @contextmanager
    def acquire_write(self):
        lockf(self.f, LOCK_EX)
        yield
        lockf(self.f, LOCK_UN)

    @contextmanager
    def acquire_read(self):
        lockf(self.f, LOCK_SH)
        yield
        lockf(self.f, LOCK_UN)

    def __del__(self):
        self.f.close()

class lru_shared(object):
    def __init__(self, size=4096):
        assert size > 0 and (size & (size - 1) == 0), "LRU size must be an exponantiel of 2"
        self.size = size
        self.mask = size - 1
        self.max_length = size // 3  # should be always < than size. more it is big more there is hash conflict
        byte_size = size * 4096  # 4096 * 4096 = 16 MB by default
        try:
            self.sm = SharedMemory(name="odoo_sm_lru_shared", size=byte_size, create=True)
            self.sm.buf[:] = b'\x00' * byte_size
        except FileExistsError:
            self.sm = SharedMemory(name="odoo_sm_lru_shared")
            if self.sm.size != byte_size:
                raise MemoryError("The size of the shared memory doesn't match, exit")

        data = [
            ('head', numpy.int32, (3,)),     # Contains root, length and free_len : 12 bytes
            ('ht', numpy.int64, (size,)),    # hash array: 8 bytes * size = 32768 bytes
            ('prev', numpy.int32, (size,)),  # previous index array (of the linked list), if == -1, this index is empty: 4 bytes * size
            ('nxt', numpy.int32, (size,)),   # next index array (of the linked list), if == -1, this index is empty : 4 bytes * size
            ('data_idx', numpy.uint64, (size, 2)),  # data (position, size) array
            ('data_free', numpy.uint64, (size + 9, 2))
        ]
        start = 0
        for (name, dtype, sz) in data:
            end = start + dtype().nbytes * functools.reduce(lambda x, y: x * y, sz, 1)
            setattr(self, name, numpy.ndarray(sz, dtype=dtype, buffer=self.sm.buf[start:end]))
            start = end

        self.data = self.sm.buf[end: byte_size]
        self.data_free[0] = [0, (byte_size) - end]
        self.lock = RWLock('/tmp/odoo_sm_lock.lock')

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
            raise MemoryError("No shared memory for key/value data")

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

    def _set_entry(self, index, key, prev, nxt):
        self.prev[index] = prev
        self.nxt[index] = nxt
        self.ht[index] = key

    def _get_entry(self, index):
        return (self.ht[index], self.prev[index], self.nxt[index])

    def _index_iterator(self, hash_):
        for i in range(self.size):
            yield (hash_ + i) & self.mask

    def data_get(self, index):
        return marshal.loads(self.data[self.data_idx[index, 0]:])

    def lookup(self, key_, hash_):
        for index in self._index_iterator(hash_):
            key_hash, prev, nxt = self._get_entry(index)
            if not key_hash:
                return (index, key_hash, prev, nxt, None)
            if key_hash == hash_:
                (key_full, val) = self.data_get(index)
                if key_full == key_:
                    return (index, key_hash, prev, nxt, val)
        raise MemoryError("Hash table full, doesn't make any sense, LRU is broken")

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def lru_pop(self):
        root = self.root
        if root == -1:
            return
        _, prev_index, _ = self._get_entry(root)
        self._del_index(prev_index, *self._get_entry(prev_index))

    def lru_touch(self, index, key, prev, nxt):
        root = self.root
        if root == -1:
            self.root = index
            self._set_entry(index, key, index, index)
            return
        if root == index:
            return

        # Pop me from neibourg if i am not new in the list
        if prev is not None and nxt is not None:
            self.prev[nxt] = prev
            self.nxt[prev] = nxt

        # Change the root to be my nxt and me to have as prev the last node
        root_prev = self.prev[root]
        self.nxt[root_prev] = index
        self.nxt[index] = root
        self.prev[index] = root_prev
        self.prev[root] = index

        self.root = index

    def _del_index(self, index, key, prev, nxt):
        # TODO: there is a bug here
        if prev == index:
            self.root = -1
        else:
            self.prev[nxt] = prev
            self.nxt[prev] = nxt
            if self.root == index:
                self.root = nxt

        self._free(index)
        self._set_entry(index, 0, 0, 0)
        self.length -= 1

        # Delete the keys that are between this element, and the next free spot, having
        # an index lower or equal to the position we delete (conflicts handling).
        def change_index(old_index, new_index):
            key_i, prev_i, next_i = self._get_entry(old_index)
            self.nxt[prev_i] = new_index
            self.prev[next_i] = new_index
            self._set_entry(new_index, key_i, prev_i, next_i)
            self._set_entry(old_index, 0, 0, 0)
            self.data_idx[new_index] = self.data_idx[old_index][:]
            self.data_idx[old_index] = [0, 0]
            if self.root == old_index:
                self.root = new_index

        entry_empty = index
        for i in itertools.chain(range(index + 1, self.size), range(index)):
            if not self.ht[i]:
                break
            if (i > index and (self.ht[i] & self.mask) <= entry_empty) or (i < index and (self.ht[i] & self.mask) >= entry_empty):
                change_index(i, entry_empty)
                entry_empty = i

    def __getitem__(self, key_):
        # have_lock = self.lock.acquire(block=False)
        # if not have_lock:  # Or block ?
        #     raise KeyError("Lock cannot be acquire")
        hash_ = hash(key_)
        with self.lock.acquire_read():
            index, key, prev, nxt, val = self.lookup(key_, hash_)
        if val is None:
            raise KeyError(f"{key_} doesn't not exist")
        # self.touch = (self.touch + 1) & 7
        # if not self.touch:   # lru touch every 8th reads: not sure about this optim?
        if self.lock.acquire_write_lazy():
            try:
                self.lru_touch(index, key, prev, nxt)
            finally:
                self.lock.release()
        return val

    def __setitem__(self, key, value):
        hash_ = hash(key)
        if not hash_:
            raise KeyError(f"hash_ of key is falsy for {key} ({hash_}) {value}, Not supported for now")
        with self.lock.acquire_write():
            index, _key, _prev, _nxt, val = self.lookup(key, hash_)
            if val is None:
                self.length += 1
            else:
                self._free(index)
            self.ht[index] = hash_
            self.lru_touch(index, hash_, None, None)
            self._malloc(index, (key, value))
            while self.length > self.max_length:
                self.lru_pop()

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
        hash_ = hash(key)
        with self.lock.acquire_write():
            index, key, prev, nxt, val = self.lookup(key, hash_)
            if val is None:
                KeyError(f"{key} doesn't not exist, cannot delete it")
            self._del_index(index, key, prev, nxt)

    def __iter__(self):
        with self.lock.acquire_read():
            if self.root == -1:
                return iter(())
            node_index = self.root
            while True:
                _hash_key, _prev, nxt = self._get_entry(node_index)
                data = self.data_get(node_index)
                yield data[0], data[1]
                node_index = nxt
                if node_index == self.root:
                    break

    def __str__(self):
        with self.lock.acquire_read():
            if self.root == -1:
                return '[]'
            node_index = self.root
            result = []
            while True:
                _hash_key, _prev, nxt = self._get_entry(node_index)
                data = self.data_get(node_index)
                result.append(f'{data[0]} (hash & mask: {_hash_key & self.mask}, index: {node_index}, hash: {_hash_key:+}): {data[1]}')
                node_index = nxt
                if node_index == self.root:
                    return f'hashtable size: {self.size}, mask: {self.mask}, len: {str(self.length)}\n' + '\n'.join(result)


if __name__=="__main__":
    lru = lru_shared(16)

    # hash of key == 0 doesn't work now
    lru[lru.size] = "test"  # hash & mask = 0, should be at index 0
    lru[1] = "other"  # hash & mask = 1 should be at index 1
    lru[lru.size * 2] = "test * 2"  # hash & mask = 0, should be at index 2

    del lru[1]

    # now lru.size * 2 should be in the index 1
    assert lru.ht[1] == lru.size * 2, f"{lru.ht[1]} != {lru.size * 2}"
    assert lru[lru.size * 2] == "test * 2"
    assert lru[lru.size] == "test"
    lru_list = [(key, value) for key, value in lru]
    assert lru_list == [(lru.size, "test"), (lru.size * 2, "test * 2")], str(lru_list)

    lru[lru.size - 1] = "blu"  # hash & mask = 15 should be at index 15
    lru[(lru.size * 2) - 1] = "bla" # hash & mask = 15 (hash of 31) should be at index 2

    assert lru.ht[2] == 31, f"{lru.ht[lru.size - 1]} != {31}"
    assert lru[(lru.size * 2) - 1] == "bla"
    assert lru[lru.size - 1] == "blu"

    del lru[lru.size - 1]  # (lru.size * 2) - 1 should go at index 15

    assert lru[(lru.size * 2) - 1] == "bla"
    assert lru.ht[2] == 0
    assert lru.ht[15] == 31
    assert lru.ht[1] == lru.size * 2, f"{lru.ht[1]} != {lru.size * 2}"
    assert lru[lru.size * 2] == "test * 2"
    assert lru[lru.size] == "test"

    # test lru
    lru_list = [(key, value) for key, value in lru]
    assert lru_list == [(lru.size, "test"), (lru.size * 2, "test * 2"), ((lru.size * 2) - 1, "bla")], str(lru_list)

    del lru


    print("Success")

