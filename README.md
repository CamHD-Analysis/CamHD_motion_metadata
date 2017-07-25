# CamHD Motion Metadata

[![DOI](https://zenodo.org/badge/90894043.svg)](https://zenodo.org/badge/latestdoi/90894043)


>  See the [Metadata Status](docs/MetadataStatus.md) for current information on the metadata.

>  __PLEASE NOTE:__  The metadata files in this repo are generated automatically.   We're still developing our QA/QC processes!    _Please_ use the Github issue tracker to flag missing files, data quality issues, etc.


[CamHD](http://www.interactiveoceans.washington.edu/story/High_Definition_Video_Camera), an HD camera installed at 1500m water depth at [Axial Seamount](https://en.wikipedia.org/wiki/Axial_Seamount), generates ~13-minute HD videos of an active hydrothermal vent ecosystem, eight times a day.   These files are stored in the [Ocean Observatories Initiative](http://oceanobservatories.org/) [raw data repository](https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/).

Under the NSF OTIC-sponsored program [_Cloud-Capable Tools for CamHD Data Analysis_](https://camhd-analysis.github.io/public-www/), we are investigating the use of video analytics / machine vision to generate ancillary metadata about each video: camera motion and position, and identification of sections (sequences of frames, time bounds) within each video when the camera is still, and looking and particular known "stations" on the vent.

This repo is the primary distribution point for those metadata files.   The Git format lets us version files as they are created, flag and track data quality issues, etc.

For additional information on this project, please see [the project blog](https://camhd-analysis.github.io/public-www/)

## Using the data

The directory structure within this repository mirrors that of the raw data
archive.  Since we only analyze CamHD data, all of the metadata files is under the
directory `RS03ASHS/PN03B/06-CAMHDA301/`.   Metadata files share a common root
name with video files, followed by a suffix which describes the metadata
(described in greater detail below).  All metadata is stored in JSON-encoded
text files, and all files use the `.json` extension.   

All JSON files contain some common fields described [here](docs/JsonCommon.md).  At present, there are two kinds of data files in the repo:

 * `*_optical_flow.json` files contain the estimated camera motion for a subset of frames in in each video.  The format is described [here](docs/OpticalFlowJson.md).

 * The optical flow files are then processed to isolate sequences where the camera motion is consistent (e.g. tilting upward, zooming in, static).  These "regions" of consistent behavior are described in a `*_optical_flow_regions.json` file described [here](docs/OpticalFlowRegionsJson.md).

Right now, the JSON file formats are __unstable__.   The [file format](docs/JsonCommon.md) allows for semantic versioning of the file contents, and we describe format changes in the [Change Log](docs/ChangeLog.md).


## License / Citing the data

[![CC-SA-4.0 License](https://i.creativecommons.org/l/by-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-sa/4.0/)

This work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).

Please see out [Zenodo record](https://zenodo.org/badge/latestdoi/90894043)


## How the files are generated.

The metadata files are generated using software these github repos:

  * [CamHD-Analysis/camhd_motion_analysis](https://github.com/CamHD-Analysis/camhd_motion_analysis) contains the C++ and Python files which perform the optical flow calculation.

  * [CamHD-Analysis/camhd-motion-analysis-deploy](https://github.com/CamHD-Analysis/camhd-motion-analysis-deploy) contains scripts and documentation on running the 'camhd_motion_analysis' in parallel on a cluster formed with Docker swarm.

As well as Python tools included in the `scripts/` directory of this repo:

  * [make_regions_files.py](docs/MakeRegionsFile.md) takes the [optical flow](docs/OpticalFlowJson.md) files as input and:

    1. Breaks the video into time frames with consistent camera behavior (camera static, zooming in, panning left, etc.).  
    1. Uses a set of hand-labelled ground truth files to attempt to label each static section with its corresponding [region](docs/Regions.md).

  See [docs/MakeRegionsFile.md](docs/MakeRegionsFile.md) for more detail.

## Todos

 [ ] Use photometric comparison to squash identical segments
