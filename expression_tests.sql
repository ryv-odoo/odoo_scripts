-- AND CONDITION - Normal
-- ALL as the same query plan.....
SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
WHERE
    "voip_phonecall"."date_deadline" <= '2023-09-12'
    AND (
        "voip_phonecall"."activity_id" in (
            SELECT
                "mail_activity".id
            FROM
                "mail_activity"
            WHERE
                "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
                AND "mail_activity"."res_model_id" = 401
        )
    )
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id";
--   Sort  (cost=52.30..52.30 rows=1 width=8) (actual time=0.100..0.105 rows=3 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Hash Join  (cost=38.68..52.29 rows=1 width=8) (actual time=0.079..0.091 rows=3 loops=1)
--          Hash Cond: (voip_phonecall.activity_id = mail_activity.id)
--          ->  Seq Scan on voip_phonecall  (cost=0.00..13.38 rows=90 width=12) (actual time=0.018..0.024 rows=6 loops=1)
--                Filter: (date_deadline <= '2023-09-12'::date)
--          ->  Hash  (cost=38.61..38.61 rows=5 width=4) (actual time=0.049..0.050 rows=3 loops=1)
--                Buckets: 1024  Batches: 1  Memory Usage: 9kB
--                ->  Bitmap Heap Scan on mail_activity  (cost=21.45..38.61 rows=5 width=4) (actual time=0.040..0.043 rows=3 loops=1)
--                      Recheck Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                      Filter: (res_model_id = 401)
--                      Heap Blocks: exact=1
--                      ->  Bitmap Index Scan on mail_activity_res_id_index  (cost=0.00..21.45 rows=5 width=0) (actual time=0.031..0.032 rows=3 loops=1)
--                            Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--  Planning Time: 0.497 ms
--  Execution Time: 0.230 ms

SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
WHERE
    "voip_phonecall"."date_deadline" <= '2023-09-12'
    AND EXISTS (
        SELECT
        FROM
            "mail_activity"
        WHERE
            "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
            AND "mail_activity"."res_model_id" = 401
            AND "voip_phonecall"."activity_id" = "mail_activity"."id"
    )
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id";
--  Sort  (cost=52.30..52.30 rows=1 width=8) (actual time=0.036..0.038 rows=3 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Hash Join  (cost=38.68..52.29 rows=1 width=8) (actual time=0.029..0.033 rows=3 loops=1)
--          Hash Cond: (voip_phonecall.activity_id = mail_activity.id)
--          ->  Seq Scan on voip_phonecall  (cost=0.00..13.38 rows=90 width=12) (actual time=0.007..0.009 rows=6 loops=1)
--                Filter: (date_deadline <= '2023-09-12'::date)
--          ->  Hash  (cost=38.61..38.61 rows=5 width=4) (actual time=0.018..0.019 rows=3 loops=1)
--                Buckets: 1024  Batches: 1  Memory Usage: 9kB
--                ->  Bitmap Heap Scan on mail_activity  (cost=21.45..38.61 rows=5 width=4) (actual time=0.015..0.016 rows=3 loops=1)
--                      Recheck Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                      Filter: (res_model_id = 401)
--                      Heap Blocks: exact=1
--                      ->  Bitmap Index Scan on mail_activity_res_id_index  (cost=0.00..21.45 rows=5 width=0) (actual time=0.011..0.012 rows=3 loops=1)
--                            Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--  Planning Time: 0.172 ms
--  Execution Time: 0.064 ms

SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
    LEFT JOIN "mail_activity" ON (
        "mail_activity".id = "voip_phonecall"."activity_id"
    )
WHERE
    "voip_phonecall"."date_deadline" <= '2023-09-12'
    AND (
        "mail_activity".id IS NOT NULL
        AND "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
        AND "mail_activity"."res_model_id" = 401
    )
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id";
--  Sort  (cost=52.30..52.30 rows=1 width=8) (actual time=0.101..0.105 rows=3 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Hash Join  (cost=38.68..52.29 rows=1 width=8) (actual time=0.080..0.091 rows=3 loops=1)
--          Hash Cond: (voip_phonecall.activity_id = mail_activity.id)
--          ->  Seq Scan on voip_phonecall  (cost=0.00..13.38 rows=90 width=12) (actual time=0.018..0.024 rows=6 loops=1)
--                Filter: (date_deadline <= '2023-09-12'::date)
--          ->  Hash  (cost=38.61..38.61 rows=5 width=4) (actual time=0.049..0.051 rows=3 loops=1)
--                Buckets: 1024  Batches: 1  Memory Usage: 9kB
--                ->  Bitmap Heap Scan on mail_activity  (cost=21.45..38.61 rows=5 width=4) (actual time=0.040..0.043 rows=3 loops=1)
--                      Recheck Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                      Filter: ((id IS NOT NULL) AND (res_model_id = 401))
--                      Heap Blocks: exact=1
--                      ->  Bitmap Index Scan on mail_activity_res_id_index  (cost=0.00..21.45 rows=5 width=0) (actual time=0.031..0.031 rows=3 loops=1)
--                            Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--  Planning Time: 0.469 ms
--  Execution Time: 0.181 ms

SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
    LEFT JOIN "mail_activity" ON (
        "mail_activity".id = "voip_phonecall"."activity_id"
        AND "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
        AND "mail_activity"."res_model_id" = 401
    )
WHERE
    "voip_phonecall"."date_deadline" <= '2023-09-12'
    AND "mail_activity".id IS NOT NULL
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id"
--   Sort  (cost=52.30..52.30 rows=1 width=8) (actual time=0.100..0.104 rows=3 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Hash Join  (cost=38.68..52.29 rows=1 width=8) (actual time=0.078..0.091 rows=3 loops=1)
--          Hash Cond: (voip_phonecall.activity_id = mail_activity.id)
--          ->  Seq Scan on voip_phonecall  (cost=0.00..13.38 rows=90 width=12) (actual time=0.018..0.024 rows=6 loops=1)
--                Filter: (date_deadline <= '2023-09-12'::date)
--          ->  Hash  (cost=38.61..38.61 rows=5 width=4) (actual time=0.049..0.051 rows=3 loops=1)
--                Buckets: 1024  Batches: 1  Memory Usage: 9kB
--                ->  Bitmap Heap Scan on mail_activity  (cost=21.45..38.61 rows=5 width=4) (actual time=0.040..0.044 rows=3 loops=1)
--                      Recheck Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                      Filter: ((id IS NOT NULL) AND (res_model_id = 401))
--                      Heap Blocks: exact=1
--                      ->  Bitmap Index Scan on mail_activity_res_id_index  (cost=0.00..21.45 rows=5 width=0) (actual time=0.031..0.031 rows=3 loops=1)
--                            Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--  Planning Time: 0.469 ms
--  Execution Time: 0.181 ms


-- AND CONDITION - NOT CONDITION
SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
WHERE
    "voip_phonecall"."date_deadline" <= '2023-09-12'
    AND (
        "voip_phonecall"."activity_id" NOT in (
            SELECT
                "mail_activity".id
            FROM
                "mail_activity"
            WHERE
                "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
                AND "mail_activity"."res_model_id" = 401
        )
    )
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id";
--  Sort  (cost=56.81..56.92 rows=45 width=8) (actual time=0.104..0.106 rows=3 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Seq Scan on voip_phonecall  (cost=41.52..55.57 rows=45 width=8) (actual time=0.086..0.093 rows=3 loops=1)
--          Filter: ((date_deadline <= '2023-09-12'::date) AND (NOT (hashed SubPlan 1)))
--          Rows Removed by Filter: 3
--          SubPlan 1
--            ->  Index Scan using mail_activity_res_id_index on mail_activity  (cost=0.28..41.51 rows=5 width=4) (actual time=0.026..0.046 rows=3 loops=1)
--                  Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                  Filter: (res_model_id = 401)
--  Planning Time: 0.391 ms
--  Execution Time: 0.168 ms

SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
WHERE
    "voip_phonecall"."date_deadline" <= '2023-09-12'
    AND NOT EXISTS (
        SELECT
        FROM
            "mail_activity"
        WHERE
            "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
            AND "mail_activity"."res_model_id" = 401
            AND "voip_phonecall"."activity_id" = "mail_activity"."id"
    )
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id";
-- Sort  (cost=56.11..56.33 rows=90 width=8) (actual time=0.099..0.103 rows=3 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Hash Anti Join  (cost=38.68..53.19 rows=90 width=8) (actual time=0.080..0.090 rows=3 loops=1)
--          Hash Cond: (voip_phonecall.activity_id = mail_activity.id)
--          ->  Seq Scan on voip_phonecall  (cost=0.00..13.38 rows=90 width=12) (actual time=0.017..0.023 rows=6 loops=1)
--                Filter: (date_deadline <= '2023-09-12'::date)
--          ->  Hash  (cost=38.61..38.61 rows=5 width=4) (actual time=0.049..0.050 rows=3 loops=1)
--                Buckets: 1024  Batches: 1  Memory Usage: 9kB
--                ->  Bitmap Heap Scan on mail_activity  (cost=21.45..38.61 rows=5 width=4) (actual time=0.039..0.042 rows=3 loops=1)
--                      Recheck Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                      Filter: (res_model_id = 401)
--                      Heap Blocks: exact=1
--                      ->  Bitmap Index Scan on mail_activity_res_id_index  (cost=0.00..21.45 rows=5 width=0) (actual time=0.031..0.031 rows=3 loops=1)
--                            Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--  Planning Time: 0.460 ms
--  Execution Time: 0.201 ms


SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
    LEFT JOIN "mail_activity" ON (
        "mail_activity".id = "voip_phonecall"."activity_id"
        AND "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
        AND "mail_activity"."res_model_id" = 401
    )
WHERE
    "voip_phonecall"."date_deadline" <= '2023-09-12'
    AND "mail_activity".id IS NULL
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id"
--  Sort  (cost=56.11..56.33 rows=90 width=8) (actual time=0.100..0.104 rows=3 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Hash Anti Join  (cost=38.68..53.19 rows=90 width=8) (actual time=0.082..0.091 rows=3 loops=1)
--          Hash Cond: (voip_phonecall.activity_id = mail_activity.id)
--          ->  Seq Scan on voip_phonecall  (cost=0.00..13.38 rows=90 width=12) (actual time=0.018..0.024 rows=6 loops=1)
--                Filter: (date_deadline <= '2023-09-12'::date)
--          ->  Hash  (cost=38.61..38.61 rows=5 width=4) (actual time=0.049..0.050 rows=3 loops=1)
--                Buckets: 1024  Batches: 1  Memory Usage: 9kB
--                ->  Bitmap Heap Scan on mail_activity  (cost=21.45..38.61 rows=5 width=4) (actual time=0.040..0.043 rows=3 loops=1)
--                      Recheck Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                      Filter: (res_model_id = 401)
--                      Heap Blocks: exact=1
--                      ->  Bitmap Index Scan on mail_activity_res_id_index  (cost=0.00..21.45 rows=5 width=0) (actual time=0.031..0.031 rows=3 loops=1)
--                            Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--  Planning Time: 0.448 ms
--  Execution Time: 0.182 ms


-- WITH OR -> left join can be very stupid
-- Very good
SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
WHERE
    "voip_phonecall"."date_deadline" <= '2022-09-12'
    OR (
        "voip_phonecall"."activity_id" in (
            SELECT
                "mail_activity".id
            FROM
                "mail_activity"
            WHERE
                "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
                AND "mail_activity"."res_model_id" = 401
        )
    )
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id";
-- Sort  (cost=62.32..62.77 rows=180 width=8) (actual time=0.102..0.105 rows=4 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Seq Scan on voip_phonecall  (cost=41.52..55.57 rows=180 width=8) (actual time=0.081..0.091 rows=4 loops=1)
--          Filter: ((date_deadline <= '2022-09-12'::date) OR (hashed SubPlan 1))
--          Rows Removed by Filter: 2
--          SubPlan 1
--            ->  Index Scan using mail_activity_res_id_index on mail_activity  (cost=0.28..41.51 rows=5 width=4) (actual time=0.025..0.046 rows=3 loops=1)
--                  Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                  Filter: (res_model_id = 401)
--  Planning Time: 0.361 ms
--  Execution Time: 0.165 ms


-- Cost very bad. But why the cost is so high
SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
WHERE
    "voip_phonecall"."date_deadline" <= '2022-09-12'
    OR EXISTS (
        SELECT
        FROM
            "mail_activity"
        WHERE
            "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
            AND "mail_activity"."res_model_id" = 401
            AND "voip_phonecall"."activity_id" = "mail_activity"."id"
    )
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id";
-- TODO: Why this cost ... 
--  Sort  (cost=2263.48..2263.93 rows=180 width=8) (actual time=0.104..0.107 rows=4 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Seq Scan on voip_phonecall  (cost=0.00..2256.74 rows=180 width=8) (actual time=0.083..0.093 rows=4 loops=1)
--          Filter: ((date_deadline <= '2022-09-12'::date) OR (hashed SubPlan 2))
--          Rows Removed by Filter: 2
--          SubPlan 2
--            ->  Bitmap Heap Scan on mail_activity  (cost=21.45..38.61 rows=5 width=4) (actual time=0.039..0.043 rows=3 loops=1)
--                  Recheck Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                  Filter: (res_model_id = 401)
--                  Heap Blocks: exact=1
--                  ->  Bitmap Index Scan on mail_activity_res_id_index  (cost=0.00..21.45 rows=5 width=0) (actual time=0.030..0.031 rows=3 loops=1)
--                        Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--  Planning Time: 0.529 ms
--  Execution Time: 0.182 ms

SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
    LEFT JOIN "mail_activity" ON (
        "mail_activity".id = "voip_phonecall"."activity_id"
    )
WHERE
    "voip_phonecall"."date_deadline" <= '2022-09-12'
    OR (
        "mail_activity".id IS NOT NULL
        AND "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
        AND "mail_activity"."res_model_id" = 401
    )
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id";
--  Sort  (cost=260.15..260.37 rows=90 width=8) (actual time=4.812..4.817 rows=4 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Hash Left Join  (cost=243.81..257.22 rows=90 width=8) (actual time=4.787..4.802 rows=4 loops=1)
--          Hash Cond: (voip_phonecall.activity_id = mail_activity.id)
--          Filter: ((voip_phonecall.date_deadline <= '2022-09-12'::date) OR ((mail_activity.id IS NOT NULL) AND (mail_activity.res_id = ANY ('{20,21,562,1563,15}'::integer[])) AND (mail_activity.res_model_id = 401)))
--          Rows Removed by Filter: 2
--          ->  Seq Scan on voip_phonecall  (cost=0.00..12.70 rows=270 width=16) (actual time=0.016..0.019 rows=6 loops=1)
--          ->  Hash  (cost=181.14..181.14 rows=5014 width=12) (actual time=4.743..4.744 rows=5014 loops=1)
--                Buckets: 8192  Batches: 1  Memory Usage: 280kB
--                ->  Seq Scan on mail_activity  (cost=0.00..181.14 rows=5014 width=12) (actual time=0.012..1.974 rows=5014 loops=1)
--  Planning Time: 0.463 ms
--  Execution Time: 4.865 ms

SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
    LEFT JOIN "mail_activity" ON (
        "mail_activity".id = "voip_phonecall"."activity_id"
        AND "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
        AND "mail_activity"."res_model_id" = 401
    )
WHERE
    "voip_phonecall"."date_deadline" <= '2022-09-12'
    OR "mail_activity".id IS NOT NULL
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id"
--  Sort  (cost=62.99..63.66 rows=270 width=8) (actual time=0.103..0.107 rows=4 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Hash Left Join  (cost=38.68..52.09 rows=270 width=8) (actual time=0.080..0.094 rows=4 loops=1)
--          Hash Cond: (voip_phonecall.activity_id = mail_activity.id)
--          Filter: ((voip_phonecall.date_deadline <= '2022-09-12'::date) OR (mail_activity.id IS NOT NULL))
--          Rows Removed by Filter: 2
--          ->  Seq Scan on voip_phonecall  (cost=0.00..12.70 rows=270 width=16) (actual time=0.014..0.017 rows=6 loops=1)
--          ->  Hash  (cost=38.61..38.61 rows=5 width=4) (actual time=0.051..0.052 rows=3 loops=1)
--                Buckets: 1024  Batches: 1  Memory Usage: 9kB
--                ->  Bitmap Heap Scan on mail_activity  (cost=21.45..38.61 rows=5 width=4) (actual time=0.042..0.045 rows=3 loops=1)
--                      Recheck Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                      Filter: (res_model_id = 401)
--                      Heap Blocks: exact=1
--                      ->  Bitmap Index Scan on mail_activity_res_id_index  (cost=0.00..21.45 rows=5 width=0) (actual time=0.031..0.032 rows=3 loops=1)
--                            Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--  Planning Time: 0.477 ms
--  Execution Time: 0.187 ms






-- WITH OR - NOT
SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
WHERE
    "voip_phonecall"."date_deadline" <= '2022-09-12'
    OR (
        "voip_phonecall"."activity_id" NOT in (
            SELECT
                "mail_activity".id
            FROM
                "mail_activity"
            WHERE
                "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
                AND "mail_activity"."res_model_id" = 401
        )
    )
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id";
--  Sort  (cost=62.32..62.77 rows=180 width=8) (actual time=0.104..0.106 rows=3 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Seq Scan on voip_phonecall  (cost=41.52..55.57 rows=180 width=8) (actual time=0.086..0.093 rows=3 loops=1)
--          Filter: ((date_deadline <= '2022-09-12'::date) OR (NOT (hashed SubPlan 1)))
--          Rows Removed by Filter: 3
--          SubPlan 1
--            ->  Index Scan using mail_activity_res_id_index on mail_activity  (cost=0.28..41.51 rows=5 width=4) (actual time=0.025..0.046 rows=3 loops=1)
--                  Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                  Filter: (res_model_id = 401)
--  Planning Time: 0.369 ms
--  Execution Time: 0.167 ms

SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
WHERE
    "voip_phonecall"."date_deadline" <= '2022-09-12'
    OR NOT EXISTS (
        SELECT
        FROM
            "mail_activity"
        WHERE
            "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
            AND "mail_activity"."res_model_id" = 401
            AND "voip_phonecall"."activity_id" = "mail_activity"."id"
    )
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id";
-- TODO: Why this cost ... 
-- Sort  (cost=2263.48..2263.93 rows=180 width=8) (actual time=0.104..0.108 rows=3 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Seq Scan on voip_phonecall  (cost=0.00..2256.74 rows=180 width=8) (actual time=0.087..0.095 rows=3 loops=1)
--          Filter: ((date_deadline <= '2022-09-12'::date) OR (NOT (hashed SubPlan 2)))
--          Rows Removed by Filter: 3
--          SubPlan 2
--            ->  Bitmap Heap Scan on mail_activity  (cost=21.45..38.61 rows=5 width=4) (actual time=0.040..0.043 rows=3 loops=1)
--                  Recheck Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                  Filter: (res_model_id = 401)
--                  Heap Blocks: exact=1
--                  ->  Bitmap Index Scan on mail_activity_res_id_index  (cost=0.00..21.45 rows=5 width=0) (actual time=0.031..0.031 rows=3 loops=1)
--                        Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--  Planning Time: 0.560 ms
--  Execution Time: 0.182 ms


SELECT
    "voip_phonecall".id
FROM
    "voip_phonecall"
    LEFT JOIN "mail_activity" ON (
        "mail_activity".id = "voip_phonecall"."activity_id"
        AND "mail_activity"."res_id" in (20, 21, 562, 1563, 15)
        AND "mail_activity"."res_model_id" = 401
    )
WHERE
    "voip_phonecall"."date_deadline" <= '2022-09-12'
    OR "mail_activity".id IS NULL
ORDER BY
    "voip_phonecall"."sequence",
    "voip_phonecall"."id"
--  Sort  (cost=55.01..55.23 rows=90 width=8) (actual time=0.130..0.134 rows=3 loops=1)
--    Sort Key: voip_phonecall.sequence, voip_phonecall.id
--    Sort Method: quicksort  Memory: 25kB
--    ->  Hash Left Join  (cost=38.68..52.09 rows=90 width=8) (actual time=0.109..0.120 rows=3 loops=1)
--          Hash Cond: (voip_phonecall.activity_id = mail_activity.id)
--          Filter: ((voip_phonecall.date_deadline <= '2022-09-12'::date) OR (mail_activity.id IS NULL))
--          Rows Removed by Filter: 3
--          ->  Seq Scan on voip_phonecall  (cost=0.00..12.70 rows=270 width=16) (actual time=0.014..0.017 rows=6 loops=1)
--          ->  Hash  (cost=38.61..38.61 rows=5 width=4) (actual time=0.050..0.052 rows=3 loops=1)
--                Buckets: 1024  Batches: 1  Memory Usage: 9kB
--                ->  Bitmap Heap Scan on mail_activity  (cost=21.45..38.61 rows=5 width=4) (actual time=0.041..0.044 rows=3 loops=1)
--                      Recheck Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--                      Filter: (res_model_id = 401)
--                      Heap Blocks: exact=1
--                      ->  Bitmap Index Scan on mail_activity_res_id_index  (cost=0.00..21.45 rows=5 width=0) (actual time=0.031..0.031 rows=3 loops=1)
--                            Index Cond: (res_id = ANY ('{20,21,562,1563,15}'::integer[]))
--  Planning Time: 0.473 ms
--  Execution Time: 0.214 ms
