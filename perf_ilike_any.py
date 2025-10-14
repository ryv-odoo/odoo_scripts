"""
CREATE TABLE location (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    parent_path VARCHAR NOT NULL
);

INSERT INTO location (name, parent_path)
SELECT md5(random()::text),
CASE
    WHEN s = 1 THEN '1/'
    WHEN s < 100 THEN '1/' || (random() * s)::int::text || '/' || s
    ELSE '1/' || (random() * 100)::int::text || '/' || (((random() * s) - 100) + 100)::int::text || '/' || s
END
FROM generate_series(1, 100000) AS s;

CREATE INDEX tgrm_name ON location USING gin(name gin_trgm_ops);
CREATE INDEX parent_path_index ON location (parent_path);

"""

# Trigram test
"""
-- NOW:
EXPLAIN ANALYSE SELECT id FROM location
WHERE name ilike '%ebb0%' OR name ilike '%bcb2%';

-- Simpler query plan and sightly better
EXPLAIN ANALYSE SELECT id FROM location
WHERE name ILIKE ANY (array['%ebb0%', '%bcb2%']);

-- NOW:
EXPLAIN ANALYSE SELECT id FROM location
WHERE name ilike '%ebb0%' OR name ilike '%bcb2%' OR name ilike '%cb26%' OR name ilike '%aaa2%' OR name ilike '%cccc%';

-- Simpler query plan but the cost is sightly higher
EXPLAIN ANALYSE SELECT id FROM location
WHERE name ILIKE ANY (array['%ebb0%', '%bcb2%', '%cb26%', '%aaa2%', '%cccc%']);

-- NOW:
EXPLAIN ANALYSE SELECT id FROM location
WHERE name ilike '%ebb0%' OR name ilike '%bcb2%' OR name ilike '%cb26%' OR name ilike '%aaa2%' OR name ilike '%cccc%'
OR name ilike '%8b1a%' OR name ilike '%214c%' OR name ilike '%851d1b4%' OR name ilike '%1e91a74%' OR name ilike '%e81dbcd%';

-- Simpler query plan and sightly better
EXPLAIN ANALYSE SELECT id FROM location
WHERE name ILIKE ANY (array['%ebb0%', '%bcb2%', '%cb26%', '%aaa2%', '%cccc%', 
'%8b1a%', '%214c%', '%851d1b4%', '%1e91a74%', '%e81dbcd%']);

-- NOW:
EXPLAIN ANALYSE SELECT id FROM location
WHERE name ilike '%eb%' OR name ilike '%bc%';

-- Simpler query plan and sightly better
EXPLAIN ANALYSE SELECT id FROM location
WHERE name ILIKE ANY (array['%eb%', '%bc%']);
"""

# Parent_path test
"""
-- NOW:
EXPLAIN ANALYSE SELECT id FROM location
WHERE parent_path LIKE '1/93/64/%' OR parent_path LIKE '1/19/%';

-- Worst :'(
EXPLAIN ANALYSE SELECT id FROM location
WHERE parent_path LIKE ANY (array['1/93/64/%', '1/19/%']);


-- NOW:
EXPLAIN ANALYSE SELECT id FROM location
WHERE parent_path LIKE '1/93/64/%' OR parent_path LIKE '1/19/%' 
OR parent_path LIKE '1/85/96/%' OR parent_path LIKE '1/52/52/%' OR parent_path LIKE '1/5/100/%';

-- Worst :'(
EXPLAIN ANALYSE SELECT id FROM location
WHERE parent_path LIKE ANY (array['1/93/64/%', '1/19/%', '1/85/96/%', '1/52/52/%', '1/5/100/%']);

-- Special case, same prefix
-- NOW:
EXPLAIN ANALYSE SELECT id FROM location
WHERE parent_path LIKE '1/93/%' OR parent_path LIKE '1/93/52/%' OR parent_path LIKE '1/93/58/%';

-- Worst :'(
EXPLAIN ANALYSE SELECT id FROM location
WHERE parent_path LIKE ANY (array['1/93/%', '1/93/52/%', '1/93/58/%']);

--Simplification
EXPLAIN ANALYSE SELECT id FROM location
WHERE parent_path LIKE '1/93/%';

"""



"""USELESS SOLUTION
-- Very slow
EXPLAIN ANALYSE SELECT id FROM location
WHERE name ILIKE ANY (values ('%ebb0%'), ('%bcb2%'), ('%cb26%'), ('%aaa2%'), ('%cccc%'));
"""

