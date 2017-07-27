
PYTHON = python3


## Convert all optical_flow_regions.json files into the flat CSV file format.
csv:  datapackage/regions.csv
.PHONY: csv datapackage/regions.csv

datapackage/regions.csv:
	${PYTHON} scripts/make_csv.py --output $@ RS03ASHS/PN03B/06-CAMHDA301/**/*regions.json


datapackage/movie_metadata.csv:
	${PYTHON} scripts/ci_scrape_to_csv.py --output $@ ci_scrape_*.json
