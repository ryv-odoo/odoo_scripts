import random
import grequests
import time

urls = [
    "http://127.0.0.1:8069/",
    "http://127.0.0.1:8069/shop",
    "http://127.0.0.1:8069/blog",
    "http://127.0.0.1:8069/event",
]

random.seed(5)

request_getters = [grequests.get(urls[i % len(urls)]) for i in range(12)]

s = time.time_ns()
response = grequests.map(request_getters, size=4)
print(f"Warmup (12 requests) takes {((time.time_ns() - s) / 1_000_000_000):.4f} sec")

request_getters = [grequests.get(urls[random.randint(0, len(urls) - 1)]) for _ in range(200)]
s = time.time_ns()
response = grequests.map(request_getters, size=4)
print(f"200 requests takes {((time.time_ns() - s) / 1_000_000_000):.4f} sec")
