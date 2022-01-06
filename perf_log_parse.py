from collections import defaultdict
import sys
from statistics import fmean, pstdev
import matplotlib.pyplot as plt
import tabulate

from odoo_scripts.misc import BLUE, GREEN, RED, RESET, YELLOW


SIZES = [1, 3, 5, 10, 101, 1000]
MODULE_INSTALLED = "purchase,sale,mrp,project"

FLAG_TO_DESC = {
    "create": "`create` method",
    "_create": "`_create` method",
    "insert_loop": "Insertion loop",
    "insert": "INSERT INTO",
}

def parse_lines_create(lines, match):
    by_model = defaultdict(lambda: defaultdict(list))
    nb_by_model = defaultdict(list)
    by_size = defaultdict(list)
    by_model_size = defaultdict(list)
    global_time = 0
    for line in lines:
        list_lines = line.split()
        if len(list_lines) != 5:
            continue
        create, model, nb, time, _ = list_lines
        if create != match:
            continue
        nb, time = float(nb), float(time)
        global_time += time
        by_model[model][nb].append(time)
        nb_by_model[model].append(nb)
        by_size[nb].append(time)
        by_model_size[(model, nb)].append(time)
    return len(lines), global_time, by_model, nb_by_model, by_size, by_model_size

def remove_outliner_by_model_size(datas):
    outlier_thr = 2

    for key in datas:
        _, _, by_model, _, _, by_model_size = datas[key]
        for key, values in by_model_size.items():
            mean = fmean(values)
            std = pstdev(values)
            # outlier = [val for val in values if (val > (mean + outlier_thr * std)) or (val < (mean - outlier_thr * std)) ]
            # print(f"Outliers {key}: {len(outlier)} / {len(values)}")
            by_model_size[key] = [val for val in values if not ((val > (mean + outlier_thr * std)) or (val < (mean - outlier_thr * std)))]

        for model, size_dict in by_model.items():
            new_values = {}
            for size, values in size_dict.items():
                mean = fmean(values)
                std = pstdev(values)
                new_values[size] = [val for val in values if not ((val > (mean + outlier_thr * std)) or (val < (mean - outlier_thr * std)))]
            by_model[model] = new_values

def print_results(lenn, global_t, by_model, nb_by_model, by_size, by_model_size):
    print(f"Parse {lenn} lines ({global_t} sec = {int(global_t // 60)} min {int(global_t % 60)} sec)")
    for s in SIZES:
        if s in by_size:
            print(f"Size {s} : {fmean(by_size[s])} sec in average")

def parse_log_file(filename):
    datas = {}
    with open(filename) as bef:
        lines = bef.readlines()
        print(f"-------------- {filename} ----------------")
        for k, v in FLAG_TO_DESC.items():
            lenn, global_t, by_model, nb_by_model, by_size, by_model_size = parse_lines_create(lines, k)
            print(" -- " + v)
            print_results(lenn, global_t, by_model, nb_by_model, by_size, by_model_size)
            datas[k] = (lenn, global_t, by_model, nb_by_model, by_size, by_model_size)

    return datas

def get_models_most_data(data):
    _, _, _, nb_by_model, _, by_model_size = data

    def filter_with_sample(model_name):
        return all(len(by_model_size.get((model_name, s), [])) > 5 for s in SIZES)

    best = sorted([(sum(v), k) for k, v in nb_by_model.items() if filter_with_sample(k)], reverse=True)
    # best = sorted([(sum(v), k) for k, v in nb_by_model.items()], reverse=True)
    return [b[1] for b in best]


def graph_all_creates_comparison(datas, models, title=""):
    # - Pourcentage _create vs insert data vs create (before / after) by model + size
    width = 0.35
    fig, axs = plt.subplots(3)
    fig.suptitle(f'Time spend in `create` vs `_create` vs insertion loop vs inversion (cumulative) - {title}')
    for i, s in enumerate((1, 10, 1000)):
        labels = ['Average'] + models
        means = {}
        for k, data in datas.items():
            _, _, _, _, by_size, by_model_size = data
            means[k] = [fmean(by_size[s])]
            for m in models:
                means[k].append(fmean(by_model_size[(m, s)]))

        ax = axs[(i % 3)]
        for k in datas:
            ax.bar(labels, means[k], width, label=FLAG_TO_DESC[k])

        ax.set_ylabel('Time in sec')
        ax.set_title(f'Batch SIZE={s}')
        ax.legend()

    # plt.show()
    fig.set_size_inches((20, 12), forward=False)
    plt.savefig(f'time_spend_{title}.png', bbox_inches='tight')

    fig, axs = plt.subplots(3)
    fig.suptitle(f'% Time spend in `create` vs `_create` vs insertion loop vs inversion (cumulative) - {title}')
    for i, s in enumerate((1, 10, 1000)):
        labels = ['Average'] + models
        means = {}
        _, _, _, _, by_size_create, by_model_size_created = datas["create"]
        for k, data in datas.items():
            _, _, _, _, by_size, by_model_size = data
            means[k] = [fmean(by_size[s]) / fmean(by_size_create[s]) * 100]
            for m in models:
                means[k].append(fmean(by_model_size[(m, s)]) / fmean(by_model_size_created[(m, s)]) * 100)

        ax = axs[(i % 3)]
        for k in datas:
            ax.bar(labels, means[k], width, label=FLAG_TO_DESC[k])

        ax.set_ylabel('% Time of `create`')
        ax.set_title(f'Batch SIZE={s}')
        ax.legend()

    # plt.show()
    fig.set_size_inches((20, 12), forward=False)
    plt.savefig(f'%_time_spend_{title}.png', bbox_inches='tight')


def graph_average_comparison(data_before, data_after, models):
    _, _, by_model, _, _, _ = data_before
    _, _, by_model_after, _, _, _ = data_after

    # plot
    fig, ax = plt.subplots()
    fig.suptitle("Insertion Loop time, before vs after")
    for model in models:
        x, y = [], []
        for size, values in sorted(by_model[model].items(), key= lambda x: x[0], reverse=True):
            if len(values) < 3:
                continue
            x.append(fmean(values))
            y.append(int(size))
        ax.plot(y, x, 'x:', label=f"Before: {model}")

    plt.gca().set_prop_cycle(None)

    for model in models:
        x, y = [], []
        for size, values in sorted(by_model_after[model].items(), key= lambda x: x[0], reverse=True):
            if len(values) < 3:
                continue
            x.append(fmean(values))
            y.append(int(size))
        ax.plot(y, x, 'X--', label=f"After: {model}")
    ax.legend()
    ax.set_ylabel("Time in Sec")
    ax.set_xlabel("Batch Size")
    plt.xscale('log')
    fig.set_size_inches((20, 12), forward=False)
    plt.savefig('time_vs_batch_time.png', bbox_inches='tight', dpi=400)


def table_size_solution(data_before, data_after, bests_models):
    # - Size vs time of insert data of each model table
    # (x <sec> +- x <std * 2>)
    headers = ["Batch Size\nModel"]
    tabulate.PRESERVE_WHITESPACE = True
    for s in SIZES:
        headers.append(f"{s}\nbefore: μ ± σ² msec (n)\nafter : μ ± σ² msec (n)")
    tablefmt = "grid"
    _, _, _, _, by_size, by_model_size = data_before
    _, _, _, _, by_size_after, by_model_size_after = data_after

    def get_row_infos(d, d_after):
        if len(d) < 2 or len(d_after) < 2:
            return ["" * 3]
        mean_before = fmean(d) * 1000
        mean_after = fmean(d_after) * 1000
        std_before = pstdev(d) * 1000
        std_after = pstdev(d_after) * 1000

        mean_impro = ((mean_after / mean_before)) - 1
        std_impro = (std_after / mean_after)
        if (mean_impro + std_impro) < 0:
            color_impro = GREEN
        elif (mean_impro - std_impro) > 0:
            color_impro = RED
        elif mean_impro > 0:
            color_impro = YELLOW
        else:
            color_impro = BLUE

        color_variance_after = RED if (mean_after / std_after) < 2.0 else RESET
        color_variance_before = RED if (mean_before / std_before) < 2.0 else RESET
        return [
            f"{mean_before:>7.3f} ± {color_variance_before}{std_before:>6.3f}{RESET} ({len(d)})",
            f"{mean_after:>7.3f} ± {color_variance_after}{std_after:>6.3f}{RESET} ({len(d_after)})",
            f"{color_impro}{mean_impro:>+7.1%}{RESET} ± {std_impro:>5.1%}",
        ]

    row_ave = ["Average"]
    tab = [row_ave]
    for s in SIZES:
        d = by_size[s]
        d_after = by_size_after[s]
        row_ave.append("\n".join(get_row_infos(d, d_after)))

    for model in bests_models:
        row = [model]
        tab.append(row)
        for s in SIZES:
            d = by_model_size[(model, s)]
            d_after = by_model_size_after[(model, s)]
            row.append("\n".join(get_row_infos(d, d_after)))

    print(tabulate.tabulate(tab, headers, tablefmt=tablefmt, colalign=['left' for _ in headers]))

TO_COMPARE = [
    "before.log",
    "after.log",
]

if len(sys.argv) > 1:
    TO_COMPARE = sys.argv[1:]


models = ['worst.case', 'ir.property', 'mail.message', 'mail.followers', 'stock.move', 'project.task', 'res.partner', 'product.product', 'product.template', 'product.supplierinfo', ]

for f1, f2 in zip(TO_COMPARE, TO_COMPARE[1:]):
    data_f1 = parse_log_file(f1)
    data_f2 = parse_log_file(f2)

    bests_models = models or get_models_most_data(data_f1['insert'])[:30]

    remove_outliner_by_model_size(data_f1)
    remove_outliner_by_model_size(data_f2)

    for flag in FLAG_TO_DESC:
        print(" --- ", flag)
        print(f"{f1} vs {f2}")
        table_size_solution(data_f1[flag], data_f2[flag], models)

    graph_average_comparison(data_f1["insert_loop"], data_f2["insert_loop"], bests_models)
    comparason_model = get_models_most_data(data_f1['insert_loop'])[:8]
    graph_all_creates_comparison(data_f1, comparason_model, "Before")
    graph_all_creates_comparison(data_f2, comparason_model, "After")


# Idea of graph:
# - Create 1 by model (before / After)
# - Depending of the value of split_every

# Number fields ?? vs insert data

