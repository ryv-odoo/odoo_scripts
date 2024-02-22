from time import time_ns
import grequests
import requests
import itertools
from functools import partial
from statistics import fmean, stdev


# Branch: saas-17.1-web-read-group-unity-to-test-prod-ryv

spec_lead = {
    "stage_id": {"fields": {"display_name": {}}},
    "probability": {},
    "color": {},
    "priority": {},
    "expected_revenue": {},
    "kanban_state": {},
    "activity_date_deadline": {},
    "user_id": {"fields": {"display_name": {}}},
    "partner_assigned_id": {"fields": {"display_name": {}}},
    "partner_id": {"fields": {"display_name": {}}},
    "activity_summary": {},
    "active": {},
    "company_currency": {"fields": {"display_name": {}}},
    "activity_state": {},
    "activity_ids": {"fields": {}},
    "recurring_revenue_monthly": {},
    "team_id": {"fields": {"display_name": {}}},
    "name": {},
    "recurring_revenue": {},
    "recurring_plan": {"fields": {"display_name": {}}},
    "tag_ids": {"fields": {"display_name": {}, "color": {}}},
    "lead_properties": {},
    "activity_exception_decoration": {},
    "activity_exception_icon": {},
    "activity_type_icon": {},
    "activity_type_id": {"fields": {"display_name": {}}},
    "phone": {},
    "mobile": {},
    "has_call_in_queue": {},
}

project_spec = {
    "color": {},
    "priority": {},
    "stage_id": {"fields": {"display_name": {}}},
    "user_ids": {"fields": {"display_name": {}}, "context": {"active_test": False}},
    "partner_id": {"fields": {"display_name": {}}},
    "sequence": {},
    "displayed_image_id": {"fields": {"display_name": {}}},
    "active": {},
    "activity_ids": {"fields": {}},
    "activity_state": {},
    "rating_count": {},
    "rating_avg": {},
    "rating_active": {},
    "has_late_and_unreached_milestone": {},
    "allow_milestones": {},
    "state": {},
    "company_id": {"fields": {"display_name": {}}},
    "recurrence_id": {"fields": {"display_name": {}}},
    "subtask_count": {},
    "closed_subtask_count": {},
    "progress": {},
    "remaining_hours": {},
    "allocated_hours": {},
    "allow_timesheets": {},
    "encode_uom_in_days": {},
    "x_virtual_remaining": {},
    "project_id": {"fields": {"display_name": {}}},
    "name": {},
    "parent_id": {"fields": {"display_name": {}}},
    "milestone_id": {"fields": {"display_name": {}}},
    "tag_ids": {"fields": {"display_name": {}, "color": {}}},
    "date_deadline": {},
    "planned_date_begin": {},
    "task_properties": {},
    "activity_exception_decoration": {},
    "activity_exception_icon": {},
    "activity_summary": {},
    "activity_type_icon": {},
    "activity_type_id": {"fields": {"display_name": {}}},
    "display_timesheet_timer": {},
    "timer_start": {},
    "timer_pause": {},
}

project_project_spec = {
    "display_name": {},
    "partner_id": {"fields": {"display_name": {}}},
    "allow_timesheets": {},
    "allow_billable": {},
    "warning_employee_rate": {},
    "sale_order_id": {"fields": {}},
    "pricing_type": {},
    "remaining_hours": {},
    "encode_uom_in_days": {},
    "allocated_hours": {},
    "color": {},
    "task_count": {},
    "closed_task_count": {},
    "open_task_count": {},
    "milestone_count_reached": {},
    "milestone_count": {},
    "allow_milestones": {},
    "label_tasks": {},
    "alias_email": {},
    "is_favorite": {},
    "rating_count": {},
    "rating_avg": {},
    "rating_status": {},
    "rating_active": {},
    "analytic_account_id": {"fields": {"display_name": {}}},
    "date": {},
    "privacy_visibility": {},
    "last_update_color": {},
    "last_update_status": {},
    "tag_ids": {"fields": {"display_name": {}, "color": {}}},
    "sequence": {},
    "use_documents": {},
    "date_start": {},
    "total_planned_amount": {},
    "total_budget_progress": {},
    "activity_ids": {"fields": {}},
    "activity_exception_decoration": {},
    "activity_exception_icon": {},
    "activity_state": {},
    "activity_summary": {},
    "activity_type_icon": {},
    "activity_type_id": {"fields": {"display_name": {}}},
    "user_id": {"fields": {"display_name": {}}},
    "display_planning_timesheet_analysis": {},
    "id": {},
}

cookies = {
    "session_id": "",
}
base_url = "https://127.0.0.1/"


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


def get_url(model, method):
    return f"{base_url}/web/dataset/call_kw/RYV/{model}/{method}"


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
    res = requests.post(url, json=json_data, cookies=cookies)
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
        # (  # When you open crm
        #     "crm.lead",
        #     [["type", "=", "opportunity"]],
        #     ["stage_id"],
        #     # I remove "probability:avg" because it is not dertermistic
        #     ["__count", "color:sum", "expected_revenue:sum", "recurring_revenue_monthly:sum"],
        #     spec_lead,
        #     40,
        #     None,
        # ),
        (  # When you open crm (fixed aggregates)
            "crm.lead",
            [["type", "=", "opportunity"]],
            ["stage_id"],
            ["__count", "expected_revenue:sum", "recurring_revenue_monthly:sum"],
            spec_lead,
            40,
            None,
        ),
        (  # When you open Orm project (fixed aggregates)
            "project.task",
            [
                "&",
                "&",
                ["project_id", "=", 1364],
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

# Warmup worker 0/1 :
#         - Open CRM : 10 groups open
#         - Open ORM project : 5 groups open
#         - Open Help project : 5 groups open
#         - Open CRM -> search 'test' : 8 groups open
#         - Open CRM -> search 'infinity' included archived : 4 groups open
#         - Open CRM -> search 'Won t find anything' : 0 groups open
#         - Open CRM -> groupby 'Sales Team' : 10 groups open
#         - Open CRM -> custom groupby language : 10 groups open
#         - Open Project -> Groupby Status : 6 groups open
# Launching test
# For 'Open CRM':
#         - union_all_cte: 1041.938 +- 5.253 ms / min=1035.856, max=1049.793 ms
#         - naive_search: 1013.589 +- 7.694 ms / min=1007.152, max=1024.794 ms
#         - Old way (Fixed): 1303.302 +- 30.351 ms / min=1267.920, max=1343.040 ms
#         - Old way: 1353.042 +- 32.072 ms / min=1291.366, max=1375.361 ms
# For 'Open ORM project':
#         - union_all_cte: 195.178 +- 3.781 ms / min=190.861, max=200.268 ms
#         - naive_search: 206.428 +- 5.492 ms / min=199.192, max=213.320 ms
#         - Old way (Fixed): 435.045 +- 13.020 ms / min=412.178, max=450.954 ms
#         - Old way: 425.152 +- 13.465 ms / min=410.615, max=447.192 ms
# For 'Open Help project':
#         - union_all_cte: 274.160 +- 3.729 ms / min=268.541, max=278.962 ms
#         - naive_search: 284.665 +- 7.156 ms / min=274.192, max=292.445 ms
#         - Old way (Fixed): 532.714 +- 12.108 ms / min=510.334, max=542.942 ms
#         - Old way: 527.046 +- 10.869 ms / min=509.606, max=537.778 ms
# For "Open CRM -> search 'test'":
#         - union_all_cte: 2736.100 +- 7.051 ms / min=2725.346, max=2743.721 ms
#         - naive_search: 3996.510 +- 13.616 ms / min=3971.167, max=4006.496 ms
#         - Old way (Fixed): 2655.541 +- 21.633 ms / min=2629.082, max=2692.341 ms
#         - Old way: 3439.990 +- 21.272 ms / min=3403.804, max=3459.134 ms
# For "Open CRM -> search 'infinity' included archived":
#         - union_all_cte: 32807.011 +- 134.880 ms / min=32652.577, max=32933.491 ms
#         - naive_search: 36863.349 +- 267.655 ms / min=36678.835, max=37360.471 ms
#         - Old way (Fixed): 34905.079 +- 92.901 ms / min=34792.019, max=35010.290 ms
#         - Old way: 49734.720 +- 99.857 ms / min=49605.354, max=49867.933 ms
# For "Open CRM -> search 'Won t find anything'":
#         - union_all_cte: 1685.414 +- 28.648 ms / min=1647.706, max=1735.588 ms
#         - naive_search: 1690.935 +- 29.609 ms / min=1655.007, max=1728.857 ms
#         - Old way (Fixed): 1718.638 +- 29.525 ms / min=1659.859, max=1737.698 ms
#         - Old way: 1706.435 +- 42.028 ms / min=1641.071, max=1747.581 ms
# For "Open CRM -> groupby 'Sales Team'":
#         - union_all_cte: 811.708 +- 6.287 ms / min=805.277, max=821.081 ms
#         - naive_search: 1285.122 +- 33.977 ms / min=1238.380, max=1318.665 ms
#         - Old way (Fixed): 1282.019 +- 30.112 ms / min=1237.886, max=1312.708 ms
#         - Old way: 1381.347 +- 62.200 ms / min=1308.049, max=1456.810 ms
# For 'Open CRM -> custom groupby language':
#         - union_all_cte: 1313.880 +- 28.485 ms / min=1270.084, max=1352.300 ms
#         - naive_search: 3348.710 +- 34.964 ms / min=3284.476, max=3375.463 ms
#         - Old way (Fixed): 1882.669 +- 41.552 ms / min=1834.666, max=1943.447 ms
#         - Old way: 2563.283 +- 55.244 ms / min=2458.960, max=2610.958 ms
# For 'Open Project -> Groupby Status':
#         - union_all_cte: 2191.834 +- 10.239 ms / min=2177.484, max=2204.447 ms
#         - naive_search: 2192.693 +- 3.795 ms / min=2187.576, max=2198.750 ms
#         - Old way (Fixed): 2038.496 +- 3.590 ms / min=2034.822, max=2043.147 ms
#         - Old way: 2040.202 +- 25.064 ms / min=2006.974, max=2079.213 ms

# LOG SERVER (round-trip +- 0.025 sec (from browser with very almost empty request))
# 2024-02-23 11:54:38,464 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.279 0.004
# 2024-02-23 11:54:38,805 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.007 0.020
# 2024-02-23 11:54:38,814 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.007 0.024
# 2024-02-23 11:54:38,816 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.008 0.025
# 2024-02-23 11:54:38,818 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.025
# 2024-02-23 11:54:38,822 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.013 0.027
# 2024-02-23 11:54:38,837 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.008 0.023
# 2024-02-23 11:54:39,015 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.008 0.026
# 2024-02-23 11:54:39,314 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.292 0.031
# 2024-02-23 11:54:39,371 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.253 0.036
# 2024-02-23 11:54:39,394 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.291 0.032
# 2024-02-23 11:54:39,801 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.281 0.004
# 2024-02-23 11:54:40,253 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.024
# 2024-02-23 11:54:40,256 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.007 0.020
# 2024-02-23 11:54:40,258 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.032
# 2024-02-23 11:54:40,269 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.010 0.031
# 2024-02-23 11:54:40,274 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.037
# 2024-02-23 11:54:40,279 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.005 0.019
# 2024-02-23 11:54:40,524 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.012 0.032
# 2024-02-23 11:54:40,645 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.118 0.051
# 2024-02-23 11:54:40,672 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.174 0.030
# 2024-02-23 11:54:40,771 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.267 0.028
# 2024-02-23 11:54:41,741 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.739 0.112
# 2024-02-23 11:54:42,847 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.765 0.182
# 2024-02-23 11:54:43,027 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.001 0.004
# 2024-02-23 11:54:43,297 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.005 0.013
# 2024-02-23 11:54:43,298 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.006 0.014
# 2024-02-23 11:54:43,308 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.007 0.020
# 2024-02-23 11:54:43,308 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.006 0.020
# 2024-02-23 11:54:43,319 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.008 0.022
# 2024-02-23 11:54:43,429 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.001 0.004
# 2024-02-23 11:54:43,706 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.005 0.012
# 2024-02-23 11:54:43,706 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.006 0.014
# 2024-02-23 11:54:43,716 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.006 0.016
# 2024-02-23 11:54:43,718 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.027
# 2024-02-23 11:54:43,719 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.027
# 2024-02-23 11:54:43,894 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.010 0.028
# 2024-02-23 11:54:44,040 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.009 0.026
# 2024-02-23 11:54:44,269 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.065 0.004
# 2024-02-23 11:54:44,556 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.012 0.023
# 2024-02-23 11:54:44,562 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.014 0.030
# 2024-02-23 11:54:44,569 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.015 0.035
# 2024-02-23 11:54:44,578 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.023 0.034
# 2024-02-23 11:54:44,580 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.025 0.026
# 2024-02-23 11:54:44,772 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.065 0.004
# 2024-02-23 11:54:45,079 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.011 0.024
# 2024-02-23 11:54:45,081 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.011 0.024
# 2024-02-23 11:54:45,082 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.018 0.023
# 2024-02-23 11:54:45,084 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.017 0.024
# 2024-02-23 11:54:45,089 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.009 0.020
# 2024-02-23 11:54:45,338 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.097 0.051
# 2024-02-23 11:54:45,615 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.096 0.049
# 2024-02-23 11:54:47,025 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.242 0.004
# 2024-02-23 11:54:47,538 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.140 0.015
# 2024-02-23 11:54:47,659 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.107 0.014
# 2024-02-23 11:54:47,683 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.258 0.044
# 2024-02-23 11:54:47,820 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.132 0.023
# 2024-02-23 11:54:48,031 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.614 0.033
# 2024-02-23 11:54:48,174 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.725 0.061
# 2024-02-23 11:54:48,891 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.107 0.028
# 2024-02-23 11:54:49,126 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.713 0.028
# 2024-02-23 11:54:50,500 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.253 0.004
# 2024-02-23 11:54:50,943 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.118 0.020
# 2024-02-23 11:54:50,943 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.116 0.020
# 2024-02-23 11:54:51,096 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.259 0.028
# 2024-02-23 11:54:51,132 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.295 0.033
# 2024-02-23 11:54:51,264 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.132 0.020
# 2024-02-23 11:54:51,335 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.357 0.033
# 2024-02-23 11:54:51,690 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.562 0.027
# 2024-02-23 11:54:51,750 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.921 0.026
# 2024-02-23 11:54:54,353 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 33.495 0.033
# 2024-02-23 11:54:55,757 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.788 0.092
# 2024-02-23 11:54:58,484 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.500 0.092
# 2024-02-23 11:55:15,327 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.694 0.011
# 2024-02-23 11:55:15,986 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.393 0.014
# 2024-02-23 11:55:16,119 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.524 0.017
# 2024-02-23 11:55:16,909 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.314 0.018
# 2024-02-23 11:55:48,292 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 32.674 0.026
# 2024-02-23 11:56:04,817 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.387 0.011
# 2024-02-23 11:56:05,464 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.391 0.013
# 2024-02-23 11:56:05,603 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.529 0.015
# 2024-02-23 11:56:06,408 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.332 0.025
# 2024-02-23 11:56:23,110 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 18.042 0.030
# 2024-02-23 11:57:00,447 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 37.157 0.043
# 2024-02-23 11:57:33,447 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.862 0.036
# 2024-02-23 11:57:35,081 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.527 0.010
# 2024-02-23 11:57:36,750 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.538 0.009
# 2024-02-23 11:57:38,397 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.542 0.010
# 2024-02-23 11:57:40,044 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.543 0.011
# 2024-02-23 11:57:40,442 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.280 0.010
# 2024-02-23 11:57:40,763 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.009 0.031
# 2024-02-23 11:57:40,769 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.009 0.028
# 2024-02-23 11:57:40,771 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.012 0.037
# 2024-02-23 11:57:40,893 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.140 0.028
# 2024-02-23 11:57:40,922 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.025 0.026
# 2024-02-23 11:57:40,965 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.203 0.036
# 2024-02-23 11:57:41,032 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.018 0.041
# 2024-02-23 11:57:41,230 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.137 0.048
# 2024-02-23 11:57:41,273 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.513 0.034
# 2024-02-23 11:57:41,405 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.397 0.027
# 2024-02-23 11:57:41,832 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.281 0.010
# 2024-02-23 11:57:42,228 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.027
# 2024-02-23 11:57:42,231 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.008 0.028
# 2024-02-23 11:57:42,234 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.012 0.035
# 2024-02-23 11:57:42,298 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.082 0.029
# 2024-02-23 11:57:42,332 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.107 0.031
# 2024-02-23 11:57:42,443 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.024
# 2024-02-23 11:57:42,444 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.014 0.027
# 2024-02-23 11:57:42,508 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.284 0.035
# 2024-02-23 11:57:42,593 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.077 0.028
# 2024-02-23 11:57:42,699 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.261 0.027
# 2024-02-23 11:57:43,910 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.970 0.123
# 2024-02-23 11:57:44,769 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.549 0.121
# 2024-02-23 11:57:45,219 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.285 0.010
# 2024-02-23 11:57:46,075 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.523 0.021
# 2024-02-23 11:57:46,226 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.666 0.031
# 2024-02-23 11:57:46,343 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.757 0.062
# 2024-02-23 11:57:46,372 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.813 0.032
# 2024-02-23 11:57:46,725 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.485 0.033
# 2024-02-23 11:57:46,951 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.377 0.051
# 2024-02-23 11:57:47,008 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.652 0.034
# 2024-02-23 11:57:47,016 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.514 0.032
# 2024-02-23 11:57:47,064 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.503 0.033
# 2024-02-23 11:57:47,469 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.919 0.028
# 2024-02-23 11:57:47,960 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.280 0.009
# 2024-02-23 11:57:48,599 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.352 0.033
# 2024-02-23 11:57:48,650 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.411 0.024
# 2024-02-23 11:57:48,675 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.426 0.033
# 2024-02-23 11:57:48,686 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.436 0.036
# 2024-02-23 11:57:48,989 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.692 0.037
# 2024-02-23 11:57:49,013 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.693 0.049
# 2024-02-23 11:57:49,135 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.390 0.032
# 2024-02-23 11:57:49,265 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.380 0.032
# 2024-02-23 11:57:49,270 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.386 0.029
# 2024-02-23 11:57:49,384 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.490 0.031
# 2024-02-23 11:57:52,643 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 2.983 0.141
# 2024-02-23 11:57:53,906 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.976 0.138
# 2024-02-23 11:57:54,116 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 11:57:54,488 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.030 0.038
# 2024-02-23 11:57:54,525 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.059 0.048
# 2024-02-23 11:57:54,567 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.066 0.086
# 2024-02-23 11:57:54,570 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.071 0.078
# 2024-02-23 11:57:54,575 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.084 0.065
# 2024-02-23 11:57:55,983 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.423 0.144
# 2024-02-23 11:57:56,115 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.010 0.008
# 2024-02-23 11:57:56,485 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.033 0.045
# 2024-02-23 11:57:56,513 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.057 0.049
# 2024-02-23 11:57:56,559 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.080 0.070
# 2024-02-23 11:57:56,561 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.072 0.076
# 2024-02-23 11:57:56,564 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.056 0.090
# 2024-02-23 11:57:58,000 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.446 0.142
# 2024-02-23 11:58:00,169 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.795 0.240
# 2024-02-23 11:58:02,357 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.806 0.238
# 2024-02-23 11:58:03,406 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.781 0.113
# 2024-02-23 11:58:04,462 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.781 0.113
# 2024-02-23 11:58:05,514 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.780 0.113
# 2024-02-23 11:58:06,567 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.789 0.112
# 2024-02-23 11:58:07,611 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.788 0.114
# 2024-02-23 11:58:08,650 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.788 0.114
# 2024-02-23 11:58:09,708 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.788 0.114
# 2024-02-23 11:58:10,773 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.789 0.115
# 2024-02-23 11:58:11,827 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.786 0.115
# 2024-02-23 11:58:12,875 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.788 0.115
# 2024-02-23 11:58:13,903 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.747 0.118
# 2024-02-23 11:58:14,917 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.756 0.118
# 2024-02-23 11:58:15,927 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.735 0.116
# 2024-02-23 11:58:16,962 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.753 0.116
# 2024-02-23 11:58:17,985 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.744 0.118
# 2024-02-23 11:58:18,988 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.742 0.116
# 2024-02-23 11:58:20,085 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.755 0.116
# 2024-02-23 11:58:21,134 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.746 0.117
# 2024-02-23 11:58:22,227 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.748 0.116
# 2024-02-23 11:58:23,260 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.748 0.116
# 2024-02-23 11:58:23,758 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.288 0.009
# 2024-02-23 11:58:24,124 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.007 0.027
# 2024-02-23 11:58:24,124 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.023
# 2024-02-23 11:58:24,130 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.031
# 2024-02-23 11:58:24,132 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.007 0.027
# 2024-02-23 11:58:24,145 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.011 0.044
# 2024-02-23 11:58:24,145 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.012 0.045
# 2024-02-23 11:58:24,387 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.044
# 2024-02-23 11:58:24,519 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.126 0.053
# 2024-02-23 11:58:24,543 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.175 0.039
# 2024-02-23 11:58:24,644 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.282 0.034
# 2024-02-23 11:58:25,072 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.294 0.010
# 2024-02-23 11:58:25,411 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.010 0.026
# 2024-02-23 11:58:25,417 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.030
# 2024-02-23 11:58:25,420 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.011 0.031
# 2024-02-23 11:58:25,420 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.012 0.032
# 2024-02-23 11:58:25,424 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.008 0.035
# 2024-02-23 11:58:25,428 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.036
# 2024-02-23 11:58:25,775 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.016 0.054
# 2024-02-23 11:58:25,880 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.137 0.036
# 2024-02-23 11:58:25,935 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.169 0.048
# 2024-02-23 11:58:26,016 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.275 0.033
# 2024-02-23 11:58:26,457 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.295 0.010
# 2024-02-23 11:58:26,878 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.006 0.023
# 2024-02-23 11:58:26,881 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.011 0.034
# 2024-02-23 11:58:26,884 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.007 0.032
# 2024-02-23 11:58:26,885 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.030
# 2024-02-23 11:58:26,888 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.015 0.039
# 2024-02-23 11:58:26,891 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.010 0.033
# 2024-02-23 11:58:27,105 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.018 0.051
# 2024-02-23 11:58:27,229 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.122 0.033
# 2024-02-23 11:58:27,265 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.161 0.030
# 2024-02-23 11:58:27,377 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.265 0.028
# 2024-02-23 11:58:27,806 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.287 0.009
# 2024-02-23 11:58:28,219 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.012 0.030
# 2024-02-23 11:58:28,221 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.012 0.032
# 2024-02-23 11:58:28,224 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.033
# 2024-02-23 11:58:28,227 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.007 0.039
# 2024-02-23 11:58:28,231 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.034
# 2024-02-23 11:58:28,232 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.010 0.043
# 2024-02-23 11:58:28,480 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.011 0.032
# 2024-02-23 11:58:28,599 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.135 0.037
# 2024-02-23 11:58:28,635 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.175 0.035
# 2024-02-23 11:58:28,727 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.269 0.033
# 2024-02-23 11:58:29,146 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.294 0.010
# 2024-02-23 11:58:29,485 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.007 0.023
# 2024-02-23 11:58:29,491 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.028
# 2024-02-23 11:58:29,499 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.006 0.034
# 2024-02-23 11:58:29,503 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.037
# 2024-02-23 11:58:29,505 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.010 0.035
# 2024-02-23 11:58:29,508 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.010 0.034
# 2024-02-23 11:58:29,794 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.013 0.032
# 2024-02-23 11:58:29,908 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.128 0.031
# 2024-02-23 11:58:29,921 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.177 0.037
# 2024-02-23 11:58:30,043 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.266 0.028
# 2024-02-23 11:58:30,480 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.295 0.010
# 2024-02-23 11:58:30,830 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.011 0.028
# 2024-02-23 11:58:30,835 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.007 0.037
# 2024-02-23 11:58:30,842 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.038
# 2024-02-23 11:58:30,848 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.023
# 2024-02-23 11:58:30,852 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.007 0.028
# 2024-02-23 11:58:30,859 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.007 0.032
# 2024-02-23 11:58:31,047 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.014 0.037
# 2024-02-23 11:58:31,225 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.139 0.031
# 2024-02-23 11:58:31,242 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.168 0.031
# 2024-02-23 11:58:31,305 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.275 0.033
# 2024-02-23 11:58:31,748 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.289 0.010
# 2024-02-23 11:58:32,063 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.010 0.028
# 2024-02-23 11:58:32,063 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.008 0.027
# 2024-02-23 11:58:32,071 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.012 0.035
# 2024-02-23 11:58:32,073 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.016 0.034
# 2024-02-23 11:58:32,073 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.029
# 2024-02-23 11:58:32,075 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.012 0.035
# 2024-02-23 11:58:32,328 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.017 0.041
# 2024-02-23 11:58:32,467 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.143 0.054
# 2024-02-23 11:58:32,486 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.179 0.035
# 2024-02-23 11:58:32,589 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.275 0.032
# 2024-02-23 11:58:33,026 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.289 0.010
# 2024-02-23 11:58:33,360 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.007 0.024
# 2024-02-23 11:58:33,362 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.006 0.021
# 2024-02-23 11:58:33,365 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.013 0.026
# 2024-02-23 11:58:33,365 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.012 0.031
# 2024-02-23 11:58:33,375 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.010 0.042
# 2024-02-23 11:58:33,378 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.011 0.042
# 2024-02-23 11:58:33,623 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.017 0.043
# 2024-02-23 11:58:33,755 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.152 0.040
# 2024-02-23 11:58:33,789 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.173 0.035
# 2024-02-23 11:58:33,887 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.286 0.036
# 2024-02-23 11:58:34,313 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.281 0.009
# 2024-02-23 11:58:34,657 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.011 0.032
# 2024-02-23 11:58:34,663 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.034
# 2024-02-23 11:58:34,665 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.007 0.040
# 2024-02-23 11:58:34,673 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.014 0.044
# 2024-02-23 11:58:34,673 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.013 0.044
# 2024-02-23 11:58:34,673 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.037
# 2024-02-23 11:58:34,889 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.016 0.044
# 2024-02-23 11:58:35,046 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.126 0.030
# 2024-02-23 11:58:35,058 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.172 0.045
# 2024-02-23 11:58:35,146 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.283 0.033
# 2024-02-23 11:58:35,593 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.296 0.010
# 2024-02-23 11:58:35,934 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.010 0.036
# 2024-02-23 11:58:35,935 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.024
# 2024-02-23 11:58:35,938 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.012 0.029
# 2024-02-23 11:58:35,939 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.011 0.033
# 2024-02-23 11:58:35,947 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.012 0.045
# 2024-02-23 11:58:35,953 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.014 0.042
# 2024-02-23 11:58:36,194 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.013 0.038
# 2024-02-23 11:58:36,336 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.137 0.055
# 2024-02-23 11:58:36,371 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.170 0.047
# 2024-02-23 11:58:36,459 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.282 0.035
# 2024-02-23 11:58:36,875 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.290 0.010
# 2024-02-23 11:58:37,237 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.010 0.031
# 2024-02-23 11:58:37,244 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.018 0.030
# 2024-02-23 11:58:37,247 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.011 0.023
# 2024-02-23 11:58:37,250 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.007 0.035
# 2024-02-23 11:58:37,253 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.013 0.044
# 2024-02-23 11:58:37,333 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.028
# 2024-02-23 11:58:37,444 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.016 0.045
# 2024-02-23 11:58:37,718 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.199 0.050
# 2024-02-23 11:58:37,809 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.311 0.030
# 2024-02-23 11:58:37,821 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.310 0.032
# 2024-02-23 11:58:38,229 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.290 0.010
# 2024-02-23 11:58:38,564 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.023
# 2024-02-23 11:58:38,564 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.008 0.024
# 2024-02-23 11:58:38,568 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.009 0.026
# 2024-02-23 11:58:38,572 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.013 0.026
# 2024-02-23 11:58:38,581 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.012 0.036
# 2024-02-23 11:58:38,583 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.008 0.034
# 2024-02-23 11:58:38,823 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.012 0.037
# 2024-02-23 11:58:39,051 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.244 0.038
# 2024-02-23 11:58:39,110 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.304 0.036
# 2024-02-23 11:58:39,119 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.310 0.038
# 2024-02-23 11:58:39,530 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.290 0.010
# 2024-02-23 11:58:39,849 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.006 0.021
# 2024-02-23 11:58:39,849 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.006 0.019
# 2024-02-23 11:58:39,861 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.009 0.032
# 2024-02-23 11:58:39,861 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.007 0.035
# 2024-02-23 11:58:39,866 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.012 0.036
# 2024-02-23 11:58:39,869 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.012 0.029
# 2024-02-23 11:58:40,037 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.016 0.043
# 2024-02-23 11:58:40,336 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.303 0.036
# 2024-02-23 11:58:40,350 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.244 0.031
# 2024-02-23 11:58:40,398 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.297 0.034
# 2024-02-23 11:58:40,806 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.290 0.006
# 2024-02-23 11:58:41,133 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.007 0.028
# 2024-02-23 11:58:41,137 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.010 0.038
# 2024-02-23 11:58:41,139 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.034
# 2024-02-23 11:58:41,139 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.010 0.037
# 2024-02-23 11:58:41,145 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.017 0.035
# 2024-02-23 11:58:41,148 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.041
# 2024-02-23 11:58:41,390 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.015 0.039
# 2024-02-23 11:58:41,619 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.237 0.034
# 2024-02-23 11:58:41,676 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.303 0.037
# 2024-02-23 11:58:41,680 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.304 0.037
# 2024-02-23 11:58:42,097 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.295 0.010
# 2024-02-23 11:58:42,434 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.009 0.028
# 2024-02-23 11:58:42,438 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.010 0.032
# 2024-02-23 11:58:42,443 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.008 0.035
# 2024-02-23 11:58:42,446 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.011 0.034
# 2024-02-23 11:58:42,447 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.018 0.030
# 2024-02-23 11:58:42,453 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.013 0.033
# 2024-02-23 11:58:42,768 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.014 0.037
# 2024-02-23 11:58:42,999 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.237 0.032
# 2024-02-23 11:58:43,055 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.301 0.037
# 2024-02-23 11:58:43,056 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.303 0.038
# 2024-02-23 11:58:43,613 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.295 0.010
# 2024-02-23 11:58:43,999 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.013 0.034
# 2024-02-23 11:58:44,000 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.012 0.032
# 2024-02-23 11:58:44,007 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.009 0.029
# 2024-02-23 11:58:44,007 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.020 0.035
# 2024-02-23 11:58:44,009 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.012 0.030
# 2024-02-23 11:58:44,207 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.013 0.031
# 2024-02-23 11:58:44,256 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.013 0.031
# 2024-02-23 11:58:44,460 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.207 0.050
# 2024-02-23 11:58:44,533 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.304 0.030
# 2024-02-23 11:58:44,537 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.303 0.032
# 2024-02-23 11:58:45,031 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.294 0.010
# 2024-02-23 11:58:45,356 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.028
# 2024-02-23 11:58:45,357 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.008 0.028
# 2024-02-23 11:58:45,366 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.009 0.027
# 2024-02-23 11:58:45,367 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.011 0.035
# 2024-02-23 11:58:45,375 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.014 0.038
# 2024-02-23 11:58:45,376 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.016 0.038
# 2024-02-23 11:58:45,604 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.012 0.039
# 2024-02-23 11:58:45,819 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.224 0.041
# 2024-02-23 11:58:45,920 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.325 0.031
# 2024-02-23 11:58:45,939 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.331 0.055
# 2024-02-23 11:58:46,385 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.290 0.010
# 2024-02-23 11:58:46,745 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.010 0.032
# 2024-02-23 11:58:46,748 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.012 0.035
# 2024-02-23 11:58:46,749 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.011 0.031
# 2024-02-23 11:58:46,749 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.008 0.035
# 2024-02-23 11:58:46,754 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.019 0.033
# 2024-02-23 11:58:46,763 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.034
# 2024-02-23 11:58:47,048 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.014 0.036
# 2024-02-23 11:58:47,269 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.242 0.037
# 2024-02-23 11:58:47,330 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.308 0.035
# 2024-02-23 11:58:47,340 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.314 0.038
# 2024-02-23 11:58:47,756 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.289 0.010
# 2024-02-23 11:58:48,140 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.013 0.032
# 2024-02-23 11:58:48,140 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.010 0.032
# 2024-02-23 11:58:48,146 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.037
# 2024-02-23 11:58:48,151 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.011 0.034
# 2024-02-23 11:58:48,151 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.017 0.037
# 2024-02-23 11:58:48,152 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.018 0.036
# 2024-02-23 11:58:48,421 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.018 0.045
# 2024-02-23 11:58:48,659 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.246 0.054
# 2024-02-23 11:58:48,705 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.313 0.036
# 2024-02-23 11:58:48,727 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.320 0.038
# 2024-02-23 11:58:49,204 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 0.289 0.010
# 2024-02-23 11:58:49,547 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.012 0.033
# 2024-02-23 11:58:49,548 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 0.009 0.032
# 2024-02-23 11:58:49,551 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.013 0.036
# 2024-02-23 11:58:49,555 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.016 0.034
# 2024-02-23 11:58:49,556 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.017 0.032
# 2024-02-23 11:58:49,561 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.013 0.031
# 2024-02-23 11:58:49,791 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.017 0.042
# 2024-02-23 11:58:50,051 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.231 0.031
# 2024-02-23 11:58:50,086 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.318 0.037
# 2024-02-23 11:58:50,101 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.295 0.030
# 2024-02-23 11:58:50,304 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.020 0.050
# 2024-02-23 11:58:50,501 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.020 0.049
# 2024-02-23 11:58:50,686 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.021 0.051
# 2024-02-23 11:58:50,890 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.021 0.051
# 2024-02-23 11:58:51,084 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.022 0.051
# 2024-02-23 11:58:51,298 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.021 0.051
# 2024-02-23 11:58:51,500 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.021 0.051
# 2024-02-23 11:58:51,696 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.021 0.051
# 2024-02-23 11:58:51,890 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.021 0.050
# 2024-02-23 11:58:52,107 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 20 0.022 0.051
# 2024-02-23 11:58:52,298 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.023 0.053
# 2024-02-23 11:58:52,509 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.023 0.053
# 2024-02-23 11:58:53,035 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.023 0.053
# 2024-02-23 11:58:53,252 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.023 0.053
# 2024-02-23 11:58:53,453 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.024 0.053
# 2024-02-23 11:58:53,659 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.023 0.053
# 2024-02-23 11:58:53,876 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.023 0.053
# 2024-02-23 11:58:54,071 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.024 0.053
# 2024-02-23 11:58:54,413 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.023 0.053
# 2024-02-23 11:58:54,616 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 24 0.023 0.052
# 2024-02-23 11:58:54,763 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:58:55,047 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.006 0.016
# 2024-02-23 11:58:55,050 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.005 0.013
# 2024-02-23 11:58:55,052 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.022
# 2024-02-23 11:58:55,057 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.006 0.026
# 2024-02-23 11:58:55,061 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.031
# 2024-02-23 11:58:55,186 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:58:55,465 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.017
# 2024-02-23 11:58:55,466 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.007 0.023
# 2024-02-23 11:58:55,467 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.007 0.028
# 2024-02-23 11:58:55,468 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.008 0.029
# 2024-02-23 11:58:55,474 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.008 0.032
# 2024-02-23 11:58:55,602 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:58:55,900 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.009 0.024
# 2024-02-23 11:58:55,903 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.009 0.028
# 2024-02-23 11:58:55,905 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.008 0.020
# 2024-02-23 11:58:55,906 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.011 0.029
# 2024-02-23 11:58:55,907 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.010 0.029
# 2024-02-23 11:58:56,047 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:58:56,345 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.006 0.019
# 2024-02-23 11:58:56,354 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.006 0.026
# 2024-02-23 11:58:56,355 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.026
# 2024-02-23 11:58:56,358 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.008 0.026
# 2024-02-23 11:58:56,383 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.005 0.016
# 2024-02-23 11:58:56,522 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.004 0.013
# 2024-02-23 11:58:56,817 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.006 0.022
# 2024-02-23 11:58:56,822 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.005 0.020
# 2024-02-23 11:58:56,825 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.007 0.027
# 2024-02-23 11:58:56,833 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.036
# 2024-02-23 11:58:56,833 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.036
# 2024-02-23 11:58:56,969 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:58:57,259 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.009 0.023
# 2024-02-23 11:58:57,260 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.009 0.027
# 2024-02-23 11:58:57,264 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.008 0.031
# 2024-02-23 11:58:57,268 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.011 0.030
# 2024-02-23 11:58:57,271 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.011 0.025
# 2024-02-23 11:58:57,398 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:58:57,718 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.008 0.027
# 2024-02-23 11:58:57,719 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.009 0.020
# 2024-02-23 11:58:57,721 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.010 0.028
# 2024-02-23 11:58:57,722 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.012 0.031
# 2024-02-23 11:58:57,724 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.010 0.033
# 2024-02-23 11:58:57,851 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.013
# 2024-02-23 11:58:58,126 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.007 0.025
# 2024-02-23 11:58:58,127 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.006 0.023
# 2024-02-23 11:58:58,128 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.008 0.023
# 2024-02-23 11:58:58,128 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.027
# 2024-02-23 11:58:58,131 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.020
# 2024-02-23 11:58:58,270 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:58:58,567 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.011 0.028
# 2024-02-23 11:58:58,567 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.010 0.022
# 2024-02-23 11:58:58,571 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.009 0.028
# 2024-02-23 11:58:58,574 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.010 0.024
# 2024-02-23 11:58:58,575 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.010 0.030
# 2024-02-23 11:58:58,697 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.004 0.010
# 2024-02-23 11:58:58,971 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.006 0.020
# 2024-02-23 11:58:58,974 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.022
# 2024-02-23 11:58:58,983 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.007 0.030
# 2024-02-23 11:58:58,984 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.006 0.018
# 2024-02-23 11:58:58,986 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.009 0.032
# 2024-02-23 11:58:59,122 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:58:59,401 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.008 0.020
# 2024-02-23 11:58:59,404 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.006 0.025
# 2024-02-23 11:58:59,406 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.006 0.018
# 2024-02-23 11:58:59,415 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.009 0.035
# 2024-02-23 11:58:59,416 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.008 0.034
# 2024-02-23 11:58:59,578 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:58:59,856 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.010 0.024
# 2024-02-23 11:58:59,856 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.008 0.025
# 2024-02-23 11:58:59,860 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.008 0.029
# 2024-02-23 11:58:59,864 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.009 0.031
# 2024-02-23 11:58:59,867 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.009 0.024
# 2024-02-23 11:59:00,003 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:59:00,341 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.008 0.023
# 2024-02-23 11:59:00,341 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.021
# 2024-02-23 11:59:00,345 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.010 0.027
# 2024-02-23 11:59:00,347 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.009 0.030
# 2024-02-23 11:59:00,351 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.010 0.022
# 2024-02-23 11:59:00,480 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.013
# 2024-02-23 11:59:00,761 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.007 0.019
# 2024-02-23 11:59:00,762 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.022
# 2024-02-23 11:59:00,766 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.006 0.018
# 2024-02-23 11:59:00,769 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.009 0.031
# 2024-02-23 11:59:00,770 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.009 0.028
# 2024-02-23 11:59:00,910 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:59:01,189 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.007 0.022
# 2024-02-23 11:59:01,194 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.007 0.018
# 2024-02-23 11:59:01,195 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.007 0.028
# 2024-02-23 11:59:01,196 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.010 0.029
# 2024-02-23 11:59:01,197 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.013 0.030
# 2024-02-23 11:59:01,331 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:59:01,621 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.011 0.031
# 2024-02-23 11:59:01,625 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.012 0.031
# 2024-02-23 11:59:01,625 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.009 0.035
# 2024-02-23 11:59:01,626 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.009 0.037
# 2024-02-23 11:59:01,628 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.010 0.028
# 2024-02-23 11:59:01,778 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.001 0.004
# 2024-02-23 11:59:02,064 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.009 0.026
# 2024-02-23 11:59:02,066 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.008 0.027
# 2024-02-23 11:59:02,070 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.010 0.032
# 2024-02-23 11:59:02,075 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.010 0.034
# 2024-02-23 11:59:02,081 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.010 0.031
# 2024-02-23 11:59:02,211 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:59:02,482 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.005 0.018
# 2024-02-23 11:59:02,483 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.006 0.022
# 2024-02-23 11:59:02,486 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.007 0.023
# 2024-02-23 11:59:02,490 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.008 0.024
# 2024-02-23 11:59:02,491 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.006 0.018
# 2024-02-23 11:59:02,614 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.004 0.013
# 2024-02-23 11:59:02,885 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.008 0.020
# 2024-02-23 11:59:02,889 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.010 0.022
# 2024-02-23 11:59:02,894 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.010 0.027
# 2024-02-23 11:59:02,895 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.005 0.020
# 2024-02-23 11:59:02,899 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.010 0.031
# 2024-02-23 11:59:03,022 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.005 0.014
# 2024-02-23 11:59:03,305 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.006 0.021
# 2024-02-23 11:59:03,306 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.007 0.014
# 2024-02-23 11:59:03,307 "POST project.task/web_search_read HTTP/1.0" 200 - 16 0.008 0.022
# 2024-02-23 11:59:03,310 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.007 0.024
# 2024-02-23 11:59:03,311 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.008 0.027
# 2024-02-23 11:59:03,570 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.102 0.055
# 2024-02-23 11:59:03,863 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.114 0.055
# 2024-02-23 11:59:04,243 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.114 0.055
# 2024-02-23 11:59:04,523 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.114 0.055
# 2024-02-23 11:59:04,795 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.110 0.055
# 2024-02-23 11:59:05,077 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.114 0.055
# 2024-02-23 11:59:05,353 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.113 0.055
# 2024-02-23 11:59:05,628 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.114 0.055
# 2024-02-23 11:59:05,889 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.102 0.056
# 2024-02-23 11:59:06,168 "POST project.task/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 29 0.101 0.056
# 2024-02-23 11:59:06,444 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.113 0.057
# 2024-02-23 11:59:06,721 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.104 0.057
# 2024-02-23 11:59:06,999 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.114 0.057
# 2024-02-23 11:59:07,284 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.115 0.057
# 2024-02-23 11:59:07,572 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.115 0.057
# 2024-02-23 11:59:07,880 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.115 0.057
# 2024-02-23 11:59:08,178 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.113 0.057
# 2024-02-23 11:59:08,475 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.113 0.057
# 2024-02-23 11:59:08,761 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.113 0.057
# 2024-02-23 11:59:09,057 "POST project.task/web_read_group_unity_naive_search HTTP/1.0" 200 - 33 0.113 0.057
# 2024-02-23 11:59:09,254 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.068 0.011
# 2024-02-23 11:59:09,559 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.008 0.022
# 2024-02-23 11:59:09,569 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.013 0.026
# 2024-02-23 11:59:09,569 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.010 0.023
# 2024-02-23 11:59:09,572 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.020 0.024
# 2024-02-23 11:59:09,576 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.019 0.026
# 2024-02-23 11:59:09,787 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.080 0.010
# 2024-02-23 11:59:10,096 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.009 0.024
# 2024-02-23 11:59:10,099 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.018 0.026
# 2024-02-23 11:59:10,101 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.022 0.024
# 2024-02-23 11:59:10,106 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.013 0.040
# 2024-02-23 11:59:10,108 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.014 0.036
# 2024-02-23 11:59:10,359 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.081 0.011
# 2024-02-23 11:59:10,613 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.010 0.025
# 2024-02-23 11:59:10,618 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.015 0.025
# 2024-02-23 11:59:10,648 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.009 0.023
# 2024-02-23 11:59:10,651 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.017 0.020
# 2024-02-23 11:59:10,652 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.008 0.018
# 2024-02-23 11:59:10,849 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.071 0.014
# 2024-02-23 11:59:11,136 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.010 0.023
# 2024-02-23 11:59:11,143 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.011 0.031
# 2024-02-23 11:59:11,144 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.011 0.023
# 2024-02-23 11:59:11,159 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.022 0.036
# 2024-02-23 11:59:11,160 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.020 0.039
# 2024-02-23 11:59:11,350 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.068 0.011
# 2024-02-23 11:59:11,657 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.015 0.027
# 2024-02-23 11:59:11,665 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.014 0.033
# 2024-02-23 11:59:11,667 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.023 0.027
# 2024-02-23 11:59:11,671 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.015 0.038
# 2024-02-23 11:59:11,675 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.015 0.031
# 2024-02-23 11:59:11,879 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.081 0.010
# 2024-02-23 11:59:12,204 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.013 0.023
# 2024-02-23 11:59:12,209 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.016 0.033
# 2024-02-23 11:59:12,210 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.016 0.035
# 2024-02-23 11:59:12,214 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.027 0.030
# 2024-02-23 11:59:12,214 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.028 0.029
# 2024-02-23 11:59:12,491 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.081 0.011
# 2024-02-23 11:59:12,810 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.012 0.028
# 2024-02-23 11:59:12,817 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.017 0.033
# 2024-02-23 11:59:12,819 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.017 0.023
# 2024-02-23 11:59:12,819 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.013 0.035
# 2024-02-23 11:59:12,821 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.022 0.032
# 2024-02-23 11:59:13,036 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.080 0.010
# 2024-02-23 11:59:13,337 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.010 0.020
# 2024-02-23 11:59:13,341 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.013 0.030
# 2024-02-23 11:59:13,345 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.017 0.030
# 2024-02-23 11:59:13,347 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.013 0.033
# 2024-02-23 11:59:13,347 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.022 0.028
# 2024-02-23 11:59:13,582 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.081 0.011
# 2024-02-23 11:59:13,899 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.013 0.027
# 2024-02-23 11:59:13,899 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.011 0.031
# 2024-02-23 11:59:13,902 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.017 0.023
# 2024-02-23 11:59:13,903 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.015 0.027
# 2024-02-23 11:59:13,909 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.012 0.031
# 2024-02-23 11:59:14,115 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.080 0.010
# 2024-02-23 11:59:14,447 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.017 0.047
# 2024-02-23 11:59:14,449 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.025 0.046
# 2024-02-23 11:59:14,475 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.018 0.020
# 2024-02-23 11:59:14,476 "POST project.task/web_search_read HTTP/1.0" 200 - 25 0.013 0.026
# 2024-02-23 11:59:14,479 "POST project.task/web_search_read HTTP/1.0" 200 - 17 0.010 0.018
# 2024-02-23 11:59:14,686 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.082 0.010
# 2024-02-23 11:59:14,995 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.015 0.030
# 2024-02-23 11:59:14,998 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.015 0.024
# 2024-02-23 11:59:14,998 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.015 0.033
# 2024-02-23 11:59:15,005 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.025 0.028
# 2024-02-23 11:59:15,011 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.030 0.028
# 2024-02-23 11:59:15,225 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.080 0.010
# 2024-02-23 11:59:15,525 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.017 0.027
# 2024-02-23 11:59:15,541 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.030 0.031
# 2024-02-23 11:59:15,542 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.014 0.026
# 2024-02-23 11:59:15,542 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.015 0.025
# 2024-02-23 11:59:15,549 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.020 0.024
# 2024-02-23 11:59:15,766 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.081 0.010
# 2024-02-23 11:59:16,091 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.013 0.030
# 2024-02-23 11:59:16,098 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.013 0.024
# 2024-02-23 11:59:16,105 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.026 0.027
# 2024-02-23 11:59:16,106 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.015 0.041
# 2024-02-23 11:59:16,113 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.026 0.040
# 2024-02-23 11:59:16,312 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.080 0.010
# 2024-02-23 11:59:16,638 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.011 0.021
# 2024-02-23 11:59:16,644 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.018 0.033
# 2024-02-23 11:59:16,647 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.020 0.035
# 2024-02-23 11:59:16,652 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.029 0.031
# 2024-02-23 11:59:16,654 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.026 0.033
# 2024-02-23 11:59:16,840 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.074 0.004
# 2024-02-23 11:59:17,141 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.014 0.029
# 2024-02-23 11:59:17,144 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.019 0.031
# 2024-02-23 11:59:17,150 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.025 0.031
# 2024-02-23 11:59:17,153 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.032 0.029
# 2024-02-23 11:59:17,163 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.012 0.024
# 2024-02-23 11:59:17,344 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.073 0.010
# 2024-02-23 11:59:17,640 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.012 0.027
# 2024-02-23 11:59:17,646 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.015 0.031
# 2024-02-23 11:59:17,654 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.026 0.026
# 2024-02-23 11:59:17,664 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.014 0.039
# 2024-02-23 11:59:17,667 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.025 0.045
# 2024-02-23 11:59:17,879 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.082 0.010
# 2024-02-23 11:59:18,199 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.018 0.027
# 2024-02-23 11:59:18,206 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.018 0.031
# 2024-02-23 11:59:18,207 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.016 0.035
# 2024-02-23 11:59:18,214 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.030 0.030
# 2024-02-23 11:59:18,214 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.023 0.025
# 2024-02-23 11:59:18,403 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.081 0.010
# 2024-02-23 11:59:18,696 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.013 0.021
# 2024-02-23 11:59:18,699 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.016 0.031
# 2024-02-23 11:59:18,712 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.018 0.038
# 2024-02-23 11:59:18,720 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.030 0.038
# 2024-02-23 11:59:18,742 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.021 0.026
# 2024-02-23 11:59:18,936 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.081 0.010
# 2024-02-23 11:59:19,242 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.016 0.030
# 2024-02-23 11:59:19,243 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.019 0.027
# 2024-02-23 11:59:19,248 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.029 0.026
# 2024-02-23 11:59:19,250 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.026 0.030
# 2024-02-23 11:59:19,254 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.015 0.033
# 2024-02-23 11:59:19,462 "POST project.task/web_read_group HTTP/1.0" 200 - 4 0.080 0.011
# 2024-02-23 11:59:19,801 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.030 0.039
# 2024-02-23 11:59:19,802 "POST project.task/web_search_read HTTP/1.0" 200 - 18 0.014 0.027
# 2024-02-23 11:59:19,814 "POST project.task/web_search_read HTTP/1.0" 200 - 19 0.026 0.024
# 2024-02-23 11:59:19,820 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.017 0.038
# 2024-02-23 11:59:19,825 "POST project.task/web_search_read HTTP/1.0" 200 - 26 0.025 0.039
# 2024-02-23 11:59:22,536 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.515 0.093
# 2024-02-23 11:59:25,279 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.527 0.091
# 2024-02-23 11:59:28,009 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.520 0.090
# 2024-02-23 11:59:30,745 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.529 0.090
# 2024-02-23 11:59:33,488 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.520 0.091
# 2024-02-23 11:59:36,302 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.525 0.091
# 2024-02-23 11:59:39,055 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.523 0.090
# 2024-02-23 11:59:41,797 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.529 0.090
# 2024-02-23 11:59:44,524 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.510 0.091
# 2024-02-23 11:59:47,266 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 2.516 0.090
# 2024-02-23 11:59:51,302 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.789 0.097
# 2024-02-23 11:59:55,282 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.748 0.098
# 2024-02-23 11:59:59,246 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.743 0.097
# 2024-02-23 12:00:03,219 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.759 0.098
# 2024-02-23 12:00:07,233 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.782 0.097
# 2024-02-23 12:00:11,248 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.768 0.097
# 2024-02-23 12:00:15,250 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.791 0.096
# 2024-02-23 12:00:19,271 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.769 0.096
# 2024-02-23 12:00:23,326 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.786 0.096
# 2024-02-23 12:00:27,332 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 35 3.775 0.096
# 2024-02-23 12:00:28,708 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.233 0.010
# 2024-02-23 12:00:29,160 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.128 0.021
# 2024-02-23 12:00:29,183 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.151 0.020
# 2024-02-23 12:00:29,305 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.259 0.029
# 2024-02-23 12:00:29,361 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.305 0.035
# 2024-02-23 12:00:29,426 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.132 0.022
# 2024-02-23 12:00:29,445 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.375 0.057
# 2024-02-23 12:00:29,912 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.563 0.026
# 2024-02-23 12:00:29,994 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.949 0.029
# 2024-02-23 12:00:31,368 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.246 0.011
# 2024-02-23 12:00:31,815 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.126 0.018
# 2024-02-23 12:00:31,819 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.125 0.027
# 2024-02-23 12:00:31,983 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.264 0.047
# 2024-02-23 12:00:32,021 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.314 0.037
# 2024-02-23 12:00:32,088 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.376 0.035
# 2024-02-23 12:00:32,122 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.134 0.020
# 2024-02-23 12:00:32,542 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.557 0.027
# 2024-02-23 12:00:32,652 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.954 0.030
# 2024-02-23 12:00:34,054 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.255 0.011
# 2024-02-23 12:00:34,513 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.124 0.026
# 2024-02-23 12:00:34,520 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.131 0.029
# 2024-02-23 12:00:34,678 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.275 0.029
# 2024-02-23 12:00:34,714 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.312 0.038
# 2024-02-23 12:00:34,786 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.382 0.042
# 2024-02-23 12:00:34,869 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.134 0.033
# 2024-02-23 12:00:35,298 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.580 0.027
# 2024-02-23 12:00:35,324 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.924 0.034
# 2024-02-23 12:00:36,672 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.234 0.010
# 2024-02-23 12:00:37,064 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.121 0.021
# 2024-02-23 12:00:37,074 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.125 0.028
# 2024-02-23 12:00:37,246 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.256 0.029
# 2024-02-23 12:00:37,266 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.308 0.038
# 2024-02-23 12:00:37,393 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.383 0.035
# 2024-02-23 12:00:37,406 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.137 0.023
# 2024-02-23 12:00:37,828 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.544 0.027
# 2024-02-23 12:00:37,877 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.923 0.031
# 2024-02-23 12:00:39,236 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.248 0.011
# 2024-02-23 12:00:39,687 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.126 0.028
# 2024-02-23 12:00:39,688 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.123 0.029
# 2024-02-23 12:00:39,847 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.273 0.030
# 2024-02-23 12:00:39,913 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.321 0.033
# 2024-02-23 12:00:39,989 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.392 0.037
# 2024-02-23 12:00:39,990 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.135 0.023
# 2024-02-23 12:00:40,426 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.552 0.027
# 2024-02-23 12:00:40,500 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.934 0.033
# 2024-02-23 12:00:41,926 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.259 0.010
# 2024-02-23 12:00:42,363 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.124 0.023
# 2024-02-23 12:00:42,363 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.123 0.025
# 2024-02-23 12:00:42,511 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.267 0.032
# 2024-02-23 12:00:42,565 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.316 0.037
# 2024-02-23 12:00:42,665 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.387 0.057
# 2024-02-23 12:00:42,667 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.134 0.023
# 2024-02-23 12:00:43,112 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.572 0.042
# 2024-02-23 12:00:43,207 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.964 0.027
# 2024-02-23 12:00:44,579 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.241 0.011
# 2024-02-23 12:00:45,035 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.129 0.019
# 2024-02-23 12:00:45,043 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.130 0.024
# 2024-02-23 12:00:45,209 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.275 0.044
# 2024-02-23 12:00:45,257 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.321 0.045
# 2024-02-23 12:00:45,303 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.369 0.037
# 2024-02-23 12:00:45,355 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.145 0.020
# 2024-02-23 12:00:45,793 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.574 0.041
# 2024-02-23 12:00:45,873 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.956 0.026
# 2024-02-23 12:00:47,248 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.237 0.011
# 2024-02-23 12:00:47,685 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.122 0.020
# 2024-02-23 12:00:47,709 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.147 0.018
# 2024-02-23 12:00:47,849 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.274 0.029
# 2024-02-23 12:00:47,901 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.325 0.034
# 2024-02-23 12:00:47,968 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.380 0.036
# 2024-02-23 12:00:47,996 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.134 0.021
# 2024-02-23 12:00:48,448 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.571 0.025
# 2024-02-23 12:00:48,497 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.929 0.028
# 2024-02-23 12:00:49,889 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.250 0.011
# 2024-02-23 12:00:50,346 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.123 0.020
# 2024-02-23 12:00:50,355 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.127 0.026
# 2024-02-23 12:00:50,521 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.291 0.032
# 2024-02-23 12:00:50,579 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.310 0.054
# 2024-02-23 12:00:50,607 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.368 0.037
# 2024-02-23 12:00:50,679 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.156 0.032
# 2024-02-23 12:00:51,063 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.558 0.025
# 2024-02-23 12:00:51,203 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.968 0.026
# 2024-02-23 12:00:52,647 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.247 0.011
# 2024-02-23 12:00:53,063 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.126 0.018
# 2024-02-23 12:00:53,063 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.124 0.024
# 2024-02-23 12:00:53,219 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.269 0.030
# 2024-02-23 12:00:53,268 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.312 0.031
# 2024-02-23 12:00:53,324 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.369 0.034
# 2024-02-23 12:00:53,584 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.130 0.021
# 2024-02-23 12:00:53,866 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.920 0.031
# 2024-02-23 12:00:53,970 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.546 0.025
# 2024-02-23 12:00:55,362 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.249 0.011
# 2024-02-23 12:00:55,814 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.121 0.021
# 2024-02-23 12:00:55,818 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.119 0.017
# 2024-02-23 12:00:55,981 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.272 0.033
# 2024-02-23 12:00:56,131 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.136 0.024
# 2024-02-23 12:00:56,367 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.635 0.056
# 2024-02-23 12:00:56,468 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.747 0.048
# 2024-02-23 12:00:57,078 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.092 0.026
# 2024-02-23 12:00:57,452 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.746 0.032
# 2024-02-23 12:00:58,810 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.254 0.010
# 2024-02-23 12:00:59,229 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.122 0.017
# 2024-02-23 12:00:59,231 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.125 0.019
# 2024-02-23 12:00:59,401 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.263 0.050
# 2024-02-23 12:00:59,530 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.135 0.022
# 2024-02-23 12:00:59,725 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.597 0.034
# 2024-02-23 12:00:59,872 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.732 0.055
# 2024-02-23 12:01:00,518 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.130 0.026
# 2024-02-23 12:01:00,834 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.713 0.030
# 2024-02-23 12:01:02,194 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.252 0.010
# 2024-02-23 12:01:02,628 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.123 0.017
# 2024-02-23 12:01:02,662 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.145 0.023
# 2024-02-23 12:01:02,801 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.286 0.030
# 2024-02-23 12:01:02,906 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.155 0.023
# 2024-02-23 12:01:03,131 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.592 0.053
# 2024-02-23 12:01:03,224 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.697 0.040
# 2024-02-23 12:01:03,942 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.112 0.026
# 2024-02-23 12:01:04,229 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.713 0.031
# 2024-02-23 12:01:05,599 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.247 0.011
# 2024-02-23 12:01:06,040 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.125 0.018
# 2024-02-23 12:01:06,066 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.125 0.024
# 2024-02-23 12:01:06,192 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.263 0.028
# 2024-02-23 12:01:06,364 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.141 0.036
# 2024-02-23 12:01:06,560 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.624 0.034
# 2024-02-23 12:01:06,646 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.705 0.042
# 2024-02-23 12:01:07,319 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.095 0.026
# 2024-02-23 12:01:07,658 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.714 0.047
# 2024-02-23 12:01:09,037 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.247 0.011
# 2024-02-23 12:01:09,492 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.126 0.018
# 2024-02-23 12:01:09,494 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.125 0.017
# 2024-02-23 12:01:09,675 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.279 0.047
# 2024-02-23 12:01:09,835 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.138 0.023
# 2024-02-23 12:01:09,983 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.580 0.056
# 2024-02-23 12:01:10,117 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.705 0.061
# 2024-02-23 12:01:10,812 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.158 0.027
# 2024-02-23 12:01:11,126 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.741 0.030
# 2024-02-23 12:01:12,500 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.247 0.010
# 2024-02-23 12:01:12,968 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.123 0.019
# 2024-02-23 12:01:12,973 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.123 0.015
# 2024-02-23 12:01:13,148 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.273 0.051
# 2024-02-23 12:01:13,244 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.134 0.022
# 2024-02-23 12:01:13,491 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.627 0.037
# 2024-02-23 12:01:13,595 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.707 0.065
# 2024-02-23 12:01:14,221 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.095 0.026
# 2024-02-23 12:01:14,590 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.732 0.029
# 2024-02-23 12:01:15,979 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.231 0.004
# 2024-02-23 12:01:16,436 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.129 0.021
# 2024-02-23 12:01:16,445 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.125 0.029
# 2024-02-23 12:01:16,589 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.260 0.027
# 2024-02-23 12:01:16,774 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.143 0.036
# 2024-02-23 12:01:16,924 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.596 0.040
# 2024-02-23 12:01:17,055 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.718 0.046
# 2024-02-23 12:01:17,731 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.099 0.027
# 2024-02-23 12:01:18,041 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.715 0.036
# 2024-02-23 12:01:19,394 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.233 0.010
# 2024-02-23 12:01:19,821 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.123 0.015
# 2024-02-23 12:01:19,830 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.124 0.025
# 2024-02-23 12:01:19,975 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.268 0.032
# 2024-02-23 12:01:20,154 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.160 0.024
# 2024-02-23 12:01:20,321 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.591 0.056
# 2024-02-23 12:01:20,424 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.707 0.040
# 2024-02-23 12:01:21,150 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.117 0.043
# 2024-02-23 12:01:21,452 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.744 0.031
# 2024-02-23 12:01:22,809 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.236 0.010
# 2024-02-23 12:01:23,236 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.123 0.026
# 2024-02-23 12:01:23,273 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.168 0.019
# 2024-02-23 12:01:23,442 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.302 0.046
# 2024-02-23 12:01:23,518 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.155 0.023
# 2024-02-23 12:01:23,719 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.596 0.034
# 2024-02-23 12:01:23,832 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.703 0.043
# 2024-02-23 12:01:24,576 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.116 0.042
# 2024-02-23 12:01:24,859 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.742 0.034
# 2024-02-23 12:01:26,280 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.238 0.010
# 2024-02-23 12:01:26,790 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.124 0.015
# 2024-02-23 12:01:26,794 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.124 0.030
# 2024-02-23 12:01:26,952 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.272 0.036
# 2024-02-23 12:01:27,096 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.140 0.022
# 2024-02-23 12:01:27,308 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.619 0.045
# 2024-02-23 12:01:27,422 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.718 0.062
# 2024-02-23 12:01:28,051 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.100 0.028
# 2024-02-23 12:01:28,399 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 1.723 0.034
# 2024-02-23 12:02:01,331 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.777 0.035
# 2024-02-23 12:02:34,443 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.884 0.122
# 2024-02-23 12:03:07,371 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.765 0.036
# 2024-02-23 12:03:40,340 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.751 0.035
# 2024-02-23 12:04:13,137 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.504 0.035
# 2024-02-23 12:04:45,791 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.484 0.035
# 2024-02-23 12:05:18,538 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.546 0.035
# 2024-02-23 12:05:51,174 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.466 0.033
# 2024-02-23 12:06:23,845 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.492 0.035
# 2024-02-23 12:06:56,779 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 32.547 0.035
# 2024-02-23 12:07:33,537 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 36.611 0.037
# 2024-02-23 12:08:10,239 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 36.521 0.036
# 2024-02-23 12:08:46,855 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 36.480 0.037
# 2024-02-23 12:09:23,560 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 36.530 0.036
# 2024-02-23 12:10:00,170 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 36.452 0.037
# 2024-02-23 12:10:37,619 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 37.281 0.034
# 2024-02-23 12:11:14,979 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 37.198 0.037
# 2024-02-23 12:11:51,961 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 36.661 0.037
# 2024-02-23 12:12:28,640 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 36.506 0.037
# 2024-02-23 12:12:40,013 2939752 INFO openerp longpolling: 94.140.178.73 - - [2024-02-23 12:12:40] "GET /websocket HTTP/1.1" 101 450 3948.325179 
# 2024-02-23 12:13:06,031 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 30 37.223 0.038
# 2024-02-23 12:13:22,482 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.330 0.010
# 2024-02-23 12:13:23,119 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.405 0.016
# 2024-02-23 12:13:23,402 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.681 0.021
# 2024-02-23 12:13:24,048 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.323 0.016
# 2024-02-23 12:13:40,829 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 18.101 0.029
# 2024-02-23 12:13:57,419 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.475 0.004
# 2024-02-23 12:13:58,150 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.442 0.020
# 2024-02-23 12:13:58,217 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.510 0.016
# 2024-02-23 12:13:59,012 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.299 0.017
# 2024-02-23 12:14:15,657 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 17.938 0.030
# 2024-02-23 12:14:32,037 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.241 0.011
# 2024-02-23 12:14:32,691 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.395 0.012
# 2024-02-23 12:14:32,808 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.509 0.025
# 2024-02-23 12:14:33,616 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.321 0.018
# 2024-02-23 12:14:50,670 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 18.365 0.029
# 2024-02-23 12:15:07,451 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.603 0.010
# 2024-02-23 12:15:08,104 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.398 0.016
# 2024-02-23 12:15:08,217 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.503 0.016
# 2024-02-23 12:15:09,013 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.304 0.022
# 2024-02-23 12:15:25,653 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 17.934 0.031
# 2024-02-23 12:15:42,505 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.743 0.009
# 2024-02-23 12:15:43,123 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.395 0.017
# 2024-02-23 12:15:43,243 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.510 0.019
# 2024-02-23 12:15:44,043 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.311 0.021
# 2024-02-23 12:16:00,917 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 18.165 0.026
# 2024-02-23 12:16:17,399 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.337 0.009
# 2024-02-23 12:16:18,044 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.398 0.020
# 2024-02-23 12:16:18,160 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.514 0.017
# 2024-02-23 12:16:18,966 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.310 0.018
# 2024-02-23 12:16:35,766 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 18.110 0.028
# 2024-02-23 12:16:52,420 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.408 0.010
# 2024-02-23 12:16:53,055 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.396 0.018
# 2024-02-23 12:16:53,155 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.509 0.014
# 2024-02-23 12:16:53,961 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.312 0.017
# 2024-02-23 12:17:10,739 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 18.080 0.029
# 2024-02-23 12:17:27,602 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.742 0.009
# 2024-02-23 12:17:28,293 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.393 0.014
# 2024-02-23 12:17:28,422 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.508 0.022
# 2024-02-23 12:17:29,219 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.318 0.018
# 2024-02-23 12:17:46,006 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 18.092 0.029
# 2024-02-23 12:18:02,402 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.284 0.010
# 2024-02-23 12:18:02,986 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.406 0.017
# 2024-02-23 12:18:03,121 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.505 0.013
# 2024-02-23 12:18:03,930 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.314 0.015
# 2024-02-23 12:18:20,573 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 17.935 0.026
# 2024-02-23 12:18:36,969 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.242 0.010
# 2024-02-23 12:18:37,623 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.393 0.018
# 2024-02-23 12:18:37,727 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.505 0.016
# 2024-02-23 12:18:38,567 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.343 0.019
# 2024-02-23 12:18:55,333 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 18.100 0.029
# 2024-02-23 12:19:11,762 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.265 0.010
# 2024-02-23 12:19:12,398 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.390 0.019
# 2024-02-23 12:19:12,505 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.508 0.020
# 2024-02-23 12:19:13,313 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.316 0.022
# 2024-02-23 12:19:44,864 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 32.855 0.033
# 2024-02-23 12:20:01,577 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.582 0.009
# 2024-02-23 12:20:02,272 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.447 0.024
# 2024-02-23 12:20:02,392 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.564 0.017
# 2024-02-23 12:20:03,133 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.310 0.021
# 2024-02-23 12:20:34,734 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 32.899 0.032
# 2024-02-23 12:20:51,220 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.379 0.009
# 2024-02-23 12:20:51,869 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.398 0.021
# 2024-02-23 12:20:51,995 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.510 0.014
# 2024-02-23 12:20:52,781 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.311 0.019
# 2024-02-23 12:21:24,241 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 32.750 0.027
# 2024-02-23 12:21:40,887 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.532 0.009
# 2024-02-23 12:21:41,576 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.389 0.013
# 2024-02-23 12:21:41,693 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.511 0.019
# 2024-02-23 12:21:42,480 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.295 0.021
# 2024-02-23 12:22:14,062 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 32.867 0.032
# 2024-02-23 12:22:30,881 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.690 0.010
# 2024-02-23 12:22:31,581 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.395 0.017
# 2024-02-23 12:22:31,714 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.511 0.024
# 2024-02-23 12:22:32,507 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.318 0.021
# 2024-02-23 12:23:03,712 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 32.507 0.034
# 2024-02-23 12:23:20,185 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.349 0.010
# 2024-02-23 12:23:20,837 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.392 0.023
# 2024-02-23 12:23:20,946 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.518 0.019
# 2024-02-23 12:23:21,753 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.308 0.021
# 2024-02-23 12:23:53,365 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 32.905 0.026
# 2024-02-23 12:24:10,317 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.747 0.009
# 2024-02-23 12:24:10,975 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.392 0.016
# 2024-02-23 12:24:11,094 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.504 0.014
# 2024-02-23 12:24:11,892 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.305 0.020
# 2024-02-23 12:24:43,609 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 33.011 0.032
# 2024-02-23 12:25:00,463 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.736 0.009
# 2024-02-23 12:25:01,170 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.394 0.017
# 2024-02-23 12:25:01,288 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.509 0.020
# 2024-02-23 12:25:02,127 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.338 0.018
# 2024-02-23 12:25:33,493 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 32.700 0.032
# 2024-02-23 12:25:50,090 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.375 0.009
# 2024-02-23 12:25:50,722 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.396 0.017
# 2024-02-23 12:25:50,845 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.512 0.027
# 2024-02-23 12:25:51,673 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.344 0.022
# 2024-02-23 12:26:23,142 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 32.796 0.028
# 2024-02-23 12:26:39,880 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 16.579 0.009
# 2024-02-23 12:26:40,580 "POST crm.lead/web_search_read HTTP/1.0" 200 - 14 0.394 0.018
# 2024-02-23 12:26:40,703 "POST crm.lead/web_search_read HTTP/1.0" 200 - 15 0.523 0.026
# 2024-02-23 12:26:41,543 "POST crm.lead/web_search_read HTTP/1.0" 200 - 16 1.354 0.026
# 2024-02-23 12:27:12,933 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 32.744 0.033
# 2024-02-23 12:27:14,573 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.524 0.010
# 2024-02-23 12:27:16,261 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.530 0.011
# 2024-02-23 12:27:17,945 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.529 0.012
# 2024-02-23 12:27:19,687 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.531 0.011
# 2024-02-23 12:27:21,373 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.528 0.010
# 2024-02-23 12:27:23,056 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.528 0.011
# 2024-02-23 12:27:24,738 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.536 0.011
# 2024-02-23 12:27:26,419 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.547 0.011
# 2024-02-23 12:27:28,084 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.547 0.010
# 2024-02-23 12:27:29,827 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 4 1.540 0.009
# 2024-02-23 12:27:31,471 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.542 0.011
# 2024-02-23 12:27:33,170 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.549 0.010
# 2024-02-23 12:27:34,856 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.547 0.011
# 2024-02-23 12:27:36,522 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.543 0.011
# 2024-02-23 12:27:38,313 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.538 0.011
# 2024-02-23 12:27:40,169 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.549 0.011
# 2024-02-23 12:27:41,839 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.551 0.011
# 2024-02-23 12:27:43,576 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.545 0.010
# 2024-02-23 12:27:45,233 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.544 0.010
# 2024-02-23 12:27:46,882 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 4 1.541 0.010
# 2024-02-23 12:27:48,565 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.544 0.010
# 2024-02-23 12:27:50,221 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.539 0.011
# 2024-02-23 12:27:51,944 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.533 0.010
# 2024-02-23 12:27:53,686 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.539 0.010
# 2024-02-23 12:27:55,411 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.532 0.011
# 2024-02-23 12:27:57,061 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.532 0.010
# 2024-02-23 12:27:58,798 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.536 0.010
# 2024-02-23 12:28:00,550 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.535 0.011
# 2024-02-23 12:28:02,202 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.534 0.009
# 2024-02-23 12:28:03,999 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.537 0.010
# 2024-02-23 12:28:05,634 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.522 0.004
# 2024-02-23 12:28:07,276 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.533 0.010
# 2024-02-23 12:28:09,131 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.530 0.010
# 2024-02-23 12:28:10,992 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.545 0.011
# 2024-02-23 12:28:12,723 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.525 0.010
# 2024-02-23 12:28:14,400 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.531 0.010
# 2024-02-23 12:28:16,043 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.535 0.011
# 2024-02-23 12:28:17,750 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.532 0.011
# 2024-02-23 12:28:19,479 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.537 0.010
# 2024-02-23 12:28:21,144 "POST crm.lead/web_read_group HTTP/1.0" 200 - 4 1.536 0.011
# 2024-02-23 12:28:21,999 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.555 0.118
# 2024-02-23 12:28:22,816 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.551 0.120
# 2024-02-23 12:28:23,660 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.553 0.120
# 2024-02-23 12:28:24,471 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.539 0.120
# 2024-02-23 12:28:25,297 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.558 0.120
# 2024-02-23 12:28:26,114 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.550 0.120
# 2024-02-23 12:28:26,943 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.550 0.120
# 2024-02-23 12:28:27,759 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.540 0.121
# 2024-02-23 12:28:28,590 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.538 0.119
# 2024-02-23 12:28:29,417 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 27 0.551 0.121
# 2024-02-23 12:28:30,663 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.987 0.122
# 2024-02-23 12:28:31,926 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.974 0.122
# 2024-02-23 12:28:33,200 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.972 0.123
# 2024-02-23 12:28:34,534 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.974 0.121
# 2024-02-23 12:28:35,864 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.978 0.122
# 2024-02-23 12:28:37,119 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.973 0.122
# 2024-02-23 12:28:38,415 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.972 0.123
# 2024-02-23 12:28:39,779 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.976 0.120
# 2024-02-23 12:28:41,073 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.935 0.116
# 2024-02-23 12:28:42,296 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 36 0.937 0.125
# 2024-02-23 12:28:42,730 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.272 0.010
# 2024-02-23 12:28:43,191 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.012 0.028
# 2024-02-23 12:28:43,196 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.012 0.036
# 2024-02-23 12:28:43,199 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.016 0.038
# 2024-02-23 12:28:43,288 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.097 0.040
# 2024-02-23 12:28:43,309 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.115 0.047
# 2024-02-23 12:28:43,406 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.017 0.027
# 2024-02-23 12:28:43,414 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.016 0.028
# 2024-02-23 12:28:43,495 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.286 0.051
# 2024-02-23 12:28:43,534 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.066 0.028
# 2024-02-23 12:28:43,668 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.279 0.027
# 2024-02-23 12:28:44,065 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.283 0.011
# 2024-02-23 12:28:44,419 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.014 0.032
# 2024-02-23 12:28:44,426 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.009 0.030
# 2024-02-23 12:28:44,427 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.012 0.036
# 2024-02-23 12:28:44,503 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.081 0.044
# 2024-02-23 12:28:44,517 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.106 0.035
# 2024-02-23 12:28:44,607 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.014 0.028
# 2024-02-23 12:28:44,652 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.017 0.023
# 2024-02-23 12:28:44,732 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.318 0.038
# 2024-02-23 12:28:44,783 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.079 0.028
# 2024-02-23 12:28:44,921 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.270 0.028
# 2024-02-23 12:28:45,418 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.291 0.011
# 2024-02-23 12:28:45,813 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.012 0.033
# 2024-02-23 12:28:45,817 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.035
# 2024-02-23 12:28:45,819 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.010 0.028
# 2024-02-23 12:28:45,878 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.077 0.029
# 2024-02-23 12:28:45,919 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.114 0.035
# 2024-02-23 12:28:46,017 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.016 0.024
# 2024-02-23 12:28:46,030 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.014 0.028
# 2024-02-23 12:28:46,122 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.300 0.055
# 2024-02-23 12:28:46,171 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.074 0.028
# 2024-02-23 12:28:46,285 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.277 0.027
# 2024-02-23 12:28:46,690 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.279 0.011
# 2024-02-23 12:28:46,995 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.008 0.023
# 2024-02-23 12:28:46,998 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.009 0.028
# 2024-02-23 12:28:47,000 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.008 0.031
# 2024-02-23 12:28:47,086 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.095 0.025
# 2024-02-23 12:28:47,124 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.128 0.032
# 2024-02-23 12:28:47,194 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.016 0.024
# 2024-02-23 12:28:47,198 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.013 0.027
# 2024-02-23 12:28:47,314 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.297 0.047
# 2024-02-23 12:28:47,322 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.066 0.028
# 2024-02-23 12:28:47,478 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.285 0.027
# 2024-02-23 12:28:47,945 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.279 0.011
# 2024-02-23 12:28:48,269 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.009 0.028
# 2024-02-23 12:28:48,288 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.011 0.045
# 2024-02-23 12:28:48,292 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.011 0.044
# 2024-02-23 12:28:48,338 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.078 0.032
# 2024-02-23 12:28:48,374 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.108 0.035
# 2024-02-23 12:28:48,498 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.024
# 2024-02-23 12:28:48,504 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.015 0.028
# 2024-02-23 12:28:48,563 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.296 0.039
# 2024-02-23 12:28:48,630 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.078 0.029
# 2024-02-23 12:28:48,770 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.270 0.028
# 2024-02-23 12:28:49,218 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.283 0.010
# 2024-02-23 12:28:49,617 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.033
# 2024-02-23 12:28:49,623 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.011 0.037
# 2024-02-23 12:28:49,634 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.010 0.026
# 2024-02-23 12:28:49,690 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.088 0.031
# 2024-02-23 12:28:49,725 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.117 0.038
# 2024-02-23 12:28:49,820 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.023
# 2024-02-23 12:28:49,825 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.014 0.027
# 2024-02-23 12:28:49,896 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.291 0.034
# 2024-02-23 12:28:50,023 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.075 0.043
# 2024-02-23 12:28:50,109 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.272 0.028
# 2024-02-23 12:28:50,516 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.285 0.011
# 2024-02-23 12:28:50,839 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.015 0.031
# 2024-02-23 12:28:50,847 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.016 0.038
# 2024-02-23 12:28:50,857 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.013 0.048
# 2024-02-23 12:28:50,913 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.079 0.030
# 2024-02-23 12:28:50,956 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.119 0.039
# 2024-02-23 12:28:51,057 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.023
# 2024-02-23 12:28:51,064 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.019 0.025
# 2024-02-23 12:28:51,153 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.317 0.040
# 2024-02-23 12:28:51,186 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.066 0.028
# 2024-02-23 12:28:51,388 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.285 0.026
# 2024-02-23 12:28:51,835 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.273 0.011
# 2024-02-23 12:28:52,195 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.009 0.029
# 2024-02-23 12:28:52,200 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.011 0.032
# 2024-02-23 12:28:52,207 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.011 0.039
# 2024-02-23 12:28:52,277 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.087 0.038
# 2024-02-23 12:28:52,329 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.135 0.032
# 2024-02-23 12:28:52,408 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.015 0.023
# 2024-02-23 12:28:52,459 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.015 0.044
# 2024-02-23 12:28:52,563 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.083 0.029
# 2024-02-23 12:28:52,594 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.315 0.121
# 2024-02-23 12:28:52,699 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.282 0.027
# 2024-02-23 12:28:53,125 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.281 0.011
# 2024-02-23 12:28:53,594 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.008 0.021
# 2024-02-23 12:28:53,611 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.009 0.046
# 2024-02-23 12:28:53,613 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.048
# 2024-02-23 12:28:53,667 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.082 0.027
# 2024-02-23 12:28:53,719 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.128 0.031
# 2024-02-23 12:28:53,820 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.016 0.035
# 2024-02-23 12:28:53,833 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.015 0.037
# 2024-02-23 12:28:53,930 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.321 0.050
# 2024-02-23 12:28:53,941 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.077 0.028
# 2024-02-23 12:28:54,083 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.285 0.028
# 2024-02-23 12:28:54,500 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.274 0.011
# 2024-02-23 12:28:54,832 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.010 0.033
# 2024-02-23 12:28:54,834 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.011 0.030
# 2024-02-23 12:28:54,843 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.011 0.038
# 2024-02-23 12:28:54,902 "POST crm.lead/web_search_read HTTP/1.0" 200 - 21 0.082 0.030
# 2024-02-23 12:28:54,942 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.110 0.032
# 2024-02-23 12:28:55,043 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.014 0.027
# 2024-02-23 12:28:55,051 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.022 0.036
# 2024-02-23 12:28:55,140 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.316 0.033
# 2024-02-23 12:28:55,212 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.102 0.028
# 2024-02-23 12:28:55,319 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.296 0.027
# 2024-02-23 12:28:55,721 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.284 0.011
# 2024-02-23 12:28:56,161 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.011 0.035
# 2024-02-23 12:28:56,167 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.012 0.039
# 2024-02-23 12:28:56,177 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.011 0.042
# 2024-02-23 12:28:56,314 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.167 0.030
# 2024-02-23 12:28:56,336 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.190 0.033
# 2024-02-23 12:28:56,347 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.025 0.027
# 2024-02-23 12:28:56,355 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.019 0.027
# 2024-02-23 12:28:56,629 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.160 0.031
# 2024-02-23 12:28:56,652 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.504 0.034
# 2024-02-23 12:28:56,773 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.383 0.027
# 2024-02-23 12:28:57,183 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.283 0.010
# 2024-02-23 12:28:57,584 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.009 0.027
# 2024-02-23 12:28:57,607 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.011 0.048
# 2024-02-23 12:28:57,609 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.011 0.050
# 2024-02-23 12:28:57,740 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.159 0.026
# 2024-02-23 12:28:57,780 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.187 0.047
# 2024-02-23 12:28:57,790 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.027 0.025
# 2024-02-23 12:28:57,803 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.020 0.032
# 2024-02-23 12:28:58,043 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.132 0.032
# 2024-02-23 12:28:58,098 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.517 0.033
# 2024-02-23 12:28:58,187 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.359 0.028
# 2024-02-23 12:28:58,596 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.282 0.011
# 2024-02-23 12:28:59,082 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.014 0.034
# 2024-02-23 12:28:59,086 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.012 0.037
# 2024-02-23 12:28:59,091 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.014 0.043
# 2024-02-23 12:28:59,220 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.146 0.029
# 2024-02-23 12:28:59,281 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.204 0.040
# 2024-02-23 12:28:59,312 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.019 0.029
# 2024-02-23 12:28:59,313 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.033 0.026
# 2024-02-23 12:28:59,523 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.164 0.030
# 2024-02-23 12:28:59,634 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.562 0.038
# 2024-02-23 12:28:59,649 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.364 0.030
# 2024-02-23 12:29:00,130 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.283 0.011
# 2024-02-23 12:29:00,545 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.023
# 2024-02-23 12:29:00,550 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.031
# 2024-02-23 12:29:00,552 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.011 0.033
# 2024-02-23 12:29:00,676 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.132 0.025
# 2024-02-23 12:29:00,765 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.033 0.027
# 2024-02-23 12:29:00,766 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.021 0.029
# 2024-02-23 12:29:00,774 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.215 0.049
# 2024-02-23 12:29:00,939 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.128 0.029
# 2024-02-23 12:29:01,068 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.524 0.031
# 2024-02-23 12:29:01,113 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.376 0.028
# 2024-02-23 12:29:01,530 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.281 0.011
# 2024-02-23 12:29:01,893 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.013 0.034
# 2024-02-23 12:29:01,897 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.011 0.036
# 2024-02-23 12:29:01,902 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.035
# 2024-02-23 12:29:02,011 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.140 0.025
# 2024-02-23 12:29:02,093 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.209 0.033
# 2024-02-23 12:29:02,131 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.018 0.027
# 2024-02-23 12:29:02,192 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.023 0.035
# 2024-02-23 12:29:02,363 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.133 0.032
# 2024-02-23 12:29:02,405 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.514 0.042
# 2024-02-23 12:29:02,545 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.371 0.027
# 2024-02-23 12:29:02,989 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.281 0.011
# 2024-02-23 12:29:03,332 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.009 0.024
# 2024-02-23 12:29:03,340 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.012 0.033
# 2024-02-23 12:29:03,351 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.011 0.045
# 2024-02-23 12:29:03,494 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.155 0.035
# 2024-02-23 12:29:03,499 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.022 0.030
# 2024-02-23 12:29:03,516 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.027 0.029
# 2024-02-23 12:29:03,561 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.213 0.051
# 2024-02-23 12:29:03,767 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.137 0.046
# 2024-02-23 12:29:03,868 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.536 0.034
# 2024-02-23 12:29:03,901 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.362 0.028
# 2024-02-23 12:29:04,309 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.282 0.011
# 2024-02-23 12:29:04,660 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.012 0.031
# 2024-02-23 12:29:04,679 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.053
# 2024-02-23 12:29:04,682 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.014 0.055
# 2024-02-23 12:29:04,800 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.155 0.032
# 2024-02-23 12:29:04,813 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.027 0.027
# 2024-02-23 12:29:04,838 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.186 0.039
# 2024-02-23 12:29:04,902 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.019 0.037
# 2024-02-23 12:29:05,081 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.132 0.030
# 2024-02-23 12:29:05,169 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.510 0.035
# 2024-02-23 12:29:05,235 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.369 0.028
# 2024-02-23 12:29:05,642 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.282 0.010
# 2024-02-23 12:29:05,978 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.009 0.028
# 2024-02-23 12:29:05,985 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.032
# 2024-02-23 12:29:05,987 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.010 0.032
# 2024-02-23 12:29:06,139 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.166 0.029
# 2024-02-23 12:29:06,202 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.024 0.037
# 2024-02-23 12:29:06,203 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.020 0.040
# 2024-02-23 12:29:06,215 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.216 0.048
# 2024-02-23 12:29:06,445 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.132 0.031
# 2024-02-23 12:29:06,489 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.510 0.032
# 2024-02-23 12:29:06,609 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.364 0.027
# 2024-02-23 12:29:07,023 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.283 0.010
# 2024-02-23 12:29:07,352 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.037
# 2024-02-23 12:29:07,358 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.010 0.041
# 2024-02-23 12:29:07,360 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.011 0.043
# 2024-02-23 12:29:07,523 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.168 0.037
# 2024-02-23 12:29:07,534 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.182 0.046
# 2024-02-23 12:29:07,571 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.023 0.025
# 2024-02-23 12:29:07,582 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.019 0.028
# 2024-02-23 12:29:07,784 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.129 0.030
# 2024-02-23 12:29:07,859 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.519 0.036
# 2024-02-23 12:29:07,925 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.372 0.029
# 2024-02-23 12:29:08,335 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.279 0.011
# 2024-02-23 12:29:08,657 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.009 0.024
# 2024-02-23 12:29:08,664 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.012 0.034
# 2024-02-23 12:29:08,677 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.012 0.051
# 2024-02-23 12:29:08,784 "POST crm.lead/web_search_read HTTP/1.0" 200 - 22 0.140 0.032
# 2024-02-23 12:29:08,845 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.021 0.039
# 2024-02-23 12:29:08,859 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.206 0.037
# 2024-02-23 12:29:08,897 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.024 0.040
# 2024-02-23 12:29:09,073 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.135 0.030
# 2024-02-23 12:29:09,200 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.547 0.038
# 2024-02-23 12:29:09,233 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.361 0.029
# 2024-02-23 12:29:10,521 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.972 0.137
# 2024-02-23 12:29:11,810 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.971 0.136
# 2024-02-23 12:29:13,160 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.969 0.137
# 2024-02-23 12:29:14,409 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.968 0.128
# 2024-02-23 12:29:15,658 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.975 0.133
# 2024-02-23 12:29:17,050 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.963 0.212
# 2024-02-23 12:29:18,378 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.961 0.133
# 2024-02-23 12:29:19,694 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.972 0.134
# 2024-02-23 12:29:21,031 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.973 0.138
# 2024-02-23 12:29:22,343 "POST crm.lead/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 28 0.972 0.133
# 2024-02-23 12:29:25,744 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 3.013 0.137
# 2024-02-23 12:29:29,129 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 3.003 0.140
# 2024-02-23 12:29:32,503 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 3.015 0.137
# 2024-02-23 12:29:35,904 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 2.996 0.138
# 2024-02-23 12:29:39,229 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 2.995 0.139
# 2024-02-23 12:29:42,560 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 3.022 0.144
# 2024-02-23 12:29:45,894 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 2.994 0.140
# 2024-02-23 12:29:49,300 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 3.009 0.139
# 2024-02-23 12:29:52,569 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 3.005 0.140
# 2024-02-23 12:29:55,946 "POST crm.lead/web_read_group_unity_naive_search HTTP/1.0" 200 - 37 3.009 0.141
# 2024-02-23 12:29:56,375 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.283 0.008
# 2024-02-23 12:29:57,103 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.344 0.025
# 2024-02-23 12:29:57,172 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.401 0.039
# 2024-02-23 12:29:57,228 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.435 0.056
# 2024-02-23 12:29:57,295 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.526 0.035
# 2024-02-23 12:29:57,554 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.756 0.055
# 2024-02-23 12:29:57,602 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.811 0.054
# 2024-02-23 12:29:57,684 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.362 0.034
# 2024-02-23 12:29:57,737 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.389 0.051
# 2024-02-23 12:29:57,827 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.392 0.032
# 2024-02-23 12:29:57,887 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.446 0.027
# 2024-02-23 12:29:58,315 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.284 0.008
# 2024-02-23 12:29:59,068 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.389 0.026
# 2024-02-23 12:29:59,077 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.393 0.030
# 2024-02-23 12:29:59,167 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.463 0.053
# 2024-02-23 12:29:59,220 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.536 0.029
# 2024-02-23 12:29:59,245 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.543 0.051
# 2024-02-23 12:29:59,416 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.705 0.052
# 2024-02-23 12:29:59,581 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.309 0.035
# 2024-02-23 12:29:59,624 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.367 0.030
# 2024-02-23 12:29:59,752 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.393 0.028
# 2024-02-23 12:29:59,849 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.475 0.031
# 2024-02-23 12:30:00,241 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.274 0.009
# 2024-02-23 12:30:00,950 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.362 0.041
# 2024-02-23 12:30:00,968 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.374 0.046
# 2024-02-23 12:30:01,035 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.439 0.051
# 2024-02-23 12:30:01,094 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.519 0.028
# 2024-02-23 12:30:01,150 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.550 0.050
# 2024-02-23 12:30:01,334 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.722 0.055
# 2024-02-23 12:30:01,527 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.408 0.055
# 2024-02-23 12:30:01,598 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.404 0.030
# 2024-02-23 12:30:01,622 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.420 0.050
# 2024-02-23 12:30:01,695 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.454 0.027
# 2024-02-23 12:30:02,103 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.288 0.009
# 2024-02-23 12:30:02,799 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.362 0.043
# 2024-02-23 12:30:02,833 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.386 0.049
# 2024-02-23 12:30:02,864 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.436 0.032
# 2024-02-23 12:30:02,955 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.522 0.037
# 2024-02-23 12:30:03,113 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.672 0.041
# 2024-02-23 12:30:03,133 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.691 0.038
# 2024-02-23 12:30:03,339 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.370 0.051
# 2024-02-23 12:30:03,417 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.367 0.034
# 2024-02-23 12:30:03,460 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.402 0.032
# 2024-02-23 12:30:03,544 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.427 0.027
# 2024-02-23 12:30:03,980 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.285 0.009
# 2024-02-23 12:30:04,740 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.353 0.054
# 2024-02-23 12:30:04,777 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.409 0.031
# 2024-02-23 12:30:04,782 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.423 0.024
# 2024-02-23 12:30:04,897 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.518 0.043
# 2024-02-23 12:30:05,146 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.757 0.050
# 2024-02-23 12:30:05,210 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.808 0.056
# 2024-02-23 12:30:05,254 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.364 0.031
# 2024-02-23 12:30:05,384 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.401 0.030
# 2024-02-23 12:30:05,391 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.377 0.050
# 2024-02-23 12:30:05,516 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.460 0.027
# 2024-02-23 12:30:05,935 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.286 0.009
# 2024-02-23 12:30:06,657 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.352 0.035
# 2024-02-23 12:30:06,717 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.407 0.039
# 2024-02-23 12:30:06,738 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.433 0.033
# 2024-02-23 12:30:06,836 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.525 0.032
# 2024-02-23 12:30:07,059 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.756 0.029
# 2024-02-23 12:30:07,078 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.740 0.064
# 2024-02-23 12:30:07,213 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.400 0.031
# 2024-02-23 12:30:07,315 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.400 0.032
# 2024-02-23 12:30:07,334 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.429 0.032
# 2024-02-23 12:30:07,485 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.512 0.027
# 2024-02-23 12:30:07,910 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.284 0.008
# 2024-02-23 12:30:08,599 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.358 0.050
# 2024-02-23 12:30:08,600 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.360 0.050
# 2024-02-23 12:30:08,677 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.439 0.049
# 2024-02-23 12:30:08,746 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.522 0.036
# 2024-02-23 12:30:08,968 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.717 0.052
# 2024-02-23 12:30:09,007 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.753 0.060
# 2024-02-23 12:30:09,156 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.381 0.030
# 2024-02-23 12:30:09,162 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.354 0.055
# 2024-02-23 12:30:09,274 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.381 0.032
# 2024-02-23 12:30:09,340 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.440 0.027
# 2024-02-23 12:30:09,751 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.284 0.009
# 2024-02-23 12:30:10,450 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.363 0.041
# 2024-02-23 12:30:10,452 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.368 0.039
# 2024-02-23 12:30:10,507 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.433 0.032
# 2024-02-23 12:30:10,662 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.559 0.060
# 2024-02-23 12:30:10,799 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.684 0.043
# 2024-02-23 12:30:10,801 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.694 0.052
# 2024-02-23 12:30:11,016 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.382 0.032
# 2024-02-23 12:30:11,020 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.377 0.052
# 2024-02-23 12:30:11,115 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.416 0.032
# 2024-02-23 12:30:11,186 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.396 0.027
# 2024-02-23 12:30:11,589 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.284 0.009
# 2024-02-23 12:30:12,275 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.354 0.028
# 2024-02-23 12:30:12,360 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.430 0.036
# 2024-02-23 12:30:12,387 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.444 0.050
# 2024-02-23 12:30:12,405 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.467 0.049
# 2024-02-23 12:30:12,675 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.750 0.034
# 2024-02-23 12:30:12,688 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.733 0.053
# 2024-02-23 12:30:12,807 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.398 0.034
# 2024-02-23 12:30:12,852 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.368 0.031
# 2024-02-23 12:30:12,973 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.377 0.032
# 2024-02-23 12:30:13,059 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.447 0.027
# 2024-02-23 12:30:13,466 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.279 0.009
# 2024-02-23 12:30:14,205 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.415 0.034
# 2024-02-23 12:30:14,223 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.422 0.048
# 2024-02-23 12:30:14,233 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.431 0.051
# 2024-02-23 12:30:14,286 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.500 0.030
# 2024-02-23 12:30:14,515 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.732 0.022
# 2024-02-23 12:30:14,537 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.739 0.043
# 2024-02-23 12:30:14,819 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.378 0.032
# 2024-02-23 12:30:14,883 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.442 0.030
# 2024-02-23 12:30:14,908 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.439 0.049
# 2024-02-23 12:30:14,983 "POST crm.lead/web_search_read HTTP/1.0" 200 - 24 0.467 0.028
# 2024-02-23 12:30:15,407 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.282 0.009
# 2024-02-23 12:30:16,439 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.692 0.037
# 2024-02-23 12:30:16,453 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.712 0.024
# 2024-02-23 12:30:16,561 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.793 0.056
# 2024-02-23 12:30:16,609 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.847 0.051
# 2024-02-23 12:30:16,810 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 1.047 0.056
# 2024-02-23 12:30:16,908 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.160 0.039
# 2024-02-23 12:30:17,047 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.415 0.040
# 2024-02-23 12:30:17,310 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.674 0.032
# 2024-02-23 12:30:17,444 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.731 0.036
# 2024-02-23 12:30:17,613 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.846 0.028
# 2024-02-23 12:30:18,032 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.283 0.009
# 2024-02-23 12:30:18,718 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.363 0.022
# 2024-02-23 12:30:19,098 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.732 0.033
# 2024-02-23 12:30:19,192 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.812 0.046
# 2024-02-23 12:30:19,339 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.449 0.058
# 2024-02-23 12:30:19,431 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.039 0.050
# 2024-02-23 12:30:19,503 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.113 0.059
# 2024-02-23 12:30:19,548 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.181 0.033
# 2024-02-23 12:30:19,952 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.720 0.033
# 2024-02-23 12:30:20,076 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.596 0.029
# 2024-02-23 12:30:20,082 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.728 0.051
# 2024-02-23 12:30:20,491 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.285 0.009
# 2024-02-23 12:30:21,253 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.442 0.036
# 2024-02-23 12:30:21,498 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.675 0.037
# 2024-02-23 12:30:21,589 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.770 0.041
# 2024-02-23 12:30:21,594 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.777 0.040
# 2024-02-23 12:30:21,928 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.525 0.034
# 2024-02-23 12:30:22,027 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.219 0.034
# 2024-02-23 12:30:22,091 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 1.261 0.056
# 2024-02-23 12:30:22,327 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.678 0.035
# 2024-02-23 12:30:22,569 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.762 0.033
# 2024-02-23 12:30:22,651 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.920 0.028
# 2024-02-23 12:30:23,033 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.272 0.004
# 2024-02-23 12:30:23,928 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.565 0.034
# 2024-02-23 12:30:24,132 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.745 0.057
# 2024-02-23 12:30:24,202 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.839 0.033
# 2024-02-23 12:30:24,208 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.824 0.059
# 2024-02-23 12:30:24,406 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 1.023 0.053
# 2024-02-23 12:30:24,630 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.244 0.051
# 2024-02-23 12:30:24,789 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.716 0.037
# 2024-02-23 12:30:24,918 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.525 0.047
# 2024-02-23 12:30:24,959 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.672 0.034
# 2024-02-23 12:30:25,061 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.676 0.028
# 2024-02-23 12:30:25,483 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.286 0.009
# 2024-02-23 12:30:26,548 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.732 0.045
# 2024-02-23 12:30:26,593 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.784 0.038
# 2024-02-23 12:30:26,616 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.798 0.037
# 2024-02-23 12:30:26,657 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.851 0.036
# 2024-02-23 12:30:26,881 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.044 0.062
# 2024-02-23 12:30:26,901 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 1.074 0.054
# 2024-02-23 12:30:27,051 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.367 0.033
# 2024-02-23 12:30:27,418 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.628 0.033
# 2024-02-23 12:30:27,511 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.731 0.033
# 2024-02-23 12:30:27,688 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.833 0.031
# 2024-02-23 12:30:28,092 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.285 0.009
# 2024-02-23 12:30:29,089 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.659 0.036
# 2024-02-23 12:30:29,216 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.775 0.043
# 2024-02-23 12:30:29,277 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.813 0.059
# 2024-02-23 12:30:29,293 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.844 0.053
# 2024-02-23 12:30:29,458 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.001 0.061
# 2024-02-23 12:30:29,513 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.078 0.036
# 2024-02-23 12:30:29,993 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.751 0.053
# 2024-02-23 12:30:30,035 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.661 0.055
# 2024-02-23 12:30:30,096 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.623 0.053
# 2024-02-23 12:30:30,101 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.660 0.031
# 2024-02-23 12:30:30,583 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.296 0.010
# 2024-02-23 12:30:31,643 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.674 0.032
# 2024-02-23 12:30:31,759 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.787 0.037
# 2024-02-23 12:30:31,829 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.833 0.060
# 2024-02-23 12:30:31,838 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.865 0.040
# 2024-02-23 12:30:31,993 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.016 0.035
# 2024-02-23 12:30:32,188 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.401 0.034
# 2024-02-23 12:30:32,201 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.231 0.038
# 2024-02-23 12:30:32,597 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.707 0.033
# 2024-02-23 12:30:32,692 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.692 0.044
# 2024-02-23 12:30:32,744 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.741 0.036
# 2024-02-23 12:30:33,167 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.284 0.009
# 2024-02-23 12:30:34,260 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.744 0.039
# 2024-02-23 12:30:34,300 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.781 0.043
# 2024-02-23 12:30:34,307 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.772 0.058
# 2024-02-23 12:30:34,349 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.832 0.040
# 2024-02-23 12:30:34,530 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.988 0.055
# 2024-02-23 12:30:34,784 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.260 0.038
# 2024-02-23 12:30:35,073 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.492 0.032
# 2024-02-23 12:30:35,215 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.640 0.028
# 2024-02-23 12:30:35,259 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.681 0.032
# 2024-02-23 12:30:35,321 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.706 0.051
# 2024-02-23 12:30:35,735 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.285 0.009
# 2024-02-23 12:30:36,743 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.542 0.036
# 2024-02-23 12:30:36,835 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.637 0.038
# 2024-02-23 12:30:36,985 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.785 0.040
# 2024-02-23 12:30:37,016 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.797 0.057
# 2024-02-23 12:30:37,292 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.080 0.048
# 2024-02-23 12:30:37,301 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.081 0.050
# 2024-02-23 12:30:37,465 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.416 0.033
# 2024-02-23 12:30:37,820 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.761 0.032
# 2024-02-23 12:30:37,906 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.742 0.034
# 2024-02-23 12:30:38,037 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.867 0.030
# 2024-02-23 12:30:38,450 "POST crm.lead/web_read_group HTTP/1.0" 200 - 3 0.283 0.009
# 2024-02-23 12:30:39,497 "POST crm.lead/web_search_read HTTP/1.0" 200 - 23 0.722 0.037
# 2024-02-23 12:30:39,563 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.772 0.058
# 2024-02-23 12:30:39,592 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.815 0.043
# 2024-02-23 12:30:39,593 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.798 0.050
# 2024-02-23 12:30:39,821 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.031 0.054
# 2024-02-23 12:30:40,052 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.406 0.054
# 2024-02-23 12:30:40,076 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 1.302 0.038
# 2024-02-23 12:30:40,287 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.510 0.032
# 2024-02-23 12:30:40,414 "POST crm.lead/web_search_read HTTP/1.0" 200 - 26 0.631 0.039
# 2024-02-23 12:30:40,621 "POST crm.lead/web_search_read HTTP/1.0" 200 - 25 0.839 0.028
# 2024-02-23 12:30:42,805 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.802 0.248
# 2024-02-23 12:30:44,988 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.811 0.248
# 2024-02-23 12:30:47,254 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.817 0.249
# 2024-02-23 12:30:49,469 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.803 0.249
# 2024-02-23 12:30:51,659 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.804 0.248
# 2024-02-23 12:30:53,873 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.802 0.248
# 2024-02-23 12:30:56,080 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.810 0.252
# 2024-02-23 12:30:58,267 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.808 0.238
# 2024-02-23 12:31:00,474 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.813 0.238
# 2024-02-23 12:31:02,702 "POST project.project/web_read_group_unity_union_all_cte HTTP/1.0" 200 - 36 1.814 0.247
# 2024-02-23 12:31:04,896 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.809 0.250
# 2024-02-23 12:31:07,098 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.816 0.242
# 2024-02-23 12:31:09,293 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.815 0.238
# 2024-02-23 12:31:11,498 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.832 0.239
# 2024-02-23 12:31:13,752 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.859 0.243
# 2024-02-23 12:31:15,969 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.831 0.242
# 2024-02-23 12:31:18,178 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.816 0.249
# 2024-02-23 12:31:20,364 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.809 0.240
# 2024-02-23 12:31:22,572 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.816 0.240
# 2024-02-23 12:31:24,770 "POST project.project/web_read_group_unity_naive_search HTTP/1.0" 200 - 41 1.817 0.239
# 2024-02-23 12:31:24,911 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.007 0.004
# 2024-02-23 12:31:25,288 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.033 0.042
# 2024-02-23 12:31:25,324 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.057 0.053
# 2024-02-23 12:31:25,342 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.047 0.079
# 2024-02-23 12:31:25,355 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.076 0.061
# 2024-02-23 12:31:25,361 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.078 0.059
# 2024-02-23 12:31:26,813 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.461 0.135
# 2024-02-23 12:31:26,966 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:31:27,329 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.025 0.035
# 2024-02-23 12:31:27,366 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.056 0.038
# 2024-02-23 12:31:27,408 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.078 0.060
# 2024-02-23 12:31:27,423 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.061 0.091
# 2024-02-23 12:31:27,436 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.076 0.083
# 2024-02-23 12:31:28,850 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.446 0.129
# 2024-02-23 12:31:28,986 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:31:29,367 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.034 0.044
# 2024-02-23 12:31:29,382 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.050 0.038
# 2024-02-23 12:31:29,416 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.050 0.079
# 2024-02-23 12:31:29,418 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.071 0.063
# 2024-02-23 12:31:29,442 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.084 0.073
# 2024-02-23 12:31:30,880 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.446 0.145
# 2024-02-23 12:31:31,110 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.005 0.006
# 2024-02-23 12:31:36,370 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.060 0.055
# 2024-02-23 12:31:36,439 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.023 0.028
# 2024-02-23 12:31:36,539 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.056 0.047
# 2024-02-23 12:31:36,571 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.048 0.087
# 2024-02-23 12:31:36,589 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.068 0.071
# 2024-02-23 12:31:38,007 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.446 0.129
# 2024-02-23 12:31:38,146 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:31:38,529 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.032 0.044
# 2024-02-23 12:31:38,564 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.054 0.052
# 2024-02-23 12:31:38,605 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.060 0.091
# 2024-02-23 12:31:38,610 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.080 0.073
# 2024-02-23 12:31:38,617 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.079 0.072
# 2024-02-23 12:31:40,050 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.450 0.144
# 2024-02-23 12:31:40,193 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:31:40,580 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.045 0.036
# 2024-02-23 12:31:40,591 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.033 0.036
# 2024-02-23 12:31:40,618 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.079 0.068
# 2024-02-23 12:31:40,627 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.052 0.103
# 2024-02-23 12:31:40,629 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.085 0.076
# 2024-02-23 12:31:42,101 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.453 0.139
# 2024-02-23 12:31:42,266 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.009 0.008
# 2024-02-23 12:31:42,641 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.035 0.043
# 2024-02-23 12:31:42,672 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.059 0.042
# 2024-02-23 12:31:42,698 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.054 0.080
# 2024-02-23 12:31:42,705 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.081 0.059
# 2024-02-23 12:31:42,712 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.083 0.070
# 2024-02-23 12:31:44,148 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.447 0.140
# 2024-02-23 12:31:44,310 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:31:44,682 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.026 0.040
# 2024-02-23 12:31:44,715 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.051 0.052
# 2024-02-23 12:31:44,756 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.077 0.071
# 2024-02-23 12:31:44,758 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.050 0.088
# 2024-02-23 12:31:44,758 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.083 0.063
# 2024-02-23 12:31:46,188 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.437 0.142
# 2024-02-23 12:31:46,379 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:31:46,764 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.033 0.052
# 2024-02-23 12:31:46,776 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.052 0.048
# 2024-02-23 12:31:46,826 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.072 0.080
# 2024-02-23 12:31:46,838 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.075 0.076
# 2024-02-23 12:31:46,853 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.063 0.116
# 2024-02-23 12:31:48,263 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.449 0.135
# 2024-02-23 12:31:48,437 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:31:48,827 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.031 0.050
# 2024-02-23 12:31:48,851 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.048 0.050
# 2024-02-23 12:31:48,893 "POST project.project/web_search_read HTTP/1.0" 200 - 25 0.077 0.071
# 2024-02-23 12:31:48,894 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.079 0.069
# 2024-02-23 12:31:48,905 "POST project.project/web_search_read HTTP/1.0" 200 - 33 0.062 0.097
# 2024-02-23 12:31:50,321 "POST project.project/web_search_read HTTP/1.0" 200 - 35 1.434 0.141
# 2024-02-23 12:31:50,485 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:31:50,869 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.029 0.044
# 2024-02-23 12:31:50,912 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.058 0.053
# 2024-02-23 12:31:50,931 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.053 0.081
# 2024-02-23 12:31:50,938 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.068 0.072
# 2024-02-23 12:31:50,963 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.084 0.086
# 2024-02-23 12:31:52,382 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.446 0.141
# 2024-02-23 12:31:52,606 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:31:52,978 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.032 0.044
# 2024-02-23 12:31:53,003 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.058 0.043
# 2024-02-23 12:31:53,036 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.072 0.063
# 2024-02-23 12:31:53,064 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.068 0.095
# 2024-02-23 12:31:53,067 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.089 0.078
# 2024-02-23 12:31:54,491 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.435 0.141
# 2024-02-23 12:31:54,622 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.017 0.009
# 2024-02-23 12:31:54,983 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.032 0.050
# 2024-02-23 12:31:55,018 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.060 0.053
# 2024-02-23 12:31:55,051 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.080 0.068
# 2024-02-23 12:31:55,058 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.061 0.092
# 2024-02-23 12:31:55,066 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.074 0.086
# 2024-02-23 12:31:56,493 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.446 0.133
# 2024-02-23 12:31:56,699 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.017 0.009
# 2024-02-23 12:31:57,051 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.032 0.035
# 2024-02-23 12:31:57,080 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.059 0.045
# 2024-02-23 12:31:57,126 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.079 0.073
# 2024-02-23 12:31:57,134 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.061 0.099
# 2024-02-23 12:31:57,137 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.093 0.072
# 2024-02-23 12:31:58,547 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.426 0.143
# 2024-02-23 12:31:58,675 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:31:59,044 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.034 0.045
# 2024-02-23 12:31:59,079 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.058 0.053
# 2024-02-23 12:31:59,107 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.080 0.060
# 2024-02-23 12:31:59,124 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.076 0.086
# 2024-02-23 12:31:59,127 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.061 0.101
# 2024-02-23 12:32:00,567 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.446 0.141
# 2024-02-23 12:32:00,728 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:32:01,101 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.033 0.047
# 2024-02-23 12:32:01,136 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.057 0.056
# 2024-02-23 12:32:01,180 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.070 0.084
# 2024-02-23 12:32:01,181 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.079 0.070
# 2024-02-23 12:32:01,190 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.056 0.110
# 2024-02-23 12:32:02,606 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.447 0.133
# 2024-02-23 12:32:02,886 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:32:03,269 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.036 0.043
# 2024-02-23 12:32:03,289 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.052 0.049
# 2024-02-23 12:32:03,336 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.073 0.072
# 2024-02-23 12:32:03,346 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.060 0.099
# 2024-02-23 12:32:03,348 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.089 0.064
# 2024-02-23 12:32:04,771 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.443 0.139
# 2024-02-23 12:32:04,902 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:32:05,251 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.025 0.034
# 2024-02-23 12:32:05,299 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.056 0.045
# 2024-02-23 12:32:05,351 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.058 0.092
# 2024-02-23 12:32:05,352 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.083 0.076
# 2024-02-23 12:32:05,362 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.082 0.084
# 2024-02-23 12:32:06,796 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.460 0.140
# 2024-02-23 12:32:06,953 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:32:07,306 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.031 0.040
# 2024-02-23 12:32:07,334 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.055 0.046
# 2024-02-23 12:32:07,366 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.054 0.077
# 2024-02-23 12:32:07,385 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.081 0.069
# 2024-02-23 12:32:07,395 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.082 0.071
# 2024-02-23 12:32:08,808 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.431 0.145
# 2024-02-23 12:32:08,953 "POST project.project/web_read_group HTTP/1.0" 200 - 2 0.016 0.009
# 2024-02-23 12:32:09,330 "POST project.project/web_search_read HTTP/1.0" 200 - 32 0.034 0.042
# 2024-02-23 12:32:09,355 "POST project.project/web_search_read HTTP/1.0" 200 - 31 0.057 0.053
# 2024-02-23 12:32:09,386 "POST project.project/web_search_read HTTP/1.0" 200 - 29 0.076 0.061
# 2024-02-23 12:32:09,407 "POST project.project/web_search_read HTTP/1.0" 200 - 34 0.077 0.082
# 2024-02-23 12:32:09,407 "POST project.project/web_search_read HTTP/1.0" 200 - 26 0.090 0.072
# 2024-02-23 12:32:10,818 "POST project.project/web_search_read HTTP/1.0" 200 - 36 1.433 0.138

