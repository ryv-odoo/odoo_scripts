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
    {
        "name": "Open CRM - Filter: default (none) - Groupby stage_id (default)",
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
    {
        "name": "Open CRM - Filter: Creation Date = 2025 - Groupby create_date:month",
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
    {
        "name": "Open CRM - Filter: default (none) - Groupby lang_code (related field)",
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
    {
        "name": "Open CRM - Filter: search 'test' - Groupby stage_id (default)",
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
    {
        "name": "Open CRM - Filter: My Pipeline with (VIDH) as user - Groupby stage_id (default)",
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
    {
        "name": "Open Project, Framework Python project - Default filter - Groupby stage_id (default)",
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
    {
        "name": "Open Project, Help project - Default filter - Groupby stage_id (default)",
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
    {
        "name": "Open Project, Help project - Search 'bve)' on Assignees - Groupby stage_id (default)",
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

            # new_groups, [delay_user, delay_worker] = new_way(
            #     "web_read_group_unity_union_all_simple", scenario
            # )
            # print(
            #     f"\tUni Union All> User time: {delay_user:10.3f} ms | Worker time: {delay_worker:10.3f} ms"
            # )

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
            nb_open_group = sum(1 for group in new_groups if '__records' in group and group['__records'])
            nb_opened_records = sum(len(group['__records']) for group in new_groups if '__records' in group)
            if i == 0:
                print(
                    f"{scenario['name']} : {nb_open_group} groups opened (with records) - {nb_opened_records} records opened"
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
            # (
            #     "Uni Union All",
            #     partial(new_way, "web_read_group_unity_union_all_simple", scenario),
            # ),
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

# Warmup Open CRM - Filter: default (none) - Groupby stage_id (default)
#         Uni Trivial> User time:   2161.406 ms | Worker time:   2158.350 ms
#         Old> User time:   2456.564 ms | Worker time:   5106.532 ms
#         Old (Fixed)> User time:   2304.593 ms | Worker time:   4476.674 ms
# Open CRM - Filter: default (none) - Groupby stage_id (default) : 10 groups opened (with records) - 325 records opened
# Warmup Open CRM - Filter: Creation Date = 2025 - Groupby create_date:month
#         Uni Trivial> User time:   1010.640 ms | Worker time:   1009.059 ms
#         Old> User time:   1475.492 ms | Worker time:   4580.188 ms
#         Old (Fixed)> User time:   1055.770 ms | Worker time:   2297.030 ms
# Open CRM - Filter: Creation Date = 2025 - Groupby create_date:month : 6 groups opened (with records) - 240 records opened
# Warmup Open CRM - Filter: default (none) - Groupby lang_code (related field)
#         Uni Trivial> User time:   4150.679 ms | Worker time:   4123.514 ms
#         Old> User time:   4075.101 ms | Worker time:  11277.912 ms
#         Old (Fixed)> User time:   3428.199 ms | Worker time:   6380.961 ms
# Open CRM - Filter: default (none) - Groupby lang_code (related field) : 10 groups opened (with records) - 361 records opened
# Warmup Open CRM - Filter: search 'test' - Groupby stage_id (default)
#         Uni Trivial> User time:   5948.272 ms | Worker time:   5946.725 ms
#         Old> User time:   5052.318 ms | Worker time:  12245.318 ms
#         Old (Fixed)> User time:   4426.610 ms | Worker time:   7881.384 ms
# Open CRM - Filter: search 'test' - Groupby stage_id (default) : 8 groups opened (with records) - 243 records opened
# Warmup Open CRM - Filter: My Pipeline with (VIDH) as user - Groupby stage_id (default)
#         Uni Trivial> User time:    204.376 ms | Worker time:    203.395 ms
#         Old> User time:    402.012 ms | Worker time:   1650.828 ms
#         Old (Fixed)> User time:    395.693 ms | Worker time:   1558.870 ms
# Open CRM - Filter: My Pipeline with (VIDH) as user - Groupby stage_id (default) : 6 groups opened (with records) - 134 records opened
# Warmup Open Project, Framework Python project - Default filter - Groupby stage_id (default)
#         Uni Trivial> User time:    279.400 ms | Worker time:    278.477 ms
#         Old> User time:    399.884 ms | Worker time:   1026.289 ms
#         Old (Fixed)> User time:    393.598 ms | Worker time:   1060.122 ms
# Open Project, Framework Python project - Default filter - Groupby stage_id (default) : 4 groups opened (with records) - 48 records opened
# Warmup Open Project, Help project - No filter - Groupby stage_id (default)
#         Uni Trivial> User time:    507.647 ms | Worker time:    506.521 ms
#         Old> User time:    594.415 ms | Worker time:   1744.452 ms
#         Old (Fixed)> User time:    544.303 ms | Worker time:   1647.522 ms
# Open Project, Help project - No filter - Groupby stage_id (default) : 5 groups opened (with records) - 100 records opened
# Warmup Open Project, Help project - Search 'bve)' on Assignees - Groupby stage_id (default)
#         Uni Trivial> User time:    314.923 ms | Worker time:    314.091 ms
#         Old> User time:    480.343 ms | Worker time:   1328.946 ms
#         Old (Fixed)> User time:    435.648 ms | Worker time:   1286.411 ms
# Open Project, Help project - Search 'bve)' on Assignees - Groupby stage_id (default) : 3 groups opened (with records) - 4 records opened
# Launching test
# For Open CRM - Filter: default (none) - Groupby stage_id (default):
#         Old            > User time:   2495.128 +-   57.020 ms | Worker time:   5071.780 +-   22.681 ms
#         Old (Fixed)    > User time:   2257.154 +-   49.056 ms | Worker time:   3993.602 +-  125.464 ms
#         Uni Trivial    > User time:   2109.417 +-   22.845 ms | Worker time:   2105.389 +-   26.134 ms
# For Open CRM - Filter: Creation Date = 2025 - Groupby create_date:month:
#         Old            > User time:   1489.222 +-   27.526 ms | Worker time:   4388.155 +-   47.539 ms
#         Old (Fixed)    > User time:   1075.068 +-   31.726 ms | Worker time:   2298.392 +-   17.080 ms
#         Uni Trivial    > User time:    990.718 +-   36.329 ms | Worker time:    989.092 +-   36.343 ms
# For Open CRM - Filter: default (none) - Groupby lang_code (related field):
#         Old            > User time:   4172.701 +-   15.953 ms | Worker time:  11317.637 +-   46.593 ms
#         Old (Fixed)    > User time:   3414.296 +-   42.615 ms | Worker time:   6208.338 +-   56.249 ms
#         Uni Trivial    > User time:   4062.431 +-   45.224 ms | Worker time:   4037.195 +-   48.154 ms
# For Open CRM - Filter: search 'test' - Groupby stage_id (default):
#         Old            > User time:   5059.894 +-   32.458 ms | Worker time:  12214.776 +-   66.766 ms
#         Old (Fixed)    > User time:   4378.451 +-   18.623 ms | Worker time:   7843.374 +-   89.574 ms
#         Uni Trivial    > User time:   5837.071 +-   13.466 ms | Worker time:   5833.765 +-   13.061 ms
# For Open CRM - Filter: My Pipeline with (VIDH) as user - Groupby stage_id (default):
#         Old            > User time:    354.559 +-   13.876 ms | Worker time:   1406.978 +-   50.031 ms
#         Old (Fixed)    > User time:    376.677 +-    4.262 ms | Worker time:   1492.995 +-   30.313 ms
#         Uni Trivial    > User time:    224.452 +-    5.006 ms | Worker time:    223.399 +-    5.009 ms
# For Open Project, Framework Python project - Default filter - Groupby stage_id (default):
#         Old            > User time:    370.968 +-    4.947 ms | Worker time:   1007.227 +-   24.079 ms
#         Old (Fixed)    > User time:    374.651 +-    5.025 ms | Worker time:    991.994 +-   20.477 ms
#         Uni Trivial    > User time:    271.404 +-   18.166 ms | Worker time:    270.508 +-   18.144 ms
# For Open Project, Help project - No filter - Groupby stage_id (default):
#         Old            > User time:    573.647 +-    3.087 ms | Worker time:   1693.442 +-   70.651 ms
#         Old (Fixed)    > User time:    531.486 +-   20.436 ms | Worker time:   1569.463 +-   27.046 ms
#         Uni Trivial    > User time:    506.271 +-    5.747 ms | Worker time:    505.207 +-    5.708 ms
# For Open Project, Help project - Search 'bve)' on Assignees - Groupby stage_id (default):
#         Old            > User time:    433.501 +-   15.176 ms | Worker time:   1280.144 +-    7.425 ms
#         Old (Fixed)    > User time:    447.778 +-    5.673 ms | Worker time:   1283.168 +-    7.129 ms
#         Uni Trivial    > User time:    312.172 +-    3.624 ms | Worker time:    311.323 +-    3.566 ms
