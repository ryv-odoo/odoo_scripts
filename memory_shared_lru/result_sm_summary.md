

# Old Version (Exclusive Lock)

- 1 Worker (No congestion):
    - Time of test: 1.4355 sec (warmup) - 12.1363 sec (200 requests)
    - Time consumed in GET: mean = 0.0527 ms, total = 477.7197 ms
- 2 Workers (Load at 50 %):
    - Time of test: 1.1099 sec (warmup) - 5.9613 sec (200 requests)
    - Time consumed in GET: mean = 0.0729 ms, total = 549.8484 ms
- 4 Workers (Load at 100 %):
    - Time of test: 0.9926 sec (warmup) - 3.9111 sec (200 requests)
    - Time consumed in GET: mean = 0.0798 ms, total = 723.7046 ms

# New version (Read Preferring Write Lock)

## Touch only 1 time on 7

- 1 Worker (No congestion):
    - Time of test: 1.5919 sec (warmup) - 11.6313 sec (200 requests)
    - Time consumed in GET: mean = 0.0548 ms, total = 497.5186 ms
- 2 Workers (Load at 50 %):
    - Time of test: 1.1350 sec (warmup) - 5.9214 sec (200 requests)
    - Time consumed in GET: mean = 0.0625 ms, total = 567.1039 ms
- 4 Workers (Load at 100 %):
    - Time of test: 0.9068 sec (warmup) - 3.8680 sec (200 requests)
    - Time consumed in GET: mean = 0.0821 ms, total = 745.1979 ms

## Touch only when we have the write lock in ourself

- 1 Worker (No congestion):
    - Time of test: 1.4636 (warmup) - 11.7562 sec (200 requests)
    - Time consumed in GET: mean = 0.0554 ms, total = 502.5106 ms
- 2 Workers (Load at 50 %):
    - Time of test: 1.1720 sec (warmup) - 5.9135 sec (200 requests)
    - Time consumed in GET: mean = 0.0609 ms, total = 552.2370 ms
- 4 Workers (Load at 100 %):
    - Time of test: 0.9053 sec (warmup) - 3.8716 sec (200 requests)
    - Time consumed in GET: mean = 0.0804 ms, total = 729.1779 ms

(We can combine it with the 1 on 7 technique, useful ?)


