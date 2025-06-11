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

READ_SPEC_TASK = {
    "stage_id": {"fields": {"display_name": {}}},
    "rating_count": {},
    "rating_avg": {},
    "rating_active": {},
    "has_late_and_unreached_milestone": {},
    "allow_milestones": {},
    "state": {},
    "subtask_count": {},
    "progress": {},
    "remaining_hours": {},
    "allocated_hours": {},
    "allow_timesheets": {},
    "encode_uom_in_days": {},
    "x_virtual_remaining": {},
    "project_id": {"fields": {"display_name": {}}},
    "color": {},
    "name": {},
    "parent_id": {"fields": {"display_name": {}}},
    "partner_id": {"fields": {"display_name": {}}},
    "milestone_id": {"fields": {"display_name": {}}},
    "tag_ids": {"fields": {"display_name": {}, "color": {}}},
    "date_deadline": {},
    "planned_date_begin": {},
    "planning_overlap": {},
    "leave_warning": {},
    "task_properties": {},
    "displayed_image_id": {"fields": {"display_name": {}}},
    "priority": {},
    "activity_ids": {"fields": {}},
    "activity_exception_decoration": {},
    "activity_exception_icon": {},
    "activity_state": {},
    "activity_summary": {},
    "activity_type_icon": {},
    "activity_type_id": {"fields": {"display_name": {}}},
    "display_timesheet_timer": {},
    "timer_start": {},
    "user_ids": {"fields": {"display_name": {}}, "context": {"active_test": False}},
    "closed_subtask_count": {},
}

READ_SPEC_PROJECT = {}


BASE_URL = "https://www.next.odoo.com"
# BASE_URL = "http://127.0.0.1:8069"
SESSION_ID = ""
CK = ""
if not SESSION_ID:
    print("Missing SESSION_ID")
    exit()

COOKIES = {
    "session_id": SESSION_ID,
    "_ck": CK,
}
HEADERS = {
    "Content-Type": "application/json; charset=UTF-8",
    # "Accept": "*/*",
}
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
            "__count",
            "probability:avg",
            "recurring_revenue_monthly:sum",
            "color:sum",
            "expected_revenue:sum",
        ],
        "read_specification": READ_SPEC_CRM,
        "auto_unfold": True,
        "unfold_read_default_limit": 40,
        "extra_context": {
            "default_type": "opportunity",
        },
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
            "__count",
            "probability:avg",
            "recurring_revenue_monthly:sum",
            "color:sum",
            "expected_revenue:sum",
        ],
        "read_specification": READ_SPEC_CRM,
        "auto_unfold": True,
        "unfold_read_default_limit": 40,
        "extra_context": {
            "default_type": "opportunity",
        },
    },
    # Open CRM - Kanban - Filter: default (none) - groupby lang_code (related field)
    {
        "name": "Open CRM - Kanban - Filter: default (none) - groupby lang_code (related field)",
        "model": "crm.lead",
        "domain": [["type", "=", "opportunity"]],
        "groupby": ["lang_code"],
        "aggregates": [
            "__count",
            "probability:avg",
            "recurring_revenue_monthly:sum",
            "color:sum",
            "expected_revenue:sum",
        ],
        "read_specification": READ_SPEC_CRM,
        "auto_unfold": True,
        "unfold_read_default_limit": 40,
        "extra_context": {
            "default_type": "opportunity",
        },
    },
    # Open CRM - Kanban - Filter : search 'test' (default groupby)
    {
        "name": "Open CRM - Kanban - Filter : search 'test' (default groupby)",
        "model": "crm.lead",
        "domain": [
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
        "groupby": ["stage_id"],
        "aggregates": [
            "__count",
            "probability:avg",
            "recurring_revenue_monthly:sum",
            "color:sum",
            "expected_revenue:sum",
        ],
        "read_specification": READ_SPEC_CRM,
        "auto_unfold": True,
        "unfold_read_default_limit": 40,
        "extra_context": {
            "default_type": "opportunity",
        },
    },
    # Open CRM - Kanban - Filter My Pipeline with VIDH as user
    {
        "name": "Open CRM - Kanban - Filter My Pipeline with (VIDH) as user",
        "model": "crm.lead",
        "domain": ["&", ["type", "=", "opportunity"], ["user_id", "=", 6474071]],
        "groupby": ["stage_id"],
        "aggregates": [
            "__count",
            "probability:avg",
            "recurring_revenue_monthly:sum",
            "color:sum",
            "expected_revenue:sum",
        ],
        "read_specification": READ_SPEC_CRM,
        "auto_unfold": True,
        "unfold_read_default_limit": 40,
        "extra_context": {
            "default_type": "opportunity",
        },
    },
    # ------- project.task
    # Kanban: Open Framework Python project - No filters
    {
        "name": "Open Framework Python project - No filters",
        "model": "project.task",
        "domain": [
            "&",
            "&",
            ["project_id", "=", 1364],
            ["has_template_ancestor", "=", False],
            ["is_closed", "=", False],
        ],
        "groupby": ["stage_id"],
        "aggregates": [
            "__count",
            "progress:avg",
            "remaining_hours:sum",
            "allocated_hours:sum",
            "x_virtual_remaining:sum",
            "color:sum",
        ],
        "auto_unfold": True,
        "read_specification": READ_SPEC_TASK,
        "unfold_read_default_limit": 20,
        "extra_context": {
            "active_model": "project.project",
            "active_id": 1364,
            "active_ids": [1364],
            "default_project_id": 1364,
            "show_project_update": True,
            "create": True,
            "active_test": True,
            "allow_timesheets": False,
            "hide_partner": False,
            "allow_billable": True,
            "project_kanban": True,
        },
    },
    # Kanban: Open Help project - No filter
    {
        "name": "Kanban: Open Help project - No filter",
        "model": "project.task",
        "domain": [
            "&",
            "&",
            ["project_id", "=", 49],
            ["has_template_ancestor", "=", False],
            ["is_closed", "=", False],
        ],
        "groupby": ["stage_id"],
        "aggregates": [
            "__count",
            "progress:avg",
            "remaining_hours:sum",
            "allocated_hours:sum",
            "x_virtual_remaining:sum",
            "color:sum",
        ],
        "read_specification": READ_SPEC_TASK,
        "auto_unfold": True,
        "unfold_read_default_limit": 20,
        "extra_context": {
            "active_model": "project.project",
            "active_id": 49,
            "active_ids": [49],
            "default_project_id": 49,
            "show_project_update": True,
            "create": True,
            "active_test": True,
            "allow_timesheets": False,
            "hide_partner": False,
            "allow_billable": True,
            "project_kanban": True,
        },
    },
    # Kanban: Open Help project - Search "bve)" on Assignees
    {
        "name": "Kanban: Open Help project - Search 'bve)' on Assignees",
        "model": "project.task",
        "domain": [
            "&",
            "&",
            ["project_id", "=", 49],
            ["has_template_ancestor", "=", False],
            "&",
            ["is_closed", "=", False],
            "&",
            ["user_ids.name", "ilike", "bve)"],
            ["user_ids.active", "in", [True, False]],
        ],
        "groupby": ["stage_id"],
        "aggregates": [
            "__count",
            "progress:avg",
            "remaining_hours:sum",
            "allocated_hours:sum",
            "x_virtual_remaining:sum",
            "color:sum",
        ],
        "read_specification": READ_SPEC_TASK,
        "auto_unfold": True,
        "unfold_read_default_limit": 20,
        "extra_context": {
            "active_model": "project.project",
            "active_id": 49,
            "active_ids": [49],
            "default_project_id": 49,
            "show_project_update": True,
            "create": True,
            "active_test": True,
            "allow_timesheets": False,
            "hide_partner": False,
            "allow_billable": True,
            "project_kanban": True,
        },
    },
]


def get_url(model, method):
    return f"{BASE_URL}/web/dataset/call_kw/RYV/{model}/{method}"


def get_default_json_data(model, method):
    return {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": model,
            "method": method,
            "args": [],
            "kwargs": {
                "context": {
                    "lang": "en_US",
                    "tz": "Europe/Brussels",
                    "uid": 1222511,
                    "allowed_company_ids": [1],
                    "read_group_expand": True,
                    "bin_size": True,
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
    json_data["params"]["kwargs"]["context"].update(scenario["extra_context"])

    start = time_ns()
    res = requests.post(url, json=json_data, cookies=COOKIES, headers=HEADERS)
    delay_user = time_ns() - start
    worker_time = res.elapsed.total_seconds() * 1000

    try:
        groups = res.json()["result"]["groups"]
    except KeyError:
        print("Failing")
        print(res.text)
        exit()

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
        json_data["params"]["kwargs"]["context"].update(scenario["extra_context"])
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
            headers=HEADERS,
        )
        for g in unfold_groups
    ]

    start = time_ns()
    results = grequests.map(parallel_web_search_read, size=MAX_PARALLEL_REQUEST)
    delay_user += time_ns() - start

    for group, res in zip(unfold_groups, results):
        try:
            group["__records"] = res.json()["result"]["records"]
        except KeyError:
            print("Failing")
            print(res.text)
            exit()
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
    json_data["params"]["kwargs"]["context"].update(scenario["extra_context"])
    start = time_ns()
    res = requests.post(
        get_url(model, method), json=json_data, cookies=COOKIES, headers=HEADERS
    )
    delay_user = time_ns() - start
    try:
        json_res = res.json()["result"]["groups"]
    except KeyError:
        print("Failing")
        print(res.text)
        exit()

    return json_res, (
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

    return sorted(res_user_time)[: -(NB_TEST // 2)], sorted(res_worker_time)[
        : -(NB_TEST // 2)
    ]


if __name__ == "__main__":
    for i in range(1):  # Warmup
        for scenario in SCENARIOS:
            if not scenario:
                continue
            print("Warmup", scenario["name"])
            new_groups, [delay_user, delay_worker] = new_way(
                "web_read_group_unity_trivial", scenario
            )

            print(
                f"\tUni Trivial> User time: {delay_user:10.3f} ms | Worker time: {delay_worker:10.3f} ms"
            )

            new_groups, [delay_user, delay_worker] = new_way(
                "web_read_group_unity_union_all_simple", scenario
            )
            print(
                f"\tUni Union All> User time: {delay_user:10.3f} ms | Worker time: {delay_worker:10.3f} ms"
            )

            # new_groups, [delay_user, delay_worker] = new_way(
            #     "web_read_group_unity_cte", scenario
            # )
            # print(
            #     f"\tUni CTE> User time: {delay_user:10.3f} ms | Worker time: {delay_worker:10.3f} ms"
            # )
            old_groups, [delay_user, delay_worker] = old_way(
                scenario, new_groups, with_issue=True
            )
            print(
                f"\tOld> User time: {delay_user:10.3f} ms | Worker time: {delay_worker:10.3f} ms"
            )
            old_groups, [delay_user, delay_worker] = old_way(
                scenario, new_groups, with_issue=False
            )
            print(
                f"\tOld (Fixed)> User time: {delay_user:10.3f} ms | Worker time: {delay_worker:10.3f} ms"
            )

            # assert (
            #     old_groups == new_groups
            # ), f"web_read_group_unity fail assert: {scenario['name']}\n{old_groups}\nVS\n{new_groups}"

            if i == 0:
                print(
                    f"{scenario['name']} : {sum(1 for group in new_groups if '__records' in group)} groups open"
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
            (
                "Uni Union All",
                partial(new_way, "web_read_group_unity_union_all_simple", scenario),
            ),
            # ("Uni CTE", partial(new_way, "web_read_group_unity_cte", scenario)),
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


# For Open CRM - Kanban - Filter: default (none) - all open lead are loaded:
#         Old            > User time:   2530.209 +-   12.000 ms | Worker time:   5010.181 +-   45.391 ms
#         Old (Fixed)    > User time:   2266.833 +-   41.837 ms | Worker time:   3936.705 +-   25.431 ms
#         Uni Trivial    > User time:   2060.021 +-   76.349 ms | Worker time:   2058.456 +-   76.340 ms
#         Uni Union All  > User time:   2046.427 +-    3.459 ms | Worker time:   2043.932 +-    4.471 ms
# For Open CRM - Kanban - Filter: Creation Date = 2025 - Groupby month:
#         Old            > User time:   1557.907 +-   29.301 ms | Worker time:   4436.593 +-   58.773 ms
#         Old (Fixed)    > User time:   1291.402 +-  126.249 ms | Worker time:   3221.706 +-  558.178 ms
#         Uni Trivial    > User time:   1077.290 +-   19.584 ms | Worker time:   1075.670 +-   19.544 ms
#         Uni Union All  > User time:   1062.081 +-   44.808 ms | Worker time:   1057.531 +-   47.361 ms
# For Open CRM - Kanban - Filter: default (none) - groupby lang_code (related field):
#         Old            > User time:   4148.675 +-   32.936 ms | Worker time:  11637.274 +-   48.319 ms
#         Old (Fixed)    > User time:   3375.362 +-   22.794 ms | Worker time:   6154.320 +-   59.297 ms
#         Uni Trivial    > User time:   4023.565 +-   43.378 ms | Worker time:   4004.749 +-   42.077 ms
#         Uni Union All  > User time:   3960.726 +-   65.375 ms | Worker time:   3938.327 +-   65.874 ms
# For Open CRM - Kanban - Filter : search 'test' (default groupby):
#         Old            > User time:   5176.144 +-   41.047 ms | Worker time:  12321.979 +-   87.120 ms
#         Old (Fixed)    > User time:   4380.720 +-   18.591 ms | Worker time:   7884.931 +-   52.821 ms
#         Uni Trivial    > User time:   5924.002 +-   20.356 ms | Worker time:   5921.230 +-   20.979 ms
#         Uni Union All  > User time:   6300.816 +-   43.286 ms | Worker time:   6297.560 +-   46.472 ms
# For Open CRM - Kanban - Filter My Pipeline with (VIDH) as user:
#         Old            > User time:    345.941 +-    6.772 ms | Worker time:   1367.914 +-   62.801 ms
#         Old (Fixed)    > User time:    357.179 +-   12.521 ms | Worker time:   1437.534 +-   37.525 ms
#         Uni Trivial    > User time:    203.310 +-    8.037 ms | Worker time:    202.200 +-    8.050 ms
#         Uni Union All  > User time:    200.757 +-    2.924 ms | Worker time:    199.692 +-    2.918 ms
# For Open Framework Python project - No filters:
#         Old            > User time:    371.581 +-   13.179 ms | Worker time:   1009.312 +-   11.700 ms
#         Old (Fixed)    > User time:    357.443 +-    9.444 ms | Worker time:    987.150 +-   26.122 ms
#         Uni Trivial    > User time:    239.191 +-   22.793 ms | Worker time:    238.332 +-   22.827 ms
#         Uni Union All  > User time:    243.072 +-   15.329 ms | Worker time:    242.177 +-   15.342 ms
# For Kanban: Open Help project - No filter:
#         Old            > User time:    550.676 +-   14.584 ms | Worker time:   1658.978 +-   18.790 ms
#         Old (Fixed)    > User time:    538.790 +-   10.594 ms | Worker time:   1619.316 +-   25.288 ms
#         Uni Trivial    > User time:    469.783 +-   13.833 ms | Worker time:    468.593 +-   14.000 ms
#         Uni Union All  > User time:    473.537 +-   36.971 ms | Worker time:    472.327 +-   37.117 ms
# For Kanban: Open Help project - Search 'bve)' on Assignees:
#         Old            > User time:    427.892 +-   13.071 ms | Worker time:   1261.133 +-   30.862 ms
#         Old (Fixed)    > User time:    437.571 +-    8.310 ms | Worker time:   1278.440 +-   19.966 ms
#         Uni Trivial    > User time:    291.869 +-   13.975 ms | Worker time:    290.929 +-   14.002 ms
#         Uni Union All  > User time:    280.689 +-   15.320 ms | Worker time:    279.755 +-   15.350 ms