

PYTHON = python3


# Validate the data package
validate:
	${PYTHON} scripts/validate.py


upload_to_bigquery:
	${PYTHON} scripts/upload_to_bigquery.py

## Makefile rules for Conda environments

conda_install_requirements: scripts/environment.yml
	conda install --file $^

conda_export_requirements:
		conda env export > scripts/environment.yml


.PHONY: validate
