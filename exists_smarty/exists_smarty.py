import re
from statistics import mean
from statistics import quantiles


filenames = [
    'scripts/exists_smarty/test_only.txt',
    'scripts/exists_smarty/test_only_1.txt',
    'scripts/exists_smarty/test_only_2.txt',
    'scripts/exists_smarty/test_only_3.txt',
    'scripts/exists_smarty/test_only_4.txt',
    'scripts/exists_smarty/test_only_5.txt',
]

# exists() with speedup 0.0201ms vs 0.1944ms = 10.345093602139478% (1 records)
# exists() without speedup 0.2453ms vs 0.2285ms = 107.33492908810054% (1 records)

regex = re.compile(r"exists\(\) (\w+) speedup (.+)ms vs (.+)ms = (.+)% \((\d+) records\)")
time_with_res = list()
time_without_res = list()
nb_success = 0
for f in filenames:
    with open(f) as bef:
        lines = bef.readlines()
        for line in lines:
            res = regex.match(line)
            if not res:
                continue
            _type, time_with, time_without, _, nb_reco = str(res.group(1)), float(res.group(2)), float(res.group(3)), float(res.group(4)), int(res.group(5))

            time_with_res.append(time_with)
            time_without_res.append(time_without)

            if _type == 'with':
                nb_success += 1

print(f"Success: {((nb_success / len(time_with_res)) * 100):.4f} %")
print("- With optimization")
print(f"\t* mean = {mean(time_with_res):.4f} ms")
print(f"\t* sum = {sum(time_with_res):.4f} ms")
print(f"\t* max = {max(time_with_res):.4f} ms")
print(f"\t* min = {min(time_with_res):.4f} ms")
print(f"\t* decile = {quantiles(time_with_res, n=10)} ms")

print("- Without optimization")
print(f"\t* mean = {mean(time_without_res):.4f} ms")
print(f"\t* sum = {sum(time_without_res):.4f} ms")
print(f"\t* max = {max(time_without_res):.4f} ms")
print(f"\t* min = {min(time_without_res):.4f} ms")
print(f"\t* decile = {quantiles(time_without_res, n=10)} ms")
