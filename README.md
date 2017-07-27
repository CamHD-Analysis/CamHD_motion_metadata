# CamHD Motion Metadata

_DOI for all version of this dataset:_ [![DOI](https://zenodo.org/badge/90894043.svg)](https://zenodo.org/badge/latestdoi/90894043)  

Please see our [Zenodo record](https://zenodo.org/badge/latestdoi/90894043) for citation information and for DOIs associated with specific releases of the data.

[![CC-SA-4.0 License](https://i.creativecommons.org/l/by-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-sa/4.0/)

This work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).

## Introduction

>  See the [Metadata Status](docs/MetadataStatus.md) for information on the current state of the metadata.

>  _Please_ use the Github issue tracker to flag missing files, data quality issues, etc.


[CamHD](http://www.interactiveoceans.washington.edu/story/High_Definition_Video_Camera), an HD camera installed at 1500m water depth at [Axial Seamount](https://en.wikipedia.org/wiki/Axial_Seamount), generates ~13-minute HD videos of an active hydrothermal vent ecosystem, eight times a day.   These files are stored in the [Ocean Observatories Initiative](http://oceanobservatories.org/) [raw data repository](https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/).

Under the NSF OTIC-sponsored program [_Cloud-Capable Tools for CamHD Data Analysis_](https://camhd-analysis.github.io/public-www/), we are investigating the use of video analytics / machine vision to generate ancillary metadata about each video: camera motion and position, and identification of sections (sequences of frames, time bounds) within each video when the camera is still, and looking and particular known "stations" on the vent.

This repo is the primary distribution point for those metadata files.   The Git format lets us version files as they are created, flag and track data quality issues, etc.

For additional information on this project, please see [the project blog](https://camhd-analysis.github.io/public-www/)

# Data in JSON format

The "raw" data format is a set of one or more JSON files for each video in the CI.

The directory structure within this repository mirrors that of the raw data
archive.  Since we only analyze one instrument, all of the metadata files are under the
directory `RS03ASHS/PN03B/06-CAMHDA301/`.   The metadata files share a common root
name with video files, followed by a suffix which describes the metadata
(described in greater detail below).  All metadata is stored in JSON-encoded
text files, and all files use the `.json` extension.   

All JSON files contain some common fields described [here](docs/JsonCommon.md).  At present, there are two kinds of data files in the repo:

 * `*_optical_flow.json` files contain the estimated camera motion for a subset of frames in in each video.  The format is described [here](docs/OpticalFlowJson.md).

 * The optical flow files are then processed to isolate sequences where the camera motion is consistent (e.g. tilting upward, zooming in, static).   We are particularly interested in static segments and attempt to label them by comparison to a set of ground truth video sequences.

  These "regions" of consistent behavior are described in a `*_optical_flow_regions.json` file described [here](docs/OpticalFlowRegionsJson.md).

Right now, the JSON file formats are __unstable__.   The [file format](docs/JsonCommon.md) allows for semantic versioning of the file contents, and we describe format changes in the [Change Log](docs/ChangeLog.md).



# Data in CSV format

The static region information is also exported in a CSV format and includes
[Frictionless Data](http://frictionlessdata.io/) data packaging information.   The CSV file itself
is stored as [datapackage/regions.csv](datapackage/regions.csv) and the associated metadata
information is at [datapackage/datapackage.json](datapackage/datapackage.json)

The extensive [library of datapackage tools](http://frictionlessdata.io/tools/) simplifies development:

    import datapackage

    url = "https://raw.githubusercontent.com/CamHD-Analysis/CamHD_motion_metadata/master/datapackage/datapackage.json"

    dp = datapackage.DataPackage(url)

    print(dp.descriptor['title'])



The [datapackage/scripts](datapackage/scripts/) directory contains Python scripts specific
to the datapackage format.


# Data in Google Bigquery

As an experiment, the CSV version is also uploaded to [Google Bigquery](https://cloud.google.com/bigquery/), their scalable database.  This db is publicly readable and is available [here](https://bigquery.cloud.google.com/queries/camhd-motion-metadata)

The db can be accessed using standard tools.   For example, using the `bq`
 command line tool:

     >  bq query --project_id camhd-motion-metadata "SELECT mov_basename,start_frame,end_frame FROM camhd.regions WHERE scene_tag='d2_p0_z0' ORDER BY date_time LIMIT 6"

     Waiting on bqjob_r542e368cb71317b8_0000015d806335c0_1 ... (0s) Current status: DONE
     +----------------------------+-------------+-----------+
     |        mov_basename        | start_frame | end_frame |
     +----------------------------+-------------+-----------+
     | CAMHDA301-20160101T000000Z |       23601 |     23931 |
     | CAMHDA301-20160101T000000Z |       13101 |     13381 |
     | CAMHDA301-20160101T000000Z |        1711 |      2191 |
     | CAMHDA301-20160101T000000Z |        4691 |      4961 |
     | CAMHDA301-20160101T000000Z |        7531 |      7811 |
     | CAMHDA301-20160101T000000Z |       21031 |     21351 |
     +----------------------------+-------------+-----------+

## Preparation

The metadata files are generated using software these github repos:

  * [CamHD-Analysis/camhd_motion_analysis](https://github.com/CamHD-Analysis/camhd_motion_analysis) contains the C++ and Python files which perform the optical flow calculation.

  * [CamHD-Analysis/camhd-motion-analysis-deploy](https://github.com/CamHD-Analysis/camhd-motion-analysis-deploy) contains scripts and documentation on running the 'camhd_motion_analysis' in parallel on a cluster formed with Docker swarm.

The Python tools in the `scripts/` directory are also use:

  * [make_regions_files.py](docs/MakeRegionsFile.md) takes the [optical flow](docs/OpticalFlowJson.md) files as input and:

    1. Breaks the video into time frames with consistent camera behavior (camera static, zooming in, panning left, etc.).  
    1. Uses a set of hand-labelled ground truth files to attempt to label each static section with its corresponding [region](docs/Regions.md).

  See [docs/MakeRegionsFile.md](docs/MakeRegionsFile.md) for more detail.

The CSV datapackage format is prepared using the [scripts/make_csv.py](scripts/make_csv.py) script
or the `make csv` rule in the top-level Makefile.

## Todos
