from time import time_ns
import grequests
import requests
import itertools
from functools import partial
from statistics import fmean, stdev

# Branch for test:

READ_SPEC_CRM = {
    "stage_id": {
        "fields": {
        "display_name": {}
        }
    },
    "probability": {},
    "active": {},
    "company_currency": {
        "fields": {
        "display_name": {}
        }
    },
    "recurring_revenue_monthly": {},
    "team_id": {
        "fields": {
        "display_name": {}
        }
    },
    "won_status": {},
    "color": {},
    "name": {},
    "expected_revenue": {},
    "partner_id": {
        "fields": {
        "display_name": {}
        }
    },
    "tag_ids": {
        "fields": {
        "display_name": {},
        "color": {}
        }
    },
    "lead_properties": {},
    "priority": {},
    "activity_ids": {
        "fields": {}
    },
    "activity_exception_decoration": {},
    "activity_exception_icon": {},
    "activity_state": {},
    "activity_summary": {},
    "activity_type_icon": {},
    "activity_type_id": {
        "fields": {
        "display_name": {}
        }
    },
    "user_id": {
        "fields": {
        "display_name": {}
        }
    }
}

READ_SPEC_TASK = {
    
}

READ_SPEC_PROJECT = {
    
}

BASE_URL = "http://127.0.0.1:8069"
COOKIES = {
    "session_id": "",
}
MAX_AUTO_UNFOLD = 10
MAX_PARALLEL_REQUEST = 6  # Max of chrome

SCENARIOS = [
    # ------- crm.lead
    # Open CRM - Kanban - Filter: default (none) - all open lead are loaded
    {
        'name': "Open CRM - Kanban - Filter: default (none) - all open lead are loaded",
        'model': 'crm.lead',
        'domain': [],
        'groupby': ["create_date:month"],
        'aggregates': ["probability:avg", "recurring_revenue_monthly:sum", "color:sum", "expected_revenue:sum"],
        'read_specification': READ_SPEC_CRM,
        'auto_unfold': True,
        'unfold_read_default_limit': 80,
    },
    # Open CRM - Kanban - Filter: Creation Date = 2025 - Groupby month
    {

    },
    # Open CRM - Kanban - Filter: default (none) - groupby lang_code (related field)
    {

    },
    # Open CRM - Kanban - Filter : search 'test' (default groupby)
    {

    },
    # Open CRM - Kanban - Filter: included active - groupby active
    {

    },
    # Open CRM - List view - with multiple group loaded, TODO
    {

    },
    # Open CRM - List view - with multiple group loaded, TODO
    {

    },

    # ------- project.task
    # Kanban: Open Framework Python project - No filters
    {

    },
    # Kanban: Open Help project - No filter
    {

    },
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
                },
            },
        },
    }

def old_way(scenario, new_groups, with_issue=True):
    model = scenario['model']
    url = get_url(model, "web_read_group")
    json_data = get_default_json_data(model, "web_read_group")

    json_data["params"]["kwargs"].update({
        'domain': scenario['domain'],
        'groupby': scenario['groupby'],
        'aggregates': scenario['aggregates'],
    })

    start = time_ns()
    res = requests.post(url, json=json_data, cookies=COOKIES)
    delay = time_ns() - start
    groups = res.json()["result"]["groups"]

    def web_search_read_data(group):
        data = get_default_json_data(model, "web_search_read")
        data["params"]["kwargs"].update({
            'domain': scenario['domain'] + group['__extra_domain'],
            'specification': scenario['read_specification'],
            'count_limit': 10001 if with_issue else scenario['unfold_read_default_limit'],
            'limit': scenario['unfold_read_default_limit'],
        })
        return data

    unfold_groups = []
    for new_group, old_group in zip(new_groups, groups):
        if '__records' in new_group:
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
    delay += time_ns() - start

    for group, res in zip(unfold_groups, results):
        group["__records"] = res.json()["result"]["records"]

    return groups, delay / 1_000_000


def new_way(method, scenario):
    model = scenario['model']
    json_data = get_default_json_data(model, method)
    json_data["params"]["kwargs"].update({
        'domain': scenario['domain'],
        'groupby': scenario['groupby'],
        'aggregates': scenario['aggregates'],
        'unfold_read_specification': scenario['read_specification'],
        'unfold_read_default_limit': scenario['unfold_read_default_limit'],
        'auto_unfold': True,
    })
    start = time_ns()
    res = requests.post(get_url(model, method), json=json_data, cookies=COOKIES)
    delay = time_ns() - start
    return res.json()["result"]["groups"], (delay / 1_000_000)


NB_TEST = 10

def time_test(method):
    res = []
    for _ in range(NB_TEST):
        _, delay = method()
        res.append(delay)

    res.sort()
    return res[2:-2]  # Remove outlier


if __name__ == "__main__":
    # Warmup
    NB_WARMUP = 2
    for i in range(NB_WARMUP):
        print(f"Warmup worker {i}/{NB_WARMUP} :")

        for scenario in SCENARIOS:
            if not scenario:
                continue
            new_groups, _ = new_way("web_read_group_unity", scenario)
            new_groups, _ = new_way("web_read_group_unity", scenario)
            new_groups, _ = new_way("web_read_group_unity", scenario)
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
        new_groups, _ = new_way("web_read_group_unity", scenario)
        to_test = [
            (
                "web_read_group_unity",
                partial(new_way, "web_read_group_unity", scenario),
            ),
            ("Old way (Fixed)", partial(old_way, scenario, new_groups, with_issue=False)),
            ("Old way", partial(old_way, scenario, new_groups, with_issue=True)),
        ]
        print(f"For {scenario['name']}:")
        for name, method in to_test:
            res = time_test(method)

            avg_res = fmean(res)
            stdev_res = stdev(res)
            max_res = max(res)
            min_res = min(res)

            print(
                f"\t- {name}: {avg_res:.3f} +- {stdev_res:.3f} ms / min={min_res:.3f}, max={max_res:.3f} ms"
            )
