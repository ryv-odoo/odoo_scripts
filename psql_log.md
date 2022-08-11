# Main idea

Get some log from server to be more proactive for indexes
-> To get log: https://www.postgresql.org/docs/current/auto-explain.html

# Analyse

Tools to analyse:
- pg-badger
- regex ?

Stuff to analyse:
- Most indexes used (and then index unused)
- Aggregate requests (focus on the most problematic ones)
- Find missing index (SeqScan with a filtered)

Nice to have:
- Add pg_stats to the explain (to know wht psql take decision and to ensure that create new indexes will be good), how ? https://www.postgresql.org/docs/current/view-pg-stats.html
- Analyze log of Odoo (time of request python vs SQL)

