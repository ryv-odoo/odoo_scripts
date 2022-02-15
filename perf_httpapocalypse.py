import pickle
import subprocess
import re
import sys
from itertools import product
from statistics import NormalDist
from time import sleep, time
from os import path

import matplotlib.pyplot as plt
import grequests

COLOR = True
if COLOR:
    from misc import BOLD, GREEN, RED, RESET
else:
    BOLD, GREEN, RED, RESET = [""] * 4

from misc import remove_outliers, x_bests

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
    'nodb': '/test_http/greeting-none',
    'user': '/test_http/greeting-user',
    'public_website': '/',  # You should modified index and return directly
    # 'user': '',
}
SESSION = [  # % of request with a session already present
    0,
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
            session = response[0].cookies.get('session_id', session)
            assert response[0].status_code == 200

            for (auth, url), session_nb, para_req in product(AUTHENTICATIONS_URL.items(), SESSION, PARALLELE_REQUEST):
                if 'website' in auth and 'website' not in module_install:
                    continue
                if 'user' in auth and session_nb < 100.0:
                    continue

                cookies = {'session_id': session}
                _ = grequests.map([grequests.AsyncRequest('GET', URI + url, cookies=cookies, allow_redirects=False)] * int(NB_TODO / 4), size=para_req)

                requests = []
                for i in range(NB_TODO):
                    cookies = {}
                    if i % 100 < session_nb:
                        cookies['session_id'] = session
                    if 'user' in auth:
                        cookies['session_id'] = session
                    requests.append(grequests.AsyncRequest('GET', URI + url, cookies=cookies, allow_redirects=False))

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

def compare_graph(before, after):
    with open(FILE_RESULT, 'rb') as fr:
        all_result: dict = pickle.load(fr)
        before_res = all_result[before]
        after_res = all_result[after]

        labels = []
        total_mean_before = []
        mean_before = []
        median_before = []
        total_mean_after = []
        mean_after = []
        median_after = []
        for key in before_res:
            if key not in after_res:
                continue
            db, worker_nb, url, session_nb, para_req = key
            if 'user' in url and session_nb < 100.0:
                continue
            before_values, before_time = before_res[key]
            after_values, after_time = after_res[key]
            label = [
                url,
                'base' if db == 'base_db' else 'website',
                'Multi-Threading' if worker_nb is None else f'Multi-Worker ({worker_nb})',
                'Sequential requests' if para_req == 1 else f'Parallel requests ({para_req})',
                'Without session' if session_nb == 0 else 'With session',
            ]
            labels.append('\n'.join(label))
            total_mean_before.append(before_time / len(before_values))
            total_mean_after.append(after_time / len(after_values))

            n_before = NormalDist.from_samples(before_values)
            n_after = NormalDist.from_samples(after_values)
            mean_before.append(n_before.mean)
            median_before.append(n_before.median)
            mean_after.append(n_after.mean)
            median_after.append(n_after.median)


        width = 0.40
        x_before = list(i - width / 2 for i in range(len(labels)))
        x_after = list(i + width / 2 for i in range(len(labels)))

        fig, ax = plt.subplots()

        rects1 = ax.bar(x_before, total_mean_before, width, label='master')
        rects2 = ax.bar(x_after, total_mean_after, width, label='httpocalypse')

        ax.set_ylabel('Times (ms)')
        ax.set_title('Master vs Httpocalypse Benchmark (Total time / nb request)')
        ax.set_xticks(range(len(labels)), labels, size='x-small')
        ax.legend()

        ax.bar_label(rects1, fmt='%.3f', padding=3)
        ax.bar_label(rects2, fmt='%.3f', padding=3)

        fig.set_size_inches((50, 10), forward=False)
        plt.tight_layout(pad=1, w_pad=1)
        plt.savefig('http_total.png', dpi=400)

        fig, ax = plt.subplots()

        rects1 = ax.bar(x_before, mean_before, width, label='master')
        rects2 = ax.bar(x_after, mean_after, width, label='httpocalypse')

        ax.set_ylabel('Times (ms)')
        ax.set_title('Master vs Httpocalypse Benchmark (Mean request)')
        ax.set_xticks(range(len(labels)), labels, size='x-small')
        ax.legend()

        ax.bar_label(rects1, fmt='%.3f', padding=3)
        ax.bar_label(rects2, fmt='%.3f', padding=3)

        fig.set_size_inches((50, 10), forward=False)
        plt.tight_layout(pad=1, w_pad=1)
        plt.savefig('http_mean.png', dpi=400)


def compare_result(before, after):
    KEYS_NAME = ("db", "worker", "url", "% session set", "parallel request")
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
            if 'user' in key[2] and key[3] < 100.0:
                continue
            all_nb += 1
            before_values, before_time = before_res[key]
            after_values, after_time = after_res[key]
            print(f"\n--------------- FOR {', '.join(f'{k1}: {k2}' for k1, k2 in zip(KEYS_NAME, key))}")
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


USAGE = f"""\
Benchmark the Odoo HTTP layer. First command generates a pickle file
<filename> in the working directory. Second command compares two
pickle files.

usage:
  {__file__} <filename>
  {__file__} compare <filename> <filename>
"""

if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print(USAGE)
        exit(-1)
    if sys.argv[1] == 'compare' and len(sys.argv) <= 3:
        print(USAGE)
        exit(-1)

    if sys.argv[1] == 'compare':
        compare_graph(sys.argv[2], sys.argv[3])
        # compare_result(sys.argv[2], sys.argv[3])
    else:
        perf_execution(sys.argv[1])
