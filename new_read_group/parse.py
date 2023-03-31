

import re
import sys

f_before = sys.argv[1]
f_after = sys.argv[2]

re_line = re.compile(r"(.+) \+\- (.+) ms (.+) : (.+) - (.+)")


a = 0
with open(f_before, "rt") as f1, open(f_after, "rt") as f2:
    matches_before = [re_line.match(line) for line in f1.readlines() if re_line.match(line)]
    matches_after = [re_line.match(line) for line in f2.readlines() if re_line.match(line)]

    for i, (matche_before, matche_after) in enumerate(zip(matches_before, matches_after)):
        mean_1, std_1, method_1, model_1, domain_1 = matche_before.groups()
        mean_2, std_2, method_2, model_2, domain_2 = matche_after.groups()
        # To check that is correct
        # if model_1 == model_2 == 'ir.attachment()':
        #     if method_1 != method_2:
        #         print(f"Line {i} differ {(method_1, model_1, domain_1)} != {(method_2, model_2, domain_2)}")
        #         break
        # elif (method_1, model_1, domain_1) != (method_2, model_2, domain_2):
        #     if domain_1 != domain_2 and (('date' in domain_1 and 'date' in domain_2) or (method_1 in '_get_mo_count')):
        #         continue
        #     print(f"Line {i} differ {(method_1, model_1, domain_1)} != {(method_2, model_2, domain_2)}")
        #     break
        if float(mean_2) > float(mean_1):
            print(i, method_1, mean_1, mean_2)
            a += 1

    print(f"{a} slower on {len(matches_before)}")

