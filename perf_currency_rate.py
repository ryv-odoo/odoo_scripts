import random
import datetime

from itertools import product

from dateutil.relativedelta import relativedelta

# from faker import Faker

# fake = Faker()

# faker -r=1000 -s=',' name email ean8 vat

currencies_ids = list(range(1, 8))
company_ids = list(range(1, 10)) + ["NULL"]
# +- 10 years of data
days = [datetime.date.today()]
for __ in range(10 * 365):
    days.append(days[-1] - relativedelta(days=1))

# \copy res_currency_rate(currency_id, name, company_id, rate) FROM '/home/odoo/Documents/dev/odoo_scripts/currency_rate.csv' (FORMAT csv, DELIMITER ',', NULL 'NULL');
with open("currency_rate.csv", "wt") as f:
    for currency_id, company_id, date in product(currencies_ids, company_ids, days):
        rate = random.random() * 10
        line = ",".join([str(currency_id), str(date), str(company_id), str(rate)])
        f.write(f"{line}\n")

""" CREATE UNIQUE INDEX test_cur ON res_currency_rate (currency_id, company_id, name DESC) NULLS NOT DISTINCT """


# Current solution without gettind date of rate
"""
SELECT
    "res_currency"."id",
    COALESCE(
        (
            SELECT "res_currency_rate"."rate"
            FROM "res_currency_rate"
            WHERE
                (
                    ("res_currency_rate"."company_id" IN (1) OR "res_currency_rate"."company_id" IS NULL)
                    AND "res_currency_rate"."name" <= '2025-09-02'::date
                )
                AND "res_currency_rate"."currency_id" = "res_currency"."id"
            ORDER BY
                "res_currency_rate"."company_id",
                "res_currency_rate"."name" DESC
            LIMIT
                1
        ), (
            SELECT
                "res_currency_rate"."rate"
            FROM
                "res_currency_rate"
            WHERE
                (
                    "res_currency_rate"."company_id" IN (1)
                    OR "res_currency_rate"."company_id" IS NULL
                )
                AND "res_currency_rate"."currency_id" = "res_currency"."id"
            ORDER BY
                "res_currency_rate"."company_id",
                "res_currency_rate"."name" ASC
            LIMIT
                1
        ), 1.0
    )
FROM
    "res_currency"
WHERE "res_currency"."id" IN %s
"""

""" 10 currencies
 Index Only Scan using res_currency_pkey on res_currency  (cost=0.14..24132.82 rows=7 width=36) (actual time=7.065..19.959 rows=7 loops=1)
   Index Cond: (id = ANY ('{4,5,3,2,6,8,1}'::integer[]))
   Heap Fetches: 7
   SubPlan 1
     ->  Limit  (cost=1768.76..1768.76 rows=1 width=20) (actual time=2.845..2.845 rows=1 loops=7)
           ->  Sort  (cost=1768.76..1772.05 rows=1317 width=20) (actual time=2.844..2.844 rows=1 loops=7)
                 Sort Key: res_currency_rate.company_id, res_currency_rate.name DESC
                 Sort Method: quicksort  Memory: 25kB
                 ->  Index Scan using res_currency_rate__currency_id_index on res_currency_rate  (cost=0.42..1762.17 rows=1317 width=20) (actual time=0.005..2.221 rows=6259 loops=7)
                       Index Cond: (currency_id = res_currency.id)
                       Filter: (((company_id = 1) OR (company_id IS NULL)) AND (name <= '2025-10-06'::date) AND ((company_id = 1) OR (company_id IS NULL)))
                       Rows Removed by Filter: 25035
   SubPlan 2
     ->  Limit  (cost=1677.48..1677.48 rows=1 width=20) (actual time=0.003..0.003 rows=0 loops=1)
           ->  Sort  (cost=1677.48..1680.77 rows=1317 width=20) (actual time=0.003..0.003 rows=0 loops=1)
                 Sort Key: res_currency_rate_1.company_id, res_currency_rate_1.name
                 Sort Method: quicksort  Memory: 25kB
                 ->  Index Scan using res_currency_rate__currency_id_index on res_currency_rate res_currency_rate_1  (cost=0.42..1670.89 rows=1317 width=20) (actual time=0.001..0.001 rows=0 loops=1)
                       Index Cond: (currency_id = res_currency.id)
                       Filter: (((company_id = 1) OR (company_id IS NULL)) AND ((company_id = 1) OR (company_id IS NULL)))
 Planning Time: 0.418 ms
 Execution Time: 20.002 ms
(22 rows)
"""

""" 2 currencies
 Index Only Scan using res_currency_pkey on res_currency  (cost=0.14..6900.81 rows=2 width=36) (actual time=7.319..9.923 rows=2 loops=1)
   Index Cond: (id = ANY ('{4,1}'::integer[]))
   Heap Fetches: 2
   SubPlan 1
     ->  Limit  (cost=1768.76..1768.76 rows=1 width=20) (actual time=4.946..4.947 rows=1 loops=2)
           ->  Sort  (cost=1768.76..1772.05 rows=1317 width=20) (actual time=4.945..4.945 rows=1 loops=2)
                 Sort Key: res_currency_rate.company_id, res_currency_rate.name DESC
                 Sort Method: top-N heapsort  Memory: 25kB
                 ->  Index Scan using res_currency_rate__currency_id_index on res_currency_rate  (cost=0.42..1762.17 rows=1317 width=20) (actual time=0.012..3.825 rows=7302 loops=2)
                       Index Cond: (currency_id = res_currency.id)
                       Filter: (((company_id = 1) OR (company_id IS NULL)) AND (name <= '2025-10-06'::date) AND ((company_id = 1) OR (company_id IS NULL)))
                       Rows Removed by Filter: 29208
   SubPlan 2
     ->  Limit  (cost=1677.48..1677.48 rows=1 width=20) (never executed)
           ->  Sort  (cost=1677.48..1680.77 rows=1317 width=20) (never executed)
                 Sort Key: res_currency_rate_1.company_id, res_currency_rate_1.name
                 ->  Index Scan using res_currency_rate__currency_id_index on res_currency_rate res_currency_rate_1  (cost=0.42..1670.89 rows=1317 width=20) (never executed)
                       Index Cond: (currency_id = res_currency.id)
                       Filter: (((company_id = 1) OR (company_id IS NULL)) AND ((company_id = 1) OR (company_id IS NULL)))
 Planning Time: 0.427 ms
 Execution Time: 9.969 ms
(21 rows)
"""

# Solution use for left join
"""
SELECT DISTINCT ON ("res_currency_rate"."currency_id") 
    "res_currency_rate"."currency_id", "res_currency_rate"."rate"
FROM "res_currency_rate"
WHERE ("res_currency_rate"."company_id" IS NULL OR "res_currency_rate"."company_id" = 1) 
AND "res_currency_rate"."currency_id" IN %s
ORDER BY
    "res_currency_rate"."currency_id",
    "res_currency_rate"."company_id",
    CASE WHEN "res_currency_rate"."name" <= '2025-09-02'::date THEN "res_currency_rate"."name" END DESC,
    CASE WHEN "res_currency_rate"."name" > '2025-09-02'::date THEN "res_currency_rate"."name" END ASC
"""

"""
 Unique  (cost=1697.99..12509.19 rows=7 width=28) (actual time=7.591..25.273 rows=6 loops=1)
   ->  Incremental Sort  (cost=1697.99..12404.92 rows=41710 width=28) (actual time=7.590..24.304 rows=43812 loops=1)
         Sort Key: currency_id, company_id, (CASE WHEN (name <= '2025-09-02'::date) THEN name ELSE NULL::date END) DESC, (CASE WHEN (name > '2025-09-02'::date) THEN name ELSE NULL::date END)
         Presorted Key: currency_id
         Full-sort Groups: 6  Sort Method: quicksort  Average Memory: 28kB  Peak Memory: 28kB
         Pre-sorted Groups: 6  Sort Method: quicksort  Average Memory: 561kB  Peak Memory: 561kB
         ->  Index Scan using res_currency_rate__currency_id_index on res_currency_rate  (cost=0.42..9268.03 rows=41710 width=28) (actual time=0.040..14.706 rows=43812 loops=1)
               Index Cond: (currency_id = ANY ('{4,5,3,2,6,8,1}'::integer[]))
               Filter: ((company_id IS NULL) OR (company_id = 1))
               Rows Removed by Filter: 175248
 Planning Time: 0.218 ms
 Execution Time: 25.322 ms
"""

"""
 Unique  (cost=558.49..4113.84 rows=7 width=28) (actual time=14.670..23.277 rows=2 loops=1)
   ->  Incremental Sort  (cost=558.49..4079.37 rows=13786 width=28) (actual time=14.668..22.420 rows=14604 loops=1)
         Sort Key: currency_id, company_id, (CASE WHEN (name <= '2025-09-02'::date) THEN name ELSE NULL::date END) DESC, (CASE WHEN (name > '2025-09-02'::date) THEN name ELSE NULL::date END)
         Presorted Key: currency_id
         Full-sort Groups: 2  Sort Method: quicksort  Average Memory: 28kB  Peak Memory: 28kB
         Pre-sorted Groups: 2  Sort Method: quicksort  Average Memory: 561kB  Peak Memory: 561kB
         ->  Index Scan using res_currency_rate__currency_id_index on res_currency_rate  (cost=0.42..3152.57 rows=13786 width=28) (actual time=0.038..13.422 rows=14604 loops=1)
               Index Cond: (currency_id = ANY ('{4,1}'::integer[]))
               Filter: ((company_id IS NULL) OR (company_id = 1))
               Rows Removed by Filter: 58416
 Planning Time: 0.237 ms
 Execution Time: 23.334 ms
"""

"""
SELECT DISTINCT ON ("res_currency_rate"."currency_id")
    "res_currency_rate"."currency_id", "res_currency_rate"."rate"
FROM "res_currency_rate"
WHERE ("res_currency_rate"."company_id" IS NULL OR "res_currency_rate"."company_id" = 1)
AND "res_currency_rate"."currency_id" IN %s
ORDER BY
    "res_currency_rate"."currency_id",
    "res_currency_rate"."company_id",
    "res_currency_rate"."name" DESC;
"""


