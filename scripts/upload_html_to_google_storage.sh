#!/bin/sh

gsutil -m rsync -a public-read -d -r _html/ gs://camhd_region_proofs/
#gsutil -m acl -r -g AllUsers:R gs://camhd_region_proofs/
