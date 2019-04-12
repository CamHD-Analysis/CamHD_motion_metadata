
PYTHON = python3


## Convert all optical_flow_regions.json files into the flat CSV file format.
csv:  datapackage/regions.csv

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
	#${PYTHON} pycamhd-motion-metadata/scripts/ci_meta_scrape.py --lazycache-url http://localhost:8080/v1/org/oceanobservatories/rawdata/files/ --output ci_scrape_2015.json RS03ASHS/PN03B/06-CAMHDA301/2015/
	#${PYTHON} pycamhd-motion-metadata/scripts/ci_meta_scrape.py --lazycache-url http://localhost:8080/v1/org/oceanobservatories/rawdata/files/ --output ci_scrape_2016.json RS03ASHS/PN03B/06-CAMHDA301/2016/
	${PYTHON} pycamhd-motion-metadata/scripts/ci_meta_scrape.py --lazycache-url http://localhost:8080/v1/org/oceanobservatories/rawdata/files/ --output ci_scrape_2017.json RS03ASHS/PN03B/06-CAMHDA301/2017/
	#${PYTHON} pycamhd-motion-metadata/scripts/ci_meta_scrape.py --lazycache-url http://localhost:8080/v1/org/oceanobservatories/rawdata/files/ --output ci_scrape_2018.json RS03ASHS/PN03B/06-CAMHDA301/2018/
	#${PYTHON} pycamhd-motion-metadata/scripts/ci_meta_scrape.py --lazycache-url http://localhost:8080/v1/org/oceanobservatories/rawdata/files/ --output ci_scrape_2019.json RS03ASHS/PN03B/06-CAMHDA301/2019/

datapackage/movie_metadata.csv: ci_scrape_2015.json ci_scrape_2016.json ci_scrape_2017.json ci_scrape_2018.json ci_scrape_2019.json
	${PYTHON} pycamhd-motion-metadata/scripts/ci_scrape_to_csv.py --output $@ $^



## Proofsheet generation code ##

LAZYCACHE_URL=http://localhost:8080/v1/org/oceanobservatories/rawdata/files/
PROOF_DATE?=2019/02
PROOF_FILENAME=$(subst /,-,$(PROOF_DATE))

proof:
	${PYTHON} pycamhd-motion-metadata/scripts/make_regions_proof_sheet.py \
			--lazycache-url ${LAZYCACHE_URL} --output _html/$(PROOF_FILENAME)-00.html \
			RS03ASHS/PN03B/06-CAMHDA301/$(PROOF_DATE)/0?/*regions.json
	${PYTHON} pycamhd-motion-metadata/scripts/make_regions_proof_sheet.py \
			--lazycache-url ${LAZYCACHE_URL} --output _html/$(PROOF_FILENAME)-01.html \
			RS03ASHS/PN03B/06-CAMHDA301/$(PROOF_DATE)/1?/*regions.json
	${PYTHON} pycamhd-motion-metadata/scripts/make_regions_proof_sheet.py \
			--lazycache-url ${LAZYCACHE_URL} --output _html/$(PROOF_FILENAME)-02.html \
			RS03ASHS/PN03B/06-CAMHDA301/$(PROOF_DATE)/[23]?/*regions.json

## Run quality control scripts
qc:
	for f in quality_control/*.py; do python "$$f"; done


.PHONY: csv datapackage/regions.csv html_to_google_drive qa proof
