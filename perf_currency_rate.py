import random
import datetime

from itertools import product

from dateutil.relativedelta import relativedelta

# from faker import Faker

# fake = Faker()

# faker -r=1000 -s=',' name email ean8 vat

currencies_ids = list(range(1, 8))
company_ids = list(range(1, 10)) + ['NULL']
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

"""

SELECT DISTINCT ON ("res_currency_rate"."currency_id") 
    "res_currency_rate"."currency_id", "res_currency_rate"."rate"
FROM "res_currency_rate"
WHERE ("res_currency_rate"."company_id" IS NULL OR "res_currency_rate"."company_id" = 1) 
AND "res_currency_rate"."currency_id" = 5
ORDER BY
    "res_currency_rate"."currency_id",
    "res_currency_rate"."company_id",
    CASE WHEN "res_currency_rate"."name" <= '2025-09-02'::date THEN "res_currency_rate"."name" END DESC,
    CASE WHEN "res_currency_rate"."name" > '2025-09-02'::date THEN "res_currency_rate"."name" END ASC

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
WHERE "res_currency"."id" = 5
"""
