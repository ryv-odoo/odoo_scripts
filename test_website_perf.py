import grequests
import time
import sys

urls = [
    "http://127.0.0.1:8069/",  # 9 t-cache get
    "http://127.0.0.1:8069/shop",  # 35 t-cache get (16 after fix of chm)
    "http://127.0.0.1:8069/blog",  # 25 t-cache get
    "http://127.0.0.1:8069/event",  # 21 t-cache get
]

parallel_request = int(sys.argv[1])

request_getters = [grequests.get(urls[i % len(urls)]) for i in range(12)]

s = time.time_ns()
response = grequests.map(request_getters, size=parallel_request)
print(f"Warmup (12 requests) takes {((time.time_ns() - s) / 1_000_000_000):.4f} sec")

request_getters = [grequests.get(urls[i % len(urls)]) for i in range(500)]
s = time.time_ns()
response = grequests.map(request_getters, size=parallel_request)
print(f"200 requests takes {((time.time_ns() - s) / 1_000_000_000):.4f} sec")



# 1/ 2

# Warmup (12 requests) takes 1.6810 sec
# 200 requests takes 6.3384 sec
# Shared Cache counter statistics: 99.2017 % (ratio), 9072 / 73 (hit / miss), Override: 2 (same value), 0 (other value)
# Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
# Shared Cache time SET statistics: 73 items, mean = 0.0731, min = 0.0259, max = 0.2147 (i=7), sum = 5.3385, deciles = ['0.034987', '0.038577', '0.048798', '0.062085', '0.066651', '0.074132', '0.078542', '0.098715', '0.118056'] ms
# Shared Cache time GET statistics: 9072 items, mean = 0.0583, min = 0.0095, max = 2.0675 (i=8894), sum = 528.9387, deciles = ['0.013613', '0.019125', '0.028865', '0.037014', '0.044167', '0.051177', '0.057871', '0.069634', '0.119626'] ms


# 1 / 3
# Warmup (12 requests) takes 1.7919 sec
# 200 requests takes 6.3026 sec
# Shared Cache counter statistics: 99.1586 % (ratio), 9074 / 77 (hit / miss), Override: 6 (same value), 0 (other value)
# Shared Cache data statistics: 71 items, 0.00 % used (0.91 MB / 214740000.00 MB), mean = 0.012829 MB, min = 0.000303 MB, max = 0.128904 MB, deciles = ['0.000917', '0.002931', '0.003036', '0.003452', '0.004266', '0.007796', '0.011166', '0.015570', '0.034100'] MB
# Shared Cache time SET statistics: 77 items, mean = 0.0754, min = 0.0275, max = 0.2131 (i=7), sum = 5.8029, deciles = ['0.037551', '0.047747', '0.055912', '0.061741', '0.067096', '0.074565', '0.081304', '0.089880', '0.135408'] ms
# Shared Cache time GET statistics: 9074 items, mean = 0.0592, min = 0.0098, max = 1.4025 (i=6399), sum = 536.8945, deciles = ['0.013814', '0.019622', '0.029620', '0.037677', '0.044198', '0.050727', '0.058384', '0.070429', '0.117424'] ms




# 2022-08-08 08:33:36,581 25376 INFO master odoo.addons.product.populate.product_template: Set barcode on product variants (59913)
# 2022-08-08 08:35:50,787 25376 INFO master odoo.addons.product.populate.product_template: FInish
# 2022-08-08 08:35:50,804
# 2:14

# 2022-08-08 08:50:26,901 26803 INFO master odoo.addons.product.populate.product_template: Set barcode on product variants (59913)
# 2022-08-08 08:52:36,406 26803 INFO master odoo.cli.populate: Populated database for model product.template (total: 395.684751s) (average: 79.121126ms per record)
# 2022-08-08 08:52:36,406
