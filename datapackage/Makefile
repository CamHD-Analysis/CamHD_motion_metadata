

PYTHON = python3


# Validate the data package
validate:
	${PYTHON} scripts/validate.py

## Tasks related to Google bigquery
upload_to_bigquery:
	${PYTHON} scripts/upload_to_bigquery.py



BQ = bq
BQ_PROJECT = camhd-motion-metadata
BQ_DATASET = camhd
BQ_TABLE   = regions

bq_ls:
	${BQ} ls ${BQ_PROJECT}:
	${BQ} ls ${BQ_PROJECT}:${BQ_DATASET}

bq_show:
	${BQ} show ${BQ_PROJECT}:${BQ_DATASET}.${BQ_TABLE}

bq_query:
	${BQ} query --project_id ${BQ_PROJECT} "SELECT mov_basename,start_frame,end_frame FROM ${BQ_DATASET}.${BQ_TABLE} WHERE scene_tag='d2_p0_z0' ORDER BY date_time LIMIT 6"



## Makefile rules for Conda environments

conda_install_requirements: scripts/environment.yml
	conda install --file $^

conda_export_requirements:
		conda env export > scripts/environment.yml


.PHONY: validate bq_ls bq_sample upload_to_bigquery
