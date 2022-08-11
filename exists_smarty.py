from collections import defaultdict
import re
from statistics import mean

filename = 'log_exists.log'


regex = re.compile(r"(.+): ([^\s]+) ms \((\d+) real records, (\d+) false record")
res_time = defaultdict(list)
res_real_rec = defaultdict(list)
res_false_rec = defaultdict(list)
with open(filename) as bef:
    lines = bef.readlines()
    for line in lines:
        res = regex.match(line)
        assert res
        _type, time, real_rec, false_rec = str(res.group(1)), float(res.group(2)), int(res.group(3)), int(res.group(4))
        # OPTIMISATION (success): 0.0049 ms (1 real records, 0 false record)
        # OPTIMISATION (fail): 0.0077 ms (1 real records, 0 false record)
        # QUERY: 0.2238 ms (1 real records, 0 false record)
        res_time[_type].append(time)
        res_real_rec[_type].append(real_rec)
        res_false_rec[_type].append(false_rec)

print("TIME: ")
for _type, res in res_time.items():
    print(f"\t{_type}:")
    print(f"\t\t* count = {len(res)}")
    print(f"\t\t* mean = {mean(res)} ms")
    print(f"\t\t* sum = {sum(res)} ms")
    print(f"\t\t* max = {max(res)} ms")
    print(f"\t\t* min = {min(res)} ms")

print("REAL REC")
for _type, res in res_real_rec.items():
    print(f"\t{_type}: count = {len(res)}, mean = {mean(res)}, sum = {sum(res)}")
    print(f"\t\t* count = {len(res)}")
    print(f"\t\t* mean = {mean(res)}")
    print(f"\t\t* sum = {sum(res)}")
    print(f"\t\t* max = {max(res)}")
    print(f"\t\t* min = {min(res)}")

print("SUMMARY:")
success_rate = (len(res_time['OPTIMISATION (success)']) * 100 / len(res_time['OPTIMISATION (fail)']))
gain_by_success = mean(res_time['QUERY']) - mean(res_time['OPTIMISATION (success)'])
loss_by_fail = mean(res_time['OPTIMISATION (fail)'])
print(f"\t- Success Rate: {success_rate:.4f} %")
print(f"\t- Gain by Success: {gain_by_success:.4f} ms")
print(f"\t- Loss by Fail: {loss_by_fail:.4f} ms")
print(f"\t- Mean Gain: {(success_rate / 100 * gain_by_success) + ((1 - success_rate / 100) * loss_by_fail)} ms")
print(f"\t- % Gain: {success_rate * gain_by_success} ms")




# print("FALSE REC")
# for _type, res in res_false_rec.items():
#     print(f"\t{_type}: count = {len(res)}, mean = {mean(res)}, sum = {sum(res)}")
#     print(f"\t\t* count = {len(res)}")
#     print(f"\t\t* mean = {mean(res)}")
#     print(f"\t\t* sum = {sum(res)}")
#     print(f"\t\t* max = {max(res)}")
#     print(f"\t\t* min = {min(res)}")
