

import ast
from collections import defaultdict
import re
import psycopg2

inverse_line_r = re.compile(r"Inverse selection of (.+)\(.*\) / (.+): NOT IN \{(.+)\} -> IN (.+)")
query_line = re.compile(r"\<osv\.Query: '(.+)' with params: (.+)\>")
select_re = re.compile(r'SELECT "(.+)".+')

model = field = prev = None
queries = defaultdict(list)


def read_file(f):
    for line in f:
        if (m := inverse_line_r.match(line)):
            model, field, prev, new = m.group(1), m.group(2), m.group(3), m.group(4)
            prev = ast.literal_eval('(' + prev + ')')
            new = tuple(ast.literal_eval(new))
            new = tuple(None if p is False else p for p in new)
        if (m := query_line.match(line)):
            query, params = m.group(1), ast.literal_eval(m.group(2))

            assert model
            key = (query, model, field, prev, new)
            # assert model == query.match()
            queries[key].append(params)

with open('../install_test.log', 'rt', encoding='utf_8') as f:
    read_file(f)

with open('../post_test.log', 'rt', encoding='utf_8') as f:
    read_file(f)

print(len(queries))

# CONNECTION_PARAMS = "dbname=master"

# with psycopg2.connect(CONNECTION_PARAMS) as conn:
#     with conn.cursor() as cur:

for (query, model, field, prev_sel, new_sel), params_list in queries.items():
    table_model = model.replace('.', '_')
    if f'"{table_model}"."{field}" in ' in query:
        old_query = query.replace(f'"{table_model}"."{field}" in ', f'"{table_model}"."{field}" not in ')
    else:
        old_query = query.replace('AND FALSE)', f'"{table_model}"."{field}" not in ')


    for params in params_list:
        old_params = [param if param != new_sel else prev_sel for param in params]
        print(old_query)
        print(old_params)
        print(query)
        print(params)
        print()
        assert old_params != params
        break


    assert query != old_query
    # print(query)
    # print()

# print("\n\n".join(f"{s} : {a}" for s, a in queries.items()))



