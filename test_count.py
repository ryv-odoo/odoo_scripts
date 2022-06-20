

import psycopg2
import random
import time
from statistics import NormalDist, fmean, pstdev

from misc import psql_vacuum_analyse, remove_outliers, x_bests

CONNECTION_PARAMS = "dbname=master"
REPEAT_TEST = 200

count_star = "SELECT count(*) FROM test_count"
count_1 = "SELECT count(1) FROM test_count"
count_star_where = "SELECT count(*) FROM test_count WHERE salary > 5000"
count_1_where = "SELECT count(1) FROM test_count WHERE salary > 5000"
count_star_where_20 = "SELECT count(*) FROM test_count WHERE age < 20"
count_1_where_20 = "SELECT count(1) FROM test_count WHERE age < 20"

all_possibility = [
    ('count(*)', count_star),
    ('count(1)', count_1),
    ('count(*) where', count_star_where),
    ('count(1) where', count_1_where),
    ('count(*) where 20%', count_star_where_20),
    ('count(1) where 20%', count_1_where_20),
]

def create_table(con):
    with psycopg2.connect(CONNECTION_PARAMS) as con:
        with con.cursor() as cr:
            cr.execute("drop table test_count;")
            cr.execute("""
            CREATE TABLE test_count (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                age INT NOT NULL,
                salary REAL);
            """)

def insert_rows(con, nb):
    with con.cursor() as cr:
        cr.execute("INSERT INTO test_count (name, age, salary) SELECT md5(random()::text), (random() * 100)::int, random()*10000 from generate_series(1, %s)", [nb])
    con.commit()

def print_stat(time_dict):
    for k, t in time_dict.items():
        print(f"{k} take {(sum(t) / 1_000_000 / REPEAT_TEST):.4f} ms by query ({(sum(t) / 1_000_000):.4f} ms in total) ({len(t)} sample)")
    dist_star = NormalDist.from_samples(time_dict['count(*)']) / 1_000_000
    dist_1 = NormalDist.from_samples(time_dict['count(1)']) / 1_000_000
    if dist_star.overlap(dist_1) < 0.025 and dist_star.mean < dist_1.mean:
        print("count(*) is statically faster than count(1) with a normal distribution")
    print(f"count(*) : {dist_star.mean:.4f} +- {dist_star.stdev:.4f} ms vs count(1): {dist_1.mean:.4f} +- {dist_1.stdev:.4f} ms")
    print(f"count(*) : {(100 - (dist_star.mean * 100 / dist_1.mean)):.4f} % faster")
    print(f"count(*) overlaps {dist_star.overlap(dist_1):.4f} count(1)")

def launch_test():
    with psycopg2.connect(CONNECTION_PARAMS) as con:
        with con.cursor() as cr:
            print("Warm UP")
            for i in range(5):
                for p, query in all_possibility:
                    cr.execute(query)
                    if p == 'count_1' and i == 0:
                        print(f"Test for {cr.fetchone()[0]} rows")

            print("Launch Test")
            time_dict = {k:[] for k, v in all_possibility}
            for i in range(REPEAT_TEST):
                if i % 20 == 0:
                    pass
                    # print(f"{i}/{nb}")
                for p, query in random.sample(all_possibility, len(all_possibility)):
                    s = time.time_ns()
                    cr.execute(query)
                    f = time.time_ns() - s
                    time_dict[p].append(f)

            print("\nWith raw data:")
            print_stat(time_dict)

            time_ns_out1 = {k : remove_outliers(t) for k, t in time_dict.items()}
            print("\nAfter removed outliner:")
            print_stat(time_ns_out1)

            time_ns_best = {k : x_bests(t, 20) for k, t in time_dict.items()}
            print("\nWith 20 bests:")
            print_stat(time_ns_best)
            print("------------------------")


with psycopg2.connect(CONNECTION_PARAMS) as con:
    create_table(con)

def insert_and_test(nb):
    with psycopg2.connect(CONNECTION_PARAMS) as con:
        insert_rows(con, nb)
        con.commit()
    psql_vacuum_analyse(CONNECTION_PARAMS, None)
    launch_test()

insert_and_test(1_000)
insert_and_test(10_000)
insert_and_test(100_000)
insert_and_test(1_000_000)
insert_and_test(5_000_000)


# result
# python scripts/test_count.py
# Warm UP
# Launch Test

# With raw data:
# count(*) take 0.1374 ms by query (27.4784 ms in total) (200 sample)
# count(1) take 0.1432 ms by query (28.6315 ms in total) (200 sample)
# count(*) where take 0.1856 ms by query (37.1244 ms in total) (200 sample)
# count(1) where take 0.1890 ms by query (37.8023 ms in total) (200 sample)
# count(*) where 20% take 0.1669 ms by query (33.3849 ms in total) (200 sample)
# count(1) where 20% take 0.1714 ms by query (34.2791 ms in total) (200 sample)
# count(*) : 0.1374 +- 0.0771 ms vs count(1): 0.1432 +- 0.0798 ms
# count(*) : 4.0275 % faster
# count(*) overlaps 0.9677 count(1)

# After removed outliner:
# count(*) take 0.1076 ms by query (21.5187 ms in total) (183 sample)
# count(1) take 0.1093 ms by query (21.8627 ms in total) (181 sample)
# count(*) where take 0.1372 ms by query (27.4367 ms in total) (178 sample)
# count(1) where take 0.1394 ms by query (27.8812 ms in total) (178 sample)
# count(*) where 20% take 0.1327 ms by query (26.5417 ms in total) (184 sample)
# count(1) where 20% take 0.1312 ms by query (26.2421 ms in total) (181 sample)
# count(*) : 0.1176 +- 0.0402 ms vs count(1): 0.1208 +- 0.0396 ms
# count(*) : 2.6491 % faster
# count(*) overlaps 0.9674 count(1)

# With 20 bests:
# count(*) take 0.0079 ms by query (1.5830 ms in total) (20 sample)
# count(1) take 0.0082 ms by query (1.6431 ms in total) (20 sample)
# count(*) where take 0.0112 ms by query (2.2465 ms in total) (20 sample)
# count(1) where take 0.0115 ms by query (2.2996 ms in total) (20 sample)
# count(*) where 20% take 0.0098 ms by query (1.9528 ms in total) (20 sample)
# count(1) where 20% take 0.0100 ms by query (1.9902 ms in total) (20 sample)
# count(*) is statically faster than count(1) with a normal distribution
# count(*) : 0.0792 +- 0.0002 ms vs count(1): 0.0822 +- 0.0003 ms
# count(*) : 3.6532 % faster
# count(*) overlaps 0.0000 count(1)
# ------------------------
# Warm UP
# Launch Test

# With raw data:
# count(*) take 0.5347 ms by query (106.9488 ms in total) (200 sample)
# count(1) take 0.5553 ms by query (111.0653 ms in total) (200 sample)
# count(*) where take 0.8551 ms by query (171.0267 ms in total) (200 sample)
# count(1) where take 0.8753 ms by query (175.0521 ms in total) (200 sample)
# count(*) where 20% take 0.7064 ms by query (141.2783 ms in total) (200 sample)
# count(1) where 20% take 0.7199 ms by query (143.9754 ms in total) (200 sample)
# count(*) : 0.5347 +- 0.0371 ms vs count(1): 0.5553 +- 0.0431 ms
# count(*) : 3.7064 % faster
# count(*) overlaps 0.7896 count(1)

# After removed outliner:
# count(*) take 0.4995 ms by query (99.9071 ms in total) (189 sample)
# count(1) take 0.5373 ms by query (107.4627 ms in total) (195 sample)
# count(*) where take 0.8112 ms by query (162.2302 ms in total) (191 sample)
# count(1) where take 0.8347 ms by query (166.9307 ms in total) (192 sample)
# count(*) where 20% take 0.6526 ms by query (130.5112 ms in total) (187 sample)
# count(1) where 20% take 0.6692 ms by query (133.8331 ms in total) (188 sample)
# count(*) : 0.5286 +- 0.0265 ms vs count(1): 0.5511 +- 0.0315 ms
# count(*) : 4.0795 % faster
# count(*) overlaps 0.6914 count(1)

# With 20 bests:
# count(*) take 0.0508 ms by query (10.1665 ms in total) (20 sample)
# count(1) take 0.0528 ms by query (10.5530 ms in total) (20 sample)
# count(*) where take 0.0818 ms by query (16.3500 ms in total) (20 sample)
# count(1) where take 0.0833 ms by query (16.6539 ms in total) (20 sample)
# count(*) where 20% take 0.0677 ms by query (13.5370 ms in total) (20 sample)
# count(1) where 20% take 0.0684 ms by query (13.6746 ms in total) (20 sample)
# count(*) is statically faster than count(1) with a normal distribution
# count(*) : 0.5083 +- 0.0027 ms vs count(1): 0.5276 +- 0.0011 ms
# count(*) : 3.6620 % faster
# count(*) overlaps 0.0000 count(1)
# ------------------------
# Warm UP
# Launch Test

# With raw data:
# count(*) take 4.4840 ms by query (896.8011 ms in total) (200 sample)
# count(1) take 4.7350 ms by query (947.0041 ms in total) (200 sample)
# count(*) where take 8.0152 ms by query (1603.0332 ms in total) (200 sample)
# count(1) where take 8.2068 ms by query (1641.3565 ms in total) (200 sample)
# count(*) where 20% take 6.6017 ms by query (1320.3479 ms in total) (200 sample)
# count(1) where 20% take 6.6350 ms by query (1327.0042 ms in total) (200 sample)
# count(*) : 4.4840 +- 0.1636 ms vs count(1): 4.7350 +- 0.1762 ms
# count(*) : 5.3013 % faster
# count(*) overlaps 0.4596 count(1)

# After removed outliner:
# count(*) take 4.2572 ms by query (851.4382 ms in total) (191 sample)
# count(1) take 4.3930 ms by query (878.6077 ms in total) (187 sample)
# count(*) where take 7.4506 ms by query (1490.1213 ms in total) (187 sample)
# count(1) where take 7.5264 ms by query (1505.2710 ms in total) (185 sample)
# count(*) where 20% take 6.1954 ms by query (1239.0775 ms in total) (189 sample)
# count(1) where 20% take 6.1915 ms by query (1238.2951 ms in total) (188 sample)
# count(*) : 4.4578 +- 0.1023 ms vs count(1): 4.6984 +- 0.1036 ms
# count(*) : 5.1218 % faster
# count(*) overlaps 0.2426 count(1)

# With 20 bests:
# count(*) take 0.4322 ms by query (86.4354 ms in total) (20 sample)
# count(1) take 0.4557 ms by query (91.1300 ms in total) (20 sample)
# count(*) where take 0.7761 ms by query (155.2135 ms in total) (20 sample)
# count(1) where take 0.7943 ms by query (158.8697 ms in total) (20 sample)
# count(*) where 20% take 0.6346 ms by query (126.9183 ms in total) (20 sample)
# count(1) where 20% take 0.6393 ms by query (127.8629 ms in total) (20 sample)
# count(*) is statically faster than count(1) with a normal distribution
# count(*) : 4.3218 +- 0.0188 ms vs count(1): 4.5565 +- 0.0167 ms
# count(*) : 5.1515 % faster
# count(*) overlaps 0.0000 count(1)
# ------------------------
# Warm UP
# Launch Test

# With raw data:
# count(*) take 23.6813 ms by query (4736.2547 ms in total) (200 sample)
# count(1) take 24.2895 ms by query (4857.8902 ms in total) (200 sample)
# count(*) where take 36.1670 ms by query (7233.4020 ms in total) (200 sample)
# count(1) where take 36.5293 ms by query (7305.8518 ms in total) (200 sample)
# count(*) where 20% take 31.1314 ms by query (6226.2878 ms in total) (200 sample)
# count(1) where 20% take 31.3508 ms by query (6270.1600 ms in total) (200 sample)
# count(*) : 23.6813 +- 0.3180 ms vs count(1): 24.2895 +- 0.3174 ms
# count(*) : 2.5039 % faster
# count(*) overlaps 0.3385 count(1)

# After removed outliner:
# count(*) take 23.0603 ms by query (4612.0617 ms in total) (195 sample)
# count(1) take 23.0268 ms by query (4605.3664 ms in total) (190 sample)
# count(*) where take 35.6995 ms by query (7139.9006 ms in total) (198 sample)
# count(1) where take 35.0310 ms by query (7006.1941 ms in total) (192 sample)
# count(*) where 20% take 29.3778 ms by query (5875.5684 ms in total) (189 sample)
# count(1) where 20% take 30.6882 ms by query (6137.6468 ms in total) (196 sample)
# count(*) : 23.6516 +- 0.2149 ms vs count(1): 24.2388 +- 0.2169 ms
# count(*) : 2.4224 % faster
# count(*) overlaps 0.1739 count(1)

# With 20 bests:
# count(*) take 2.3290 ms by query (465.7990 ms in total) (20 sample)
# count(1) take 2.3926 ms by query (478.5267 ms in total) (20 sample)
# count(*) where take 3.5723 ms by query (714.4548 ms in total) (20 sample)
# count(1) where take 3.6176 ms by query (723.5209 ms in total) (20 sample)
# count(*) where 20% take 3.0769 ms by query (615.3740 ms in total) (20 sample)
# count(1) where 20% take 3.0977 ms by query (619.5454 ms in total) (20 sample)
# count(*) is statically faster than count(1) with a normal distribution
# count(*) : 23.2899 +- 0.0977 ms vs count(1): 23.9263 +- 0.0651 ms
# count(*) : 2.6598 % faster
# count(*) overlaps 0.0001 count(1)
# ------------------------
# Warm UP
# Launch Test

# With raw data:
# count(*) take 127.5635 ms by query (25512.7072 ms in total) (200 sample)
# count(1) take 130.7535 ms by query (26150.7033 ms in total) (200 sample)
# count(*) where take 194.8579 ms by query (38971.5736 ms in total) (200 sample)
# count(1) where take 197.6577 ms by query (39531.5423 ms in total) (200 sample)
# count(*) where 20% take 165.8626 ms by query (33172.5248 ms in total) (200 sample)
# count(1) where 20% take 166.4291 ms by query (33285.8179 ms in total) (200 sample)
# count(*) : 127.5635 +- 22.8791 ms vs count(1): 130.7535 +- 22.1474 ms
# count(*) : 2.4397 % faster
# count(*) overlaps 0.9421 count(1)

# After removed outliner:
# count(*) take 114.5727 ms by query (22914.5422 ms in total) (187 sample)
# count(1) take 115.9771 ms by query (23195.4215 ms in total) (185 sample)
# count(*) where take 176.1427 ms by query (35228.5480 ms in total) (188 sample)
# count(1) where take 175.5176 ms by query (35103.5204 ms in total) (185 sample)
# count(*) where 20% take 152.4840 ms by query (30496.7989 ms in total) (190 sample)
# count(1) where 20% take 152.0905 ms by query (30418.0915 ms in total) (189 sample)
# count(*) : 122.5377 +- 11.9399 ms vs count(1): 125.3807 +- 10.8329 ms
# count(*) : 2.2675 % faster
# count(*) overlaps 0.8937 count(1)

# With 20 bests:
# count(*) take 11.5554 ms by query (2311.0751 ms in total) (20 sample)
# count(1) take 11.8988 ms by query (2379.7536 ms in total) (20 sample)
# count(*) where take 17.9086 ms by query (3581.7189 ms in total) (20 sample)
# count(1) where take 18.1430 ms by query (3628.5980 ms in total) (20 sample)
# count(*) where 20% take 15.1846 ms by query (3036.9202 ms in total) (20 sample)
# count(1) where 20% take 15.3025 ms by query (3060.4906 ms in total) (20 sample)
# count(*) is statically faster than count(1) with a normal distribution
# count(*) : 115.5538 +- 0.2031 ms vs count(1): 118.9877 +- 0.1257 ms
# count(*) : 2.8860 % faster
# count(*) overlaps 0.0000 count(1)
# ------------------------