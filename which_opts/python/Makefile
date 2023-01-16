.PHONY: collect
collect:
	pyre check && time python src/main.py collect --name gcc12

.PHONY: process
process:
	rm ./data/database.db ; pyre check && time python src/main.py process

