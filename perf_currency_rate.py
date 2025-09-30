import random
import datetime

from itertools import product, cycle

from faker import Faker

fake = Faker()

# faker -r=1000 -s=',' name email ean8 vat

currencies_ids = list(range(1, 8))
company_ids = list(range(1, 10))

iter_currencies_company = cycle(product(currencies_ids, company_ids))

today = datetime.date.today()

# TODO

with open("currency_rate.csv", "wt") as f:
    for i in range(100_000):

        currency_id = next(currency_iter)

        date 

        line = ",".join([currency_id, date, company_id])
        f.write(f"{line}\n")


"""

SELECT DISTINCT ON ("res_currency_rate"."currency_id") 
    "res_currency_rate"."currency_id", "res_currency_rate"."rate"
FROM "res_currency_rate"
WHERE "res_currency_rate"."company_id" IS NULL OR "res_currency_rate"."company_id" = 1
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
WHERE "res_currency" = 10
"""
