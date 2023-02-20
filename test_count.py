

import psycopg2
import random
import time
from statistics import NormalDist

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
            cr.execute("drop table IF EXISTS test_count;")
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
        print(f"{k} take {(sum(t) / 1_000_000 / len(t)):.4f} ms by query ({(sum(t) / 1_000_000):.4f} ms in total) ({len(t)} sample)")
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


# -------------- result
# python scripts/test_count.py
# Warm UP
# Launch Test

# With raw data:
# count(*) take 0.0949 ms by query (18.9743 ms in total) (200 sample)
# count(1) take 0.0951 ms by query (19.0120 ms in total) (200 sample)
# count(*) where take 0.1268 ms by query (25.3589 ms in total) (200 sample)
# count(1) where take 0.1294 ms by query (25.8889 ms in total) (200 sample)
# count(*) where 20% take 0.1122 ms by query (22.4464 ms in total) (200 sample)
# count(1) where 20% take 0.1139 ms by query (22.7728 ms in total) (200 sample)
# count(*) : 0.0949 +- 0.0278 ms vs count(1): 0.0951 +- 0.0208 ms
# count(*) : 0.1985 % faster
# count(*) overlaps 0.8620 count(1)

# After removed outliner:
# count(*) take 0.0923 ms by query (18.0910 ms in total) (196 sample)
# count(1) take 0.0910 ms by query (17.0094 ms in total) (187 sample)
# count(*) where take 0.1239 ms by query (23.5321 ms in total) (190 sample)
# count(1) where take 0.1256 ms by query (23.9934 ms in total) (191 sample)
# count(*) where 20% take 0.1092 ms by query (20.7482 ms in total) (190 sample)
# count(1) where 20% take 0.1103 ms by query (20.9573 ms in total) (190 sample)
# count(*) : 0.0923 +- 0.0179 ms vs count(1): 0.0910 +- 0.0133 ms
# count(*) : -1.4750 % faster
# count(*) overlaps 0.8535 count(1)

# With 20 bests:
# count(*) take 0.0788 ms by query (1.5766 ms in total) (20 sample)
# count(1) take 0.0820 ms by query (1.6405 ms in total) (20 sample)
# count(*) where take 0.1124 ms by query (2.2480 ms in total) (20 sample)
# count(1) where take 0.1150 ms by query (2.3004 ms in total) (20 sample)
# count(*) where 20% take 0.0984 ms by query (1.9673 ms in total) (20 sample)
# count(1) where 20% take 0.1003 ms by query (2.0050 ms in total) (20 sample)
# count(*) is statically faster than count(1) with a normal distribution
# count(*) : 0.0788 +- 0.0003 ms vs count(1): 0.0820 +- 0.0003 ms
# count(*) : 3.8982 % faster
# count(*) overlaps 0.0000 count(1)
# ------------------------
# Warm UP
# Launch Test

# With raw data:
# count(*) take 0.5378 ms by query (107.5596 ms in total) (200 sample)
# count(1) take 0.5563 ms by query (111.2530 ms in total) (200 sample)
# count(*) where take 0.8656 ms by query (173.1141 ms in total) (200 sample)
# count(1) where take 0.8753 ms by query (175.0631 ms in total) (200 sample)
# count(*) where 20% take 0.7155 ms by query (143.1094 ms in total) (200 sample)
# count(1) where 20% take 0.7223 ms by query (144.4603 ms in total) (200 sample)
# count(*) : 0.5378 +- 0.0405 ms vs count(1): 0.5563 +- 0.0358 ms
# count(*) : 3.3198 % faster
# count(*) overlaps 0.8031 count(1)

# After removed outliner:
# count(*) take 0.5333 ms by query (103.4652 ms in total) (194 sample)
# count(1) take 0.5506 ms by query (104.6105 ms in total) (190 sample)
# count(*) where take 0.8572 ms by query (167.1532 ms in total) (195 sample)
# count(1) where take 0.8691 ms by query (165.9990 ms in total) (191 sample)
# count(*) where 20% take 0.7066 ms by query (132.1434 ms in total) (187 sample)
# count(1) where 20% take 0.7121 ms by query (133.1615 ms in total) (187 sample)
# count(*) : 0.5333 +- 0.0309 ms vs count(1): 0.5506 +- 0.0256 ms
# count(*) : 3.1341 % faster
# count(*) overlaps 0.7497 count(1)

# With 20 bests:
# count(*) take 0.5091 ms by query (10.1817 ms in total) (20 sample)
# count(1) take 0.5272 ms by query (10.5448 ms in total) (20 sample)
# count(*) where take 0.8171 ms by query (16.3428 ms in total) (20 sample)
# count(1) where take 0.8333 ms by query (16.6654 ms in total) (20 sample)
# count(*) where 20% take 0.6777 ms by query (13.5547 ms in total) (20 sample)
# count(1) where 20% take 0.6855 ms by query (13.7109 ms in total) (20 sample)
# count(*) is statically faster than count(1) with a normal distribution
# count(*) : 0.5091 +- 0.0016 ms vs count(1): 0.5272 +- 0.0044 ms
# count(*) : 3.4433 % faster
# count(*) overlaps 0.0020 count(1)
# ------------------------
# Warm UP
# Launch Test

# With raw data:
# count(*) take 4.4879 ms by query (897.5804 ms in total) (200 sample)
# count(1) take 4.7164 ms by query (943.2769 ms in total) (200 sample)
# count(*) where take 7.9614 ms by query (1592.2763 ms in total) (200 sample)
# count(1) where take 8.1251 ms by query (1625.0230 ms in total) (200 sample)
# count(*) where 20% take 6.5148 ms by query (1302.9694 ms in total) (200 sample)
# count(1) where 20% take 6.5817 ms by query (1316.3317 ms in total) (200 sample)
# count(*) : 4.4879 +- 0.1755 ms vs count(1): 4.7164 +- 0.1416 ms
# count(*) : 4.8444 % faster
# count(*) overlaps 0.4665 count(1)

# After removed outliner:
# count(*) take 4.4601 ms by query (856.3401 ms in total) (192 sample)
# count(1) take 4.6982 ms by query (906.7511 ms in total) (193 sample)
# count(*) where take 7.9331 ms by query (1507.2944 ms in total) (190 sample)
# count(1) where take 8.0937 ms by query (1529.7083 ms in total) (189 sample)
# count(*) where 20% take 6.4866 ms by query (1225.9608 ms in total) (189 sample)
# count(1) where 20% take 6.5575 ms by query (1252.4895 ms in total) (191 sample)
# count(*) : 4.4601 +- 0.0909 ms vs count(1): 4.6982 +- 0.0965 ms
# count(*) : 5.0676 % faster
# count(*) overlaps 0.2039 count(1)

# With 20 bests:
# count(*) take 4.3382 ms by query (86.7646 ms in total) (20 sample)
# count(1) take 4.5591 ms by query (91.1828 ms in total) (20 sample)
# count(*) where take 7.7686 ms by query (155.3725 ms in total) (20 sample)
# count(1) where take 7.9120 ms by query (158.2409 ms in total) (20 sample)
# count(*) where 20% take 6.3187 ms by query (126.3737 ms in total) (20 sample)
# count(1) where 20% take 6.3852 ms by query (127.7045 ms in total) (20 sample)
# count(*) is statically faster than count(1) with a normal distribution
# count(*) : 4.3382 +- 0.0109 ms vs count(1): 4.5591 +- 0.0205 ms
# count(*) : 4.8455 % faster
# count(*) overlaps 0.0000 count(1)
# ------------------------
# Warm UP
# Launch Test

# With raw data:
# count(*) take 23.7033 ms by query (4740.6509 ms in total) (200 sample)
# count(1) take 24.3344 ms by query (4866.8803 ms in total) (200 sample)
# count(*) where take 36.1336 ms by query (7226.7271 ms in total) (200 sample)
# count(1) where take 36.5123 ms by query (7302.4568 ms in total) (200 sample)
# count(*) where 20% take 31.1644 ms by query (6232.8835 ms in total) (200 sample)
# count(1) where 20% take 31.3234 ms by query (6264.6776 ms in total) (200 sample)
# count(*) : 23.7033 +- 0.2959 ms vs count(1): 24.3344 +- 0.7148 ms
# count(*) : 2.5936 % faster
# count(*) overlaps 0.4388 count(1)

# After removed outliner:
# count(*) take 23.6777 ms by query (4664.5009 ms in total) (197 sample)
# count(1) take 24.2656 ms by query (4804.5811 ms in total) (198 sample)
# count(*) where take 36.0686 ms by query (7177.6454 ms in total) (199 sample)
# count(1) where take 36.4883 ms by query (6969.2669 ms in total) (191 sample)
# count(*) where 20% take 31.1103 ms by query (6190.9447 ms in total) (199 sample)
# count(1) where 20% take 31.3061 ms by query (6073.3758 ms in total) (194 sample)
# count(*) : 23.6777 +- 0.1770 ms vs count(1): 24.2656 +- 0.1994 ms
# count(*) : 2.4227 % faster
# count(*) overlaps 0.1180 count(1)

# With 20 bests:
# count(*) take 23.3931 ms by query (467.8623 ms in total) (20 sample)
# count(1) take 23.9612 ms by query (479.2247 ms in total) (20 sample)
# count(*) where take 35.7494 ms by query (714.9879 ms in total) (20 sample)
# count(1) where take 36.2133 ms by query (724.2666 ms in total) (20 sample)
# count(*) where 20% take 30.8122 ms by query (616.2431 ms in total) (20 sample)
# count(1) where 20% take 31.0088 ms by query (620.1760 ms in total) (20 sample)
# count(*) is statically faster than count(1) with a normal distribution
# count(*) : 23.3931 +- 0.0716 ms vs count(1): 23.9612 +- 0.0612 ms
# count(*) : 2.3710 % faster
# count(*) overlaps 0.0000 count(1)
# ------------------------
# Warm UP
# Launch Test

# With raw data:
# count(*) take 117.2544 ms by query (23450.8867 ms in total) (200 sample)
# count(1) take 120.8121 ms by query (24162.4130 ms in total) (200 sample)
# count(*) where take 180.8495 ms by query (36169.9052 ms in total) (200 sample)
# count(1) where take 183.4698 ms by query (36693.9682 ms in total) (200 sample)
# count(*) where 20% take 154.5207 ms by query (30904.1379 ms in total) (200 sample)
# count(1) where 20% take 155.7114 ms by query (31142.2738 ms in total) (200 sample)
# count(*) : 117.2544 +- 4.7296 ms vs count(1): 120.8121 +- 5.1351 ms
# count(*) : 2.9448 % faster
# count(*) overlaps 0.7166 count(1)

# After removed outliner:
# count(*) take 116.4669 ms by query (22361.6359 ms in total) (192 sample)
# count(1) take 119.9544 ms by query (23151.2002 ms in total) (193 sample)
# count(*) where take 179.9911 ms by query (34918.2712 ms in total) (194 sample)
# count(1) where take 182.5217 ms by query (35044.1672 ms in total) (192 sample)
# count(*) where 20% take 153.1218 ms by query (29552.5036 ms in total) (193 sample)
# count(1) where 20% take 154.3365 ms by query (29941.2735 ms in total) (194 sample)
# count(*) : 116.4669 +- 1.9328 ms vs count(1): 119.9544 +- 2.2864 ms
# count(*) : 2.9074 % faster
# count(*) overlaps 0.4061 count(1)

# With 20 bests:
# count(*) take 115.1633 ms by query (2303.2660 ms in total) (20 sample)
# count(1) take 118.3685 ms by query (2367.3703 ms in total) (20 sample)
# count(*) where take 178.2470 ms by query (3564.9395 ms in total) (20 sample)
# count(1) where take 180.9691 ms by query (3619.3826 ms in total) (20 sample)
# count(*) where 20% take 151.4127 ms by query (3028.2536 ms in total) (20 sample)
# count(1) where 20% take 152.4874 ms by query (3049.7475 ms in total) (20 sample)
# count(*) is statically faster than count(1) with a normal distribution
# count(*) : 115.1633 +- 0.1695 ms vs count(1): 118.3685 +- 0.1090 ms
# count(*) : 2.7078 % faster
# count(*) overlaps 0.0000 count(1)
# ------------------------