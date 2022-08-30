

import re

from statistics import quantiles

f_before = "before.log"
f_after = "after.log"

re_line = re.compile(r"modified takes (.*) ms \((.*) ms without sql time\) with (\d+) extra queries - (\d+)")


def get_stat(matches):
    time_total = [float(m.group(1)) for m in matches]
    time_nosql = [float(m.group(2)) for m in matches]
    extra_queries =  [int(m.group(3)) for m in matches]
    return time_total, time_nosql, extra_queries


with open(f_before, "rt") as f1, open(f_after, "rt") as f2:
    matches_before = [re_line.match(line) for line in f1.readlines() if re_line.match(line)]
    matches_after = [re_line.match(line) for line in f2.readlines() if re_line.match(line)]
    # assert len(matches_before) == len(matches_after), f"{len(matches_before)} != {len(matches_after)}"
    befores_stat, afters_stat = get_stat(matches_before), get_stat(matches_after)
    print(f"Before tot: {sum(befores_stat[0]):.3f} ms, nosql: {sum(befores_stat[1]):.3f} ms, extra sql : {sum(befores_stat[2])}")
    print(f"After  tot: {sum(afters_stat[0]):.3f} ms, nosql: {sum(afters_stat[1]):.3f} ms, extra sql : {sum(afters_stat[2])}")

    print(f"Before Decile nosql:{quantiles(befores_stat[1], n=10)}")
    print(f"After  Decile nosql:{quantiles(afters_stat[1], n=10)}")
