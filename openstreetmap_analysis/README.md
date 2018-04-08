### Use the command line to get rid of the header of the csv files
```bash
python etl.py
tail -n +2 nodes.csv > nodes_no_head.csv
tail -n +2 nodes_tags.csv > nodes_tags_no_head.csv
tail -n +2 ways.csv > ways_no_head.csv
tail -n +2 ways_tags_clean.csv > ways_tags_no_head.csv
tail -n +2 ways_nodes.csv > ways_nodes_no_head.csv
```

### Create tables in sqlite
```
sqlite> .read create.sql
sqlite> .mode csv
sqlite> .import nodes_no_head.csv nodes
sqlite> .import nodes_tags_no_head.csv nodes_tags
sqlite> .import ways_no_head.csv ways
sqlite> .import ways_tags_no_head.csv ways_tags
sqlite> .import ways_nodes_no_head.csv ways_nodes
```

### Run jupyter nootbook to see the result
