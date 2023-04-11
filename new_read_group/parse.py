import re
import sys

from statistics import NormalDist, fmean, median

f_before = sys.argv[1]
f_after = sys.argv[2]

re_line = re.compile(r"(.+) \+\- (.+) ms (.+) : (.+) - (.+)")


ratios = []

slowers = []
slowers_diff = []
fasters = []
fasters_diff = []
with open(f_before, "rt") as f1, open(f_after, "rt") as f2:
    matches_before = [re_line.match(line) for line in f1.readlines() if re_line.match(line)]
    matches_after = [re_line.match(line) for line in f2.readlines() if re_line.match(line)]

    for i, (matche_before, matche_after) in enumerate(zip(matches_before, matches_after)):
        mean_1, std_1, method_1, model_1, domain_1 = matche_before.groups()
        mean_2, std_2, method_2, model_2, domain_2 = matche_after.groups()
        mean_1, std_1 = float(mean_1), float(std_1)
        mean_2, std_2 = float(mean_2), float(std_2)
        # To check that the file is similar
        # if model_1 == model_2 == 'ir.attachment()':
        #     if method_1 != method_2:
        #         print(f"Line {i} differ {(method_1, model_1, domain_1)} != {(method_2, model_2, domain_2)}")
        #         break
        # elif (method_1, model_1, domain_1) != (method_2, model_2, domain_2):
        #     if domain_1 != domain_2 and (('date' in domain_1 and 'date' in domain_2) or (method_1 in '_get_mo_count')):
        #         continue
        #     print(f"Line {i} differ {(method_1, model_1, domain_1)} != {(method_2, model_2, domain_2)}")
        #     break
        n_1 = NormalDist(mean_1, std_1 or 0.0000001)
        n_2 = NormalDist(mean_2, std_2 or 0.0000001)
        if 'ir.attachment' in model_1:  # Before security check was broken
            continue

        if mean_2 < mean_1:
            # After faster
            ratio = (mean_1 - mean_2) / mean_1
        else:
            ratio = - ((mean_2 - mean_1) / mean_2)

        ratios.append(ratio)

        print(i, model_1[:30], method_1, mean_1, mean_2, ratio)


    #     if n_1.overlap(n_2) < 0.05:
    #         if n_1.mean < n_2.mean:
    #             percentage_slower = ((n_2.mean - n_1.mean) / n_1.mean) * 100
    #             print(f"Slower {percentage_slower:.4f} %", i, model_1[:30], method_1, mean_1, mean_2)
    #             slowers.append(percentage_slower)
    #             slowers_diff.append(n_2.mean - n_1.mean)
    #         if n_1.mean > n_2.mean:
    #             percentage_faster = ((n_1.mean - n_2.mean) / n_2.mean) * 100
    #             print(f"Faster {percentage_faster:.4f} %", i, model_1[:30], method_1, mean_1, mean_2)
    #             fasters.append(percentage_faster)
    #             fasters_diff.append(n_1.mean - n_2.mean)

    # print(f"Slower {len(slowers)}/{len(matches_before)}: sum_difference = {sum(slowers_diff):.4f}, mediam % {median(slowers):.4f}, mean % {fmean(slowers):.4f}")
    # print(f"Faster {len(fasters)}/{len(matches_before)}: sum_difference = {sum(fasters_diff):.4f}, mediam % {median(fasters):.4f}, mean % {fmean(fasters):.4f}")
    def ratio_to_time_faster(ratio):
        return (1 / (1 - ratio))
    print(f"In average new read_group is {fmean(ratios)} -> {ratio_to_time_faster(fmean(ratios))} faster")
    print(f"Median: {median(ratios)} -> {ratio_to_time_faster(median(ratios))} faster")
    print(f"Max: {max(ratios)} -> {ratio_to_time_faster(max(ratios))} faster")
    print(f"Min: {min(ratios)} -> {ratio_to_time_faster(min(ratios))} faster")
