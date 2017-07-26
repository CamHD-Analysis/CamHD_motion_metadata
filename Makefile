
PYTHON = python3


csv:  datapackage/regions.csv
.PHONY: csv datapackage/regions.csv

datapackage/regions.csv:
	${PYTHON} scripts/make_csv.py --output $@ RS03ASHS/PN03B/06-CAMHDA301/**/*regions.json
