
PYTHON = python3


## Convert all optical_flow_regions.json files into the flat CSV file format.
csv:  datapackage/regions.csv

.PHONY: csv datapackage/regions.csv html_to_google_drive qa

## Process only d2 right now
datapackage/regions.csv:
	${PYTHON} scripts/regions_to_datapackage.py --output $@ RS03ASHS/PN03B/06-CAMHDA301/2015/11/[23]?/*regions.json \
																									RS03ASHS/PN03B/06-CAMHDA301/2015/12/*/*regions.json \
																									RS03ASHS/PN03B/06-CAMHDA301/2016/0[1-6]/*/*regions.json \
																									RS03ASHS/PN03B/06-CAMHDA301/2016/07/[01]?/*regions.json \
																									RS03ASHS/PN03B/06-CAMHDA301/2016/07/2[0-5]/*regions.json \

html_to_google_drive:
	gsutil -m rsync -a public-read -d -r _html/ gs://camhd-region-proofs/


## Note:   this will take a long time...
ci_scrape:
	${PYTHON} scripts/ci_meta_scrape.py --output ci_scrape_2015.json RS03ASHS/PN03B/06-CAMHDA301/2015/
	${PYTHON} scripts/ci_meta_scrape.py --output ci_scrape_2016.json RS03ASHS/PN03B/06-CAMHDA301/2016/
	${PYTHON} scripts/ci_meta_scrape.py --output ci_scrape_2017.json RS03ASHS/PN03B/06-CAMHDA301/2017/

datapackage/movie_metadata.csv: ci_scrape_2015.json ci_scrape_2016.json ci_scrape_2017.json ci_scrape_2018.json ci_scrape_2019.json
	${PYTHON} pycamhd-motion-metadata/scripts/ci_scrape_to_csv.py --output $@ $^



## Run quality control scripts
qc:
	for f in quality_control/*.py; do python "$$f"; done
