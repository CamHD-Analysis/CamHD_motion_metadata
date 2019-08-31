# Basic Region Classification with a Pretrained CNN

This introduction covers how to classify and validate regions using a pretrained cnn model. It uses the following three scripts:

* `make_regions_file.py`
* `make_regions_proof_sheet.py`
* `make_regions_csv_sheet.py`

The latter two can be run simultaneously after the region files are created.

Keep in mind that these are to be run from the root directory, or else folders may appear in unexpected locations.

## Requirements

Requirements are specified in `datapackage/scripts/environment.yml`.

## PyCamHD Package

The `lazycache` subpackage must be manually installed from the [lazycache repository](https://github.com/CamHD-Analysis/pycamhd-lazycache).

Both the motionmetadata and region_analysis subpackages under `pycamhd-motion-metadata/pycamhd` must also be manually installed.

## Environment Variables

There are three environment variables to configure:

* `CAMHD_SCENETAG_DATA_DIR=/home/user/Desktop/CamHD_motion_metadata`
* `CAMHD_MOTION_METADATA_DIR=/home/user/Desktop/CamHD_motion_metadata`
* `LAZYCACHE_URL="https://cache.camhd.science/v1/org/oceanobservatories/rawdata/files"`

`CAMHD_SCENETAG_DATA_DIR` provides the path to where the models are located. Inside this directory should be folder called `trained_classification_models` which contains the necessary CNN models. While it is recommended that this is the same as `CAMHD_MOTION_METADATA_DIR`, it is possible to specify a different path.
`CAMHD_MOTION_METADATA_DIR` points to wherever the repository is stored.
`LAZYCACHE_URL` specifies the URL for lazycache, used to retrieve images. Note that http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files redirects to the same site; however query strings are lost when redirecting.

## Pretrained CNN Model

The pretrained CNN model can be downloaded via the link in `trained_classification_models/links.txt` and should be placed in the `trained_classification_models` folder in the directory specified by `CAMHD_SCENETAG_DATA_DIR`. 

Custom configurations of the CNN can be made in `pycamhd-motion-metadata/pycamhd/region_analysis/scene_tag_classifiers_meta.json`. Creating a new configuration and specifying it as the most recent is preferable to overriding old configurations.

## make_regions_file.py

This is the program that actually creates the regions files. It first segments the optical flow files into regions, then classifies the static regions with scene tags.

`python pycamhd-motion-metadata/scripts/make_regions_files.py input RS03ASHS/PN03B/06-CAMHDA301/2019/05/*/*_optical_flow.json --use-cnn --log debug --force`

There are a variety of arguments available for customization, but the above is most likely quite sufficient.

## make_regions_proof_sheet.py

This creates an html proof sheet that can be used to visually confirm that the regions are classified correctly. Thumbnails for each region are downloaded and are displayed in a grid for ease of use.

`python pycamhd-motion-metadata/scripts/make_regions_proof_sheet.py input RS03ASHS/PN03B/06-CAMHDA301/2019/0[456]/*/*_regions.json --log debug`

The default arguments are quite sufficient here. The program uses a hard coded sequence of scene tags for reference by default; using ground truth files (with --ground-truth) may result in duplicate or missing scene tags.

## make_regions_csv_sheet.py

This creates a csv spreadsheet that summarizes the region classification results.

`python pycamhd-motion-metadata/scripts/make_regions_csv_sheet.py input RS03ASHS/PN03B/06-CAMHDA301/2019/*/*/*_regions.json --log debug`

If comparing within CNN configurations, the unknown and error numbers are useful. Since these are dependent on thresholds set in the configurations, these are not comparable across configurations.
If comparing across CNN configurations, the percentile information provides an effective analysis of how the CNN is performing.