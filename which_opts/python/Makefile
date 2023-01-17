data/ref:
	mkdir -p data/ref

data/ref/x86_64.json: data/ref
	curl -v https://raw.githubusercontent.com/astocko/json-x86-64/master/x86_64.json > data/ref/x86_64.json

.PHONY: get_mappings
get_mappings: data/ref/x86_64.json


.PHONY: collect
collect:
	pyre check && time python src/main.py collect --name gcc12

.PHONY: ingest
ingest: get_mappings
	sqlite3 data/database.db 'DROP TABLE instr;' && \
	pyre check && time python src/main.py ingest-refs

.PHONY: process
process:
	pyre check && time python src/main.py process

data/database.db: ingest process

.PHONY: reset_db
reset_db:
	rm data/database.db
	$(MAKE) data/database.db

