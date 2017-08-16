
PYTHON = python3


## Convert all optical_flow_regions.json files into the flat CSV file format.
csv:  datapackage/regions.csv

## Process only d2 right now
datapackage/regions.csv:
	${PYTHON} scripts/regions_to_csv.py --output $@ RS03ASHS/PN03B/06-CAMHDA301/2015/11/2[5-9]/*regions.json \
																									RS03ASHS/PN03B/06-CAMHDA301/2015/11/3?/*regions.json \
																									RS03ASHS/PN03B/06-CAMHDA301/2015/12/*/*regions.json \
																									RS03ASHS/PN03B/06-CAMHDA301/2016/0[1-5]/*/*regions.json \
																									RS03ASHS/PN03B/06-CAMHDA301/2016/06/[01]?/*regions.json \
																									RS03ASHS/PN03B/06-CAMHDA301/2016/06/2[0-5]/*regions.json \

html_to_google_drive:
	gsutil -m rsync -a public-read -d -r _html/ gs://camhd_region_proofs/



## Note:   this will take a long time...
ci_scrape:
	${PYTHON} scripts/ci_meta_scrape.py --output ci_scrape_2015.json RS03ASHS/PN03B/06-CAMHDA301/2015/
	${PYTHON} scripts/ci_meta_scrape.py --output ci_scrape_2016.json RS03ASHS/PN03B/06-CAMHDA301/2016/
	${PYTHON} scripts/ci_meta_scrape.py --output ci_scrape_2017.json RS03ASHS/PN03B/06-CAMHDA301/2017/

datapackage/movie_metadata.csv:
	${PYTHON} scripts/ci_scrape_to_csv.py --output $@ ci_scrape_*.json


.PHONY: csv datapackage/regions.csv html_to_google_drive
