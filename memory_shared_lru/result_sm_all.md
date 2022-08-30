

# Old Version (Exclusive Lock)

python ./scripts/test_website_perf.py 1
Warmup (12 requests) takes 1.4355 sec
200 requests takes 12.1363 sec

2022-08-09 09:18:36,180 22544 INFO master odoo.modules.shared_memory: Shared Cache counter statistics: 99.2234 % (ratio), 9072 / 71 (hit / miss), Override: 0 (same value), 0 (other value)
2022-08-09 09:18:36,186 22544 INFO master odoo.modules.shared_memory: Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
2022-08-09 09:18:36,210 22544 INFO master odoo.modules.shared_memory: Shared Cache time SET statistics: 71 items, mean = 0.0624, min = 0.0253, max = 0.1909 (i=19), sum = 4.4329, deciles = ['0.029928', '0.034239', '0.039039', '0.054401', '0.058670', '0.064294', '0.069928', '0.077010', '0.101582'] ms
2022-08-09 09:18:36,215 22544 INFO master odoo.modules.shared_memory: Shared Cache time GET statistics: 9072 items, mean = 0.0527, min = 0.0093, max = 1.1146 (i=748), sum = 477.7197, deciles = ['0.013087', '0.018077', '0.025778', '0.034267', '0.041464', '0.046150', '0.052476', '0.063802', '0.110063'] ms

python ./scripts/test_website_perf.py 2
Warmup (12 requests) takes 1.1099 sec
200 requests takes 5.9613 sec

2022-08-09 09:19:34,396 22700 INFO master odoo.modules.shared_memory: Shared Cache counter statistics: 99.2234 % (ratio), 9072 / 71 (hit / miss), Override: 0 (same value), 0 (other value)
2022-08-09 09:19:34,402 22700 INFO master odoo.modules.shared_memory: Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
2022-08-09 09:19:34,423 22700 INFO master odoo.modules.shared_memory: Shared Cache time SET statistics: 71 items, mean = 0.0729, min = 0.0318, max = 0.1908 (i=40), sum = 5.1744, deciles = ['0.037726', '0.043095', '0.053129', '0.062006', '0.066911', '0.071721', '0.081989', '0.097430', '0.111010'] ms
2022-08-09 09:19:34,428 22700 INFO master odoo.modules.shared_memory: Shared Cache time GET statistics: 9072 items, mean = 0.0606, min = 0.0095, max = 1.7651 (i=8411), sum = 549.8484, deciles = ['0.013605', '0.018919', '0.030021', '0.038437', '0.044159', '0.051770', '0.059049', '0.071479', '0.123603'] ms


 python ./scripts/test_website_perf.py 4
Warmup (12 requests) takes 0.9926 sec
200 requests takes 3.9111 sec

2022-08-09 09:20:26,259 22890 INFO master odoo.modules.shared_memory: Shared Cache counter statistics: 99.2017 % (ratio), 9072 / 73 (hit / miss), Override: 2 (same value), 0 (other value)
2022-08-09 09:20:26,265 22890 INFO master odoo.modules.shared_memory: Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
2022-08-09 09:20:26,286 22890 INFO master odoo.modules.shared_memory: Shared Cache time SET statistics: 73 items, mean = 0.0884, min = 0.0250, max = 0.3118 (i=29), sum = 6.4497, deciles = ['0.049466', '0.054469', '0.064129', '0.073664', '0.077598', '0.084916', '0.090410', '0.109291', '0.142382'] ms
2022-08-09 09:20:26,292 22890 INFO master odoo.modules.shared_memory: Shared Cache time GET statistics: 9072 items, mean = 0.0798, min = 0.0091, max = 3.3103 (i=1221), sum = 723.7046, deciles = ['0.014157', '0.020961', '0.035848', '0.044879', '0.051972', '0.059615', '0.068288', '0.089571', '0.177637'] ms



- 1 Worker (No congestion):
    - Time consumed in GET:
    - Time consumed in SET:
- 2 Workers (Load at 50 %):
    - Time consumed in GET:
    - Time consumed in SET:
- 4 Workers (Load at 100 %):
    - Time consumed in GET:
    - Time consumed in SET:

# New version (Read Preferring Write Lock)

## Touch only 1 time on 7

python ./scripts/test_website_perf.py 1
Warmup (12 requests) takes 1.5919 sec
200 requests takes 11.6313 sec

2022-08-09 09:22:00,826 23181 INFO master odoo.modules.shared_memory: Shared Cache counter statistics: 99.2234 % (ratio), 9072 / 71 (hit / miss), Override: 0 (same value), 0 (other value)
2022-08-09 09:22:00,832 23181 INFO master odoo.modules.shared_memory: Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
2022-08-09 09:22:00,853 23181 INFO master odoo.modules.shared_memory: Shared Cache time SET statistics: 71 items, mean = 0.0628, min = 0.0246, max = 0.1915 (i=1), sum = 4.4601, deciles = ['0.029464', '0.035713', '0.039854', '0.056567', '0.061014', '0.066666', '0.071463', '0.078130', '0.106453'] ms
2022-08-09 09:22:00,858 23181 INFO master odoo.modules.shared_memory: Shared Cache time GET statistics: 9072 items, mean = 0.0548, min = 0.0087, max = 2.8648 (i=7838), sum = 497.5186, deciles = ['0.012816', '0.018421', '0.026111', '0.034598', '0.040136', '0.046518', '0.054831', '0.067492', '0.107975'] ms


python ./scripts/test_website_perf.py 2
Warmup (12 requests) takes 1.1350 sec
200 requests takes 5.9214 sec

2022-08-09 09:22:43,672 23337 INFO master odoo.modules.shared_memory: Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
2022-08-09 09:22:43,693 23337 INFO master odoo.modules.shared_memory: Shared Cache time SET statistics: 72 items, mean = 0.0739, min = 0.0326, max = 0.1817 (i=6), sum = 5.3216, deciles = ['0.039095', '0.046020', '0.053759', '0.062270', '0.070532', '0.075355', '0.083244', '0.092763', '0.112781'] ms
2022-08-09 09:22:43,699 23337 INFO master odoo.modules.shared_memory: Shared Cache time GET statistics: 9073 items, mean = 0.0625, min = 0.0090, max = 1.8118 (i=6100), sum = 567.1039, deciles = ['0.013779', '0.019510', '0.029779', '0.038821', '0.045101', '0.051775', '0.061428', '0.075665', '0.120870'] ms



python ./scripts/test_website_perf.py 4
Warmup (12 requests) takes 0.9068 sec
200 requests takes 3.8680 sec

2022-08-09 09:23:46,577 23498 INFO master odoo.modules.shared_memory: Shared Cache counter statistics: 99.1689 % (ratio), 9069 / 76 (hit / miss), Override: 5 (same value), 0 (other value)
2022-08-09 09:23:46,584 23498 INFO master odoo.modules.shared_memory: Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
2022-08-09 09:23:46,605 23498 INFO master odoo.modules.shared_memory: Shared Cache time SET statistics: 76 items, mean = 0.0757, min = 0.0373, max = 0.2194 (i=18), sum = 5.7536, deciles = ['0.044050', '0.049711', '0.053000', '0.063219', '0.070105', '0.076586', '0.080751', '0.090449', '0.117531'] ms
2022-08-09 09:23:46,611 23498 INFO master odoo.modules.shared_memory: Shared Cache time GET statistics: 9076 items, mean = 0.0821, min = 0.0093, max = 8.6521 (i=1542), sum = 745.1979, deciles = ['0.014886', '0.021793', '0.035923', '0.044820', '0.051741', '0.059292', '0.069892', '0.089390', '0.170998'] ms

- 1 Worker (No congestion):
    - Time consumed in GET:
    - Time consumed in SET:
- 2 Workers (Load at 50 %):
    - Time consumed in GET:
    - Time consumed in SET:
- 4 Workers (Load at 100 %):
    - Time consumed in GET:
    - Time consumed in SET:

## Touch only when we have the write lock in ourself


python ./scripts/test_website_perf.py 1
Warmup (12 requests) takes 1.4636 sec
200 requests takes 11.7562 sec

2022-08-09 09:25:19,632 23796 INFO master odoo.modules.shared_memory: Shared Cache counter statistics: 99.2234 % (ratio), 9072 / 71 (hit / miss), Override: 0 (same value), 0 (other value)
2022-08-09 09:25:19,638 23796 INFO master odoo.modules.shared_memory: Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
2022-08-09 09:25:19,659 23796 INFO master odoo.modules.shared_memory: Shared Cache time SET statistics: 71 items, mean = 0.0614, min = 0.0188, max = 0.1856 (i=1), sum = 4.3574, deciles = ['0.028792', '0.032579', '0.036003', '0.053685', '0.060090', '0.063354', '0.070658', '0.077575', '0.111088'] ms
2022-08-09 09:25:19,665 23796 INFO master odoo.modules.shared_memory: Shared Cache time GET statistics: 9072 items, mean = 0.0554, min = 0.0120, max = 3.1243 (i=7436), sum = 502.5106, deciles = ['0.016187', '0.021497', '0.029788', '0.038493', '0.044188', '0.048738', '0.055599', '0.066329', '0.113642'] ms

python ./scripts/test_website_perf.py 2
Warmup (12 requests) takes 1.1720 sec
200 requests takes 5.9135 sec

2022-08-09 09:26:08,375 23945 INFO master odoo.modules.shared_memory: Shared Cache counter statistics: 99.2013 % (ratio), 9067 / 73 (hit / miss), Override: 2 (same value), 0 (other value)
2022-08-09 09:26:08,382 23945 INFO master odoo.modules.shared_memory: Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
2022-08-09 09:26:08,403 23945 INFO master odoo.modules.shared_memory: Shared Cache time SET statistics: 73 items, mean = 0.0770, min = 0.0262, max = 0.2143 (i=6), sum = 5.6192, deciles = ['0.037023', '0.043069', '0.054026', '0.061738', '0.068993', '0.075179', '0.080033', '0.111836', '0.130556'] ms
2022-08-09 09:26:08,409 23945 INFO master odoo.modules.shared_memory: Shared Cache time GET statistics: 9072 items, mean = 0.0609, min = 0.0096, max = 1.8042 (i=3614), sum = 552.2370, deciles = ['0.016400', '0.021953', '0.033198', '0.040880', '0.048135', '0.054509', '0.060845', '0.070231', '0.117144'] ms

python ./scripts/test_website_perf.py 4
Warmup (12 requests) takes 0.9053 sec
200 requests takes 3.8716 sec

2022-08-09 09:26:55,703 24102 INFO master odoo.modules.shared_memory: Shared Cache counter statistics: 99.1901 % (ratio), 9063 / 74 (hit / miss), Override: 3 (same value), 0 (other value)
2022-08-09 09:26:55,709 24102 INFO master odoo.modules.shared_memory: Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
2022-08-09 09:26:55,731 24102 INFO master odoo.modules.shared_memory: Shared Cache time SET statistics: 74 items, mean = 0.0850, min = 0.0360, max = 0.6481 (i=18), sum = 6.2873, deciles = ['0.041805', '0.044985', '0.055662', '0.063864', '0.069723', '0.078198', '0.081842', '0.098272', '0.141083'] ms
2022-08-09 09:26:55,737 24102 INFO master odoo.modules.shared_memory: Shared Cache time GET statistics: 9071 items, mean = 0.0804, min = 0.0101, max = 5.4685 (i=5977), sum = 729.1779, deciles = ['0.016843', '0.024046', '0.039622', '0.047727', '0.054397', '0.061570', '0.069655', '0.082378', '0.144179'] ms

- 1 Worker (No congestion):
    - Time consumed in GET:
    - Time consumed in SET:
- 2 Workers (Load at 50 %):
    - Time consumed in GET:
    - Time consumed in SET:
- 4 Workers (Load at 100 %):
    - Time consumed in GET:
    - Time consumed in SET:

(We can combine it with the 1 on 7 technique, useful ?)


