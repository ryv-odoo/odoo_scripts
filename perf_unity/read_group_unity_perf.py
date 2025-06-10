from time import time_ns
import grequests
import requests
from functools import partial
from statistics import fmean, stdev

# Branch for test:

READ_SPEC_CRM = {
    "stage_id": {"fields": {"display_name": {}}},
    "probability": {},
    "active": {},
    "company_currency": {"fields": {"display_name": {}}},
    "recurring_revenue_monthly": {},
    "team_id": {"fields": {"display_name": {}}},
    "won_status": {},
    "color": {},
    "name": {},
    "expected_revenue": {},
    "partner_id": {"fields": {"display_name": {}}},
    "tag_ids": {"fields": {"display_name": {}, "color": {}}},
    "lead_properties": {},
    "priority": {},
    "activity_ids": {"fields": {}},
    "activity_exception_decoration": {},
    "activity_exception_icon": {},
    "activity_state": {},
    "activity_summary": {},
    "activity_type_icon": {},
    "activity_type_id": {"fields": {"display_name": {}}},
    "user_id": {"fields": {"display_name": {}}},
}

READ_SPEC_TASK = {}

READ_SPEC_PROJECT = {}


SESSION_ID = ""
if not SESSION_ID:
    print("Missing ", SESSION_ID)
    exit()

COOKIES = {
    "session_id": SESSION_ID,
}
BASE_URL = "http://127.0.0.1:8069"
MAX_PARALLEL_REQUEST = 6  # Max of chrome

SCENARIOS = [
    # ------- crm.lead
    # Open CRM - Kanban - Filter: default (none) - all open lead are loaded
    {
        "name": "Open CRM - Kanban - Filter: default (none) - all open lead are loaded",
        "model": "crm.lead",
        "domain": [["type", "=", "opportunity"]],
        "groupby": ["stage_id"],
        "aggregates": [
            "probability:avg",
            "recurring_revenue_monthly:sum",
            "color:sum",
            "expected_revenue:sum",
        ],
        "read_specification": READ_SPEC_CRM,
        "auto_unfold": True,
        "unfold_read_default_limit": 80,
    },
    # Open CRM - Kanban - Filter: Creation Date = 2025 - Groupby month
    {
        "name": "Open CRM - Kanban - Filter: Creation Date = 2025 - Groupby month",
        "model": "crm.lead",
        "domain": [
            "&",
            ["type", "=", "opportunity"],
            "&",
            ["create_date", ">=", "2024-12-31 23:00:00"],
            ["create_date", "<=", "2025-12-31 22:59:59"],
        ],
        "groupby": ["create_date:month"],
        "aggregates": [
            "probability:avg",
            "recurring_revenue_monthly:sum",
            "color:sum",
            "expected_revenue:sum",
        ],
        "read_specification": READ_SPEC_CRM,
        "auto_unfold": True,
        "unfold_read_default_limit": 80,
    },
    # Open CRM - Kanban - Filter: default (none) - groupby lang_code (related field)
    {},
    # Open CRM - Kanban - Filter : search 'test' (default groupby)
    {},
    # Open CRM - Kanban - Filter: included active - groupby active
    {},
    # Open CRM - List view - with multiple group loaded, TODO
    {},
    # Open CRM - List view - with multiple group loaded, TODO
    {},
    # ------- project.task
    # Kanban: Open Framework Python project - No filters
    {},
    # Kanban: Open Help project - No filter
    {},
    # Kanban:
]


def get_url(model, method):
    return f"{BASE_URL}/web/dataset/call_kw/RYV/{model}/{method}"


def get_default_json_data(model, method):
    return {
        "id": 13,  # balec
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": model,
            "method": method,
            "args": [],
            "kwargs": {
                "context": {
                    "allowed_company_ids": [1],
                    "lang": "en_US",
                    "tz": "Europe/Brussels",
                    "read_group_expand": True,
                },
            },
        },
    }


def old_way(scenario, new_groups, with_issue=True):
    model = scenario["model"]
    url = get_url(model, "web_read_group")
    json_data = get_default_json_data(model, "web_read_group")

    json_data["params"]["kwargs"].update(
        {
            "domain": scenario["domain"],
            "groupby": scenario["groupby"],
            "aggregates": scenario["aggregates"],
        }
    )

    start = time_ns()
    res = requests.post(url, json=json_data, cookies=COOKIES)
    delay_user = time_ns() - start
    worker_time = res.elapsed.total_seconds() * 1000

    groups = res.json()["result"]["groups"]

    def web_search_read_data(group):
        data = get_default_json_data(model, "web_search_read")
        data["params"]["kwargs"].update(
            {
                "domain": scenario["domain"] + group["__extra_domain"],
                "specification": scenario["read_specification"],
                "count_limit": 10001
                if with_issue
                else scenario["unfold_read_default_limit"],
                "limit": scenario["unfold_read_default_limit"],
            }
        )
        return data

    unfold_groups = []
    for new_group, old_group in zip(new_groups, groups):
        if "__records" in new_group:
            unfold_groups.append(old_group)

    parallel_web_search_read = [
        grequests.post(
            get_url(model, "web_search_read"),
            json=web_search_read_data(g),
            cookies=COOKIES,
        )
        for g in unfold_groups
    ]

    start = time_ns()
    results = grequests.map(parallel_web_search_read, size=MAX_PARALLEL_REQUEST)
    delay_user += time_ns() - start

    for group, res in zip(unfold_groups, results):
        group["__records"] = res.json()["result"]["records"]
        worker_time += res.elapsed.total_seconds() * 1000

    return groups, (delay_user / 1_000_000, worker_time)


def new_way(method, scenario):
    model = scenario["model"]
    json_data = get_default_json_data(model, method)
    json_data["params"]["kwargs"].update(
        {
            "domain": scenario["domain"],
            "groupby": scenario["groupby"],
            "aggregates": scenario["aggregates"],
            "unfold_read_specification": scenario["read_specification"],
            "unfold_read_default_limit": scenario["unfold_read_default_limit"],
            "auto_unfold": True,
        }
    )
    start = time_ns()
    res = requests.post(get_url(model, method), json=json_data, cookies=COOKIES)
    delay_user = time_ns() - start
    return res.json()["result"]["groups"], (
        delay_user / 1_000_000,
        res.elapsed.total_seconds() * 1000,
    )


NB_TEST = 8  # min 4


def time_test(method):
    res_user_time = []
    res_worker_time = []
    for _ in range(NB_TEST):
        _, [delay_user, delay_worker] = method()
        res_user_time.append(delay_user)
        res_worker_time.append(delay_worker)

    return sorted(res_user_time)[:-(NB_TEST // 2)], sorted(res_worker_time)[:-(NB_TEST // 2)]


if __name__ == "__main__":
    # Warmup
    NB_WARMUP = 1
    for i in range(NB_WARMUP):
        print(f"Warmup worker {i}/{NB_WARMUP}")

        for scenario in SCENARIOS:
            if not scenario:
                continue
            new_groups, _ = new_way("web_read_group_unity_trivial", scenario)
            new_groups, _ = new_way("web_read_group_unity_union_all_simple", scenario)
            new_groups, _ = new_way("web_read_group_unity_cte", scenario)
            old_groups, _ = old_way(scenario, new_groups, with_issue=True)
            old_groups, _ = old_way(scenario, new_groups, with_issue=False)

            # assert (
            #     old_groups == new_groups
            # ), f"web_read_group_unity fail assert: {scenario['name']}\n{old_groups}\nVS\n{new_groups}"

            if i == 0:
                print(
                    f"\t- {scenario['name']} : {sum(1 for group in new_groups if '__records' in group)} groups open"
                )

    print("Launching test")
    for scenario in SCENARIOS:
        if not scenario:
            continue
        new_groups, _ = new_way("web_read_group_unity_trivial", scenario)
        to_test = [
            ("Old", partial(old_way, scenario, new_groups, with_issue=True)),
            ("Old (Fixed)", partial(old_way, scenario, new_groups, with_issue=False)),
            ("Uni Trivial", partial(new_way, "web_read_group_unity_trivial", scenario)),
            ("Uni Union All", partial(new_way, "web_read_group_unity_union_all_simple", scenario)),
            ("Uni CTE", partial(new_way, "web_read_group_unity_cte", scenario)),
        ]
        print(f"For {scenario['name']}:")
        for name, method in to_test:
            user_times, worker_times = time_test(method)

            avg_user_times = fmean(user_times)
            stdev_user_times = stdev(user_times)
            avg_worker_times = fmean(worker_times)
            stdev_worker_times = stdev(worker_times)

            print(
                f"\t{name:<15}> User time: {avg_user_times:10.3f} +- {stdev_user_times:8.3f} ms | Worker time: {avg_worker_times:10.3f} +- {stdev_worker_times:8.3f} ms"
            )
