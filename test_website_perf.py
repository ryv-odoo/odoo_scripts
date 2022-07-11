import grequests
import time

urls = [
    "http://127.0.0.1:8069/",  # 9 t-cache get
    "http://127.0.0.1:8069/shop",  # 35 t-cache get
    "http://127.0.0.1:8069/blog",  # 25 t-cache get
    "http://127.0.0.1:8069/event",  # 21 t-cache get
]

parallel_request = 2

request_getters = [grequests.get(urls[i % len(urls)]) for i in range(12)]

s = time.time_ns()
response = grequests.map(request_getters, size=parallel_request)
print(f"Warmup (12 requests) takes {((time.time_ns() - s) / 1_000_000_000):.4f} sec")

request_getters = [grequests.get(urls[i % len(urls)]) for i in range(500)]
s = time.time_ns()
response = grequests.map(request_getters, size=parallel_request)
print(f"200 requests takes {((time.time_ns() - s) / 1_000_000_000):.4f} sec")
