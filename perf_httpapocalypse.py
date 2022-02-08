import pickle
import subprocess
import re
import sys
from itertools import product
from statistics import NormalDist
from time import sleep, time
from os import path

import grequests

from misc import BOLD, RESET, remove_outliers, GREEN, RED

URI = "http://127.0.0.1:8069"
NB_TODO = 2_000
FILE_RESULT = 'result_http.obj'

# SERVER ATTRIBUTE
WORKERS_NB = [
    None, # None = multi-thread mode
    # 3,
    7,
]
MODULE_INSTALL = {  # module install -> db_name (should already installed)
    'test_http': 'base_db',
    'website_event,website_crm,website_blog,website_forum,website_sale,test_http': 'all_db',
}

# REQUEST ATTRIBUTE
AUTHENTICATIONS_URL = {
    'nodb': '/test_http/greeting',
    'user': '/test_http/greeting-user',
    'public_website': '/',
    # 'user': '',
}
SESSION = [  # % of request with a session already present
    # 0,
    # 80,
    100,
]
PARALLELE_REQUEST = [
    1,
    7,
    # 20,
]


def perf_execution(to_save):
    res = {}
    for worker_nb, (module_install, db) in product(WORKERS_NB, MODULE_INSTALL.items()):
        # Launch server
        logger = f'log_perf_{db}_{worker_nb}.log'
        cmd = [
            "./odoo/odoo-bin",
            "--addons-path",
            "./odoo/addons,./enterprise",
            "--logfile",
            logger,
            "-d", db
        ]
        if worker_nb:
            cmd.append("--workers")
            cmd.append(str(worker_nb))
        print("Launch command:", cmd)

        try:
            proc = subprocess.Popen(cmd)
            # print("Sleep to let the server to start-up")
            sleep(1)

            response = grequests.map([grequests.AsyncRequest('GET', URI + '/web/login')])
            session = response[0].cookies['session_id']
            csrf = re.search(r'csrf_token: "(\w+)"', response[0].text).group(1)
            assert csrf
            cookies = {'session_id': session}
            response = grequests.map([grequests.AsyncRequest('POST', URI + '/web/login', cookies=cookies, params={
                'login': 'admin', 'password': 'admin', 'csrf_token': csrf, 'db': db
            })])
            session_auth = response[0].cookies['session_id']
            assert response[0].status_code == 200

            for (auth, url), session_nb, para_req in product(AUTHENTICATIONS_URL.items(), SESSION, PARALLELE_REQUEST):
                if 'website' in auth and 'website' not in module_install:
                    continue

                _ = grequests.map([grequests.AsyncRequest('GET', URI + url)] * 100)

                requests = []
                for i in range(NB_TODO):
                    cookies = {}
                    if i % 100 < session_nb:
                        cookies['session_id'] = session_auth
                    if 'user' in auth:
                        cookies['session_id'] = session_auth
                    requests.append(grequests.AsyncRequest('GET', URI + url, cookies=cookies))

                s = time()
                responses = grequests.map(requests, size=para_req)
                end = (time() - s) * 1000

                for r in responses:
                    assert r.status_code == 200, f"{r.status_code}: {r.text}\n RESULT FOR {auth} {url} with {session_nb}% session set and {para_req} // requests"

                values = [response.elapsed.microseconds / 1000.0 for response in responses]
                # values = x_bests(values, int(NB_TODO * 0.95))
                print(f"RESULT FOR {auth} {url} with {session_nb}% session set and {para_req} // requests: ")
                print(f"\t Total time: {end:5.3f} ms for {len(values)} requests")
                print(f"\t Total time / nb request: mean {BOLD}{(end / len(values)):5.3f}{RESET} ms")
                res[(db, worker_nb, url, session_nb, para_req)] = (values, end)
                values = remove_outliers(values)
                n = NormalDist.from_samples(values)
                print(f"\t Time per request (after removing outliers): {(n.mean):2.3f} ms +- {n.stdev:2.3f} ms ({len(values)}) by request")
                # print(values[:100])

        finally:
            print("Terminate")
            proc.terminate()
        sleep(1)

    if path.isfile(FILE_RESULT):
        with open(FILE_RESULT, 'rb') as fr:
            all_result: dict = pickle.load(fr)
            all_result.update({to_save: res})
    else:
        all_result = {to_save: res}

    if all_result:
        with open(FILE_RESULT, 'wb') as fw:
            print("Save result")
            pickle.dump(all_result, fw)

def compare_result(before, after):
    with open(FILE_RESULT, 'rb') as fr:
        all_result: dict = pickle.load(fr)
        print("Result contains these keys : ", list(all_result))
        before_res = all_result[before]
        after_res = all_result[after]
        better_nb = 0 
        all_nb = 0
        for key in before_res:
            if key not in after_res:
                continue
            all_nb += 1
            before_values, before_time = before_res[key]
            after_values, after_time = after_res[key]
            print(f"\n--------------- FOR {key} (db, worker, url, % session set, parallel request)")
            print("Total time:")
            color = RED if before_time < after_time else GREEN
            print(f"\t{before} {before_time} ms for {len(before_values)}")
            print(f"\t{after} {color}{after_time}{RESET} ms for {len(after_values)}")

            print("Total time / nb request:")
            color = RED if (before_time / len(before_values)) < (after_time / len(after_values)) else GREEN
            print(f"\t{before} {before_time / len(before_values):.3f} ms by request in average")
            print(f"\t{after} {color}{after_time / len(after_values):.3f}{RESET} ms by request in average")
            if (before_time / len(before_values)) > (after_time / len(after_values)):
                better_nb += 1

            n_before = NormalDist.from_samples(remove_outliers(before_values))
            n_after = NormalDist.from_samples(remove_outliers(after_values))
            print("Time per request (after removing outliers):")
            color = RESET
            if (n_after.overlap(n_before)) < 0.05:
                if n_after.mean < n_before.mean:
                    color = GREEN
                else:
                    color = RED
            print(f"\t{before} {n_before.mean:.3f} ms +- {n_before.stdev:.3f} ms")
            print(f"\t{after} {color}{n_after.mean:.3f}{RESET} ms +- {n_after.stdev:.3f} ms")
        print(f"In {better_nb}/{all_nb} {after} do better than {before}")

if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print("No args, EXIT")

    TO_SAVE = sys.argv[1]
    if TO_SAVE == 'compare':
        compare_result(sys.argv[2], sys.argv[3])
    else:
        perf_execution(TO_SAVE)
