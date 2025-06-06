from time import time_ns
import grequests
import requests
import itertools
from functools import partial
from statistics import fmean, stdev

# Branch for test:

READ_SPEC_CRM = {
    
}

READ_SPEC_TASK = {
    
}

READ_SPEC_PROJECT = {
    
}

BASE_URL = "https://127.0.0.1/"
COOKIES = {
    "session_id": "",
}

SCENARIO = [
    # ------- crm.lead
    # Kanban: Open CRM - No filter - all open lead are loaded
    {

    },
    # Kanban: Open CRM - FZilter: Creation Date = 2025 - Groupby month
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

def get_default_json_data(model, method, domain):
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
                "domain": domain,
            },
        },
    }


def old_way(scenario, with_issue=True):
    (
        model,
        domain,
        groupby,
        aggregates,
        read_specification,
        search_limit,
        search_order,
    ) = scenario
    json_data = get_default_json_data(model, "web_read_group", domain)
    json_data["params"]["kwargs"]["fields"] = aggregates
    json_data["params"]["kwargs"]["groupby"] = groupby

    url = get_url(model, "web_read_group")

    start = time_ns()
    res = requests.post(url, json=json_data, cookies=COOKIES)
    delay = time_ns() - start
    groups = res.json()["result"]["groups"]

    def web_search_read_data(group):
        data = get_default_json_data(model, "web_search_read", [])
        data["params"]["kwargs"]["domain"] = group["__domain"]
        data["params"]["kwargs"]["specification"] = read_specification
        data["params"]["kwargs"]["count_limit"] = 10001 if with_issue else search_limit
        data["params"]["kwargs"]["limit"] = search_limit
        data["params"]["kwargs"]["order"] = search_order
        return data

    def is_unfold(group):
        return (not group.get("__fold", False)) and (group[f"{groupby[0]}_count"] != 0)

    unfold_groups = list(itertools.islice(filter(is_unfold, groups), 10))

    parallel_web_search_read = [
        grequests.post(
            get_url(model, "web_search_read"),
            json=web_search_read_data(g),
            cookies=cookies,
        )
        for g in unfold_groups
    ]

    # TODO: should be 5 because of the read_group_progress_bar ?
    start = time_ns()
    results = grequests.map(parallel_web_search_read, size=6)
    delay += time_ns() - start

    for group, res in zip(unfold_groups, results):
        group["__records"] = res.json()["result"]["records"]

    return groups, delay / 1_000_000


def new_way(method, scenario):
    (
        model,
        domain,
        groupby,
        aggregates,
        read_specification,
        search_limit,
        search_order,
    ) = scenario
    json_data = get_default_json_data(model, method, domain)
    json_data["params"]["kwargs"]["aggregates"] = aggregates
    json_data["params"]["kwargs"]["groupby"] = groupby
    json_data["params"]["kwargs"]["read_specification"] = read_specification
    json_data["params"]["kwargs"]["search_limit"] = search_limit
    json_data["params"]["kwargs"]["search_order"] = search_order
    start = time_ns()
    res = requests.post(get_url(model, method), json=json_data, cookies=cookies)
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
    # model, domain, groupby, aggregates, read_specification, limit_search, order_search
    scenarios = [
        (  # When you open Help project (fixed aggregates)
            "project.task",
            [
                "&",
                "&",
                ["project_id", "=", 49],
                ["display_in_project", "=", True],
                [
                    "state",
                    "in",
                    [
                        "01_in_progress",
                        "02_changes_requested",
                        "03_approved",
                        "04_waiting_normal",
                    ],
                ],
            ],
            ["stage_id"],
            ["__count"],
            project_spec,
            20,
            None,
        ),
        (  # When you open CRM -> search 'test' (fixed aggregates)
            "crm.lead",
            [
                "&",
                ["type", "=", "opportunity"],
                "|",
                "|",
                "|",
                "|",
                ["partner_id", "ilike", "test"],
                ["partner_name", "ilike", "test"],
                ["email_from", "ilike", "test"],
                ["name", "ilike", "test"],
                ["contact_name", "ilike", "test"],
            ],
            ["stage_id"],
            ["__count", "expected_revenue:sum", "recurring_revenue_monthly:sum"],
            spec_lead,
            40,
            None,
        ),
        (  # When you open CRM -> search 'infinity' included archived
            "crm.lead",
            [
                "&",
                ["type", "=", "opportunity"],
                "&",
                "|",
                "|",
                "|",
                "|",
                ["partner_id", "ilike", "infinity i"],
                ["partner_name", "ilike", "infinity i"],
                ["email_from", "ilike", "infinity i"],
                ["name", "ilike", "infinity i"],
                ["contact_name", "ilike", "infinity i"],
                ["active", "in", [True, False]],
            ],
            ["stage_id"],
            ["__count", "expected_revenue:sum", "recurring_revenue_monthly:sum"],
            spec_lead,
            40,
            None,
        ),
        (  # When you open CRM -> search 'Won t find anything' (fixed aggregates)
            "crm.lead",
            [
                "&",
                ["type", "=", "opportunity"],
                "|",
                "|",
                "|",
                "|",
                ["partner_id", "ilike", "Won t find anything"],
                ["partner_name", "ilike", "Won t find anything"],
                ["email_from", "ilike", "Won t find anything"],
                ["name", "ilike", "Won t find anything"],
                ["contact_name", "ilike", "Won t find anything"],
            ],
            ["stage_id"],
            ["__count", "expected_revenue:sum", "recurring_revenue_monthly:sum"],
            spec_lead,
            40,
            None,
        ),
        (  # When you open CRM -> groupby 'Sales Team' (fixed aggregates)
            "crm.lead",
            [["type", "=", "opportunity"]],
            ["team_id"],
            ["__count", "expected_revenue:sum", "recurring_revenue_monthly:sum"],
            spec_lead,
            40,
            None,
        ),
        (  # When you open CRM -> custom groupby language (fixed aggregates)
            "crm.lead",
            [["type", "=", "opportunity"]],
            ["lang_id"],
            ["__count", "expected_revenue:sum", "recurring_revenue_monthly:sum"],
            spec_lead,
            40,
            None,
        ),
        (  # Open Project -> Groupby Status (fixed aggregates)
            "project.project",
            [["is_internal_project", "=", False]],
            ["last_update_status"],
            ["__count"],
            project_project_spec,
            80,
            "is_favorite DESC, sequence ASC, name ASC, id ASC",
        ),
        # TODO: with date ??? But _records_by_group_union_all_cte doesn't work
    ]

    scenario_names = [
        # "Open CRM",
        "Open CRM",
        "Open ORM project",
        "Open Help project",
        "Open CRM -> search 'test'",
        "Open CRM -> search 'infinity' included archived",
        "Open CRM -> search 'Won t find anything'",
        "Open CRM -> groupby 'Sales Team'",
        "Open CRM -> custom groupby language",
        "Open Project -> Groupby Status",
    ]

    # Warmup
    NB_WARMUP = 1
    for i in range(NB_WARMUP):
        print(f"Warmup worker {i}/{NB_WARMUP} :")
        for scenario, name_s in zip(scenarios, scenario_names):
            old_groups, _ = old_way(scenario, with_issue=True)
            old_groups, _ = old_way(scenario, with_issue=False)

            new_groups, _ = new_way("web_read_group_unity_naive_search", scenario)
            assert (
                old_groups == new_groups
            ), f"web_read_group_unity_naive_search fail assert: {name_s}\n{old_groups}\nVS\n{new_groups}"

            # new_groups, _ = new_way("web_read_group_unity_union_all", scenario)
            # assert (
            #     old_groups == new_groups
            # ), f"web_read_group_unity_union_all fail assert: {name_s}\n{old_groups}\nVS\n{new_groups}"

            new_groups, _ = new_way("web_read_group_unity_union_all_cte", scenario)
            assert (
                old_groups == new_groups
            ), f"web_read_group_unity_union_all_cte fail assert: {name_s}\n{old_groups}\nVS\n{new_groups}"
            if i == 0:
                print(
                    f"\t- {name_s} : {sum(1 for group in new_groups if '__records' in group)} groups open"
                )

    print("Launching test")
    for scenario, name_s in zip(scenarios, scenario_names):
        to_test = [
            (
                "union_all_cte",
                partial(new_way, "web_read_group_unity_union_all_cte", scenario),
            ),
            (
                "naive_search",
                partial(new_way, "web_read_group_unity_naive_search", scenario),
            ),
            ("Old way (Fixed)", partial(old_way, scenario, with_issue=False)),
            ("Old way", partial(old_way, scenario, with_issue=True)),
            # ('union_all', partial(new_way, "web_read_group_unity_union_all", scenario)),
        ]
        print(f"For {name_s!r}:")
        for name, method in to_test:
            res = time_test(method)

            avg_res = fmean(res)
            stdev_res = stdev(res)
            max_res = max(res)
            min_res = min(res)

            print(
                f"\t- {name}: {avg_res:.3f} +- {stdev_res:.3f} ms / min={min_res:.3f}, max={max_res:.3f} ms"
            )
