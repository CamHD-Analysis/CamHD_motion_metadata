Twenty-Thousand Foot View
=========================

[CamHD](http://oceanobservatories.org/instrument-class/camhd/) is a HD camera installed on the
[Ocean Observatories Initiative](http://oceanobservatories.org) [Cabled Array](http://oceanobservatories.org).

![](http://oceanobservatories.org/wp-content/uploads/2015/09/lights_sdi1_2015-07-099_27_26_19006_med.jpg)

_Credit: NSF-OOI/UW/ISS; Dive R1835; V15_

It comes on every three hours and captures a pre-programmed 12 minute sequence of pan, tilt, and zooms examining the
surface of Mushroom, an active hydrothermal vent on Axial Seamount.

This video is stored on shore as both Apple Prores ("Uncompressed HD") and H.264 / MP4, both on the [OOI RawData server](https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2017/11/14/).

When it came time to analyze this data, we ran into two big problems:

1. The uncompress data is too voluminous to download, but there is not processing attached to the
raw data server.

2. While the camera's motion is consistent between videos, the exact position of the camera
at a given time in a video can vary by quite a bit due to small timing difference, motion slop, etc.

This repository stores our solution to problem \#2.   We've gone through the "standard sequence" of camera moves and
labelled each of the times where the camera _isn't_ moving.   There are 42 of these "static regions"
in the camera motion, with some of them being repeated views of the same place.   Examples of each region can be found in [Regions.md](Regions.md).

# High Level

The overall processing is somewhat convoluted.  Here's a __very__ high level view:

![](images/twenty_thousand_view_one.svg)

CamHD ProRes files are delivered to the OOI Cyber-Infrastructure Rawdata server.

The [camhd-motion-analysis](https://github.com/CamHD-Analysis/camhd-motion-analysis) program
then analyzes the entire movie, estimating the camera motion (pan, tilt, zoom) throughout the whole movie:

![](images/optical_flow_sample.jpg)

The results of this analysis are stored in this repository as a [JSON file](Json_Optical_Flow_File_Format.md), one per movie.

This JSON file is then loaded by a [Python script](https://github.com/CamHD-Analysis/CamHD_motion_metadata/blob/master/scripts/make_regions_files.py) which finds the segments of each movie where the camera is believed to be static (the yellow bands in the image above).   Using a set of reference data files, it attempts to label each of those static segments using the naming scheme defined [here](Regions.md).  The result of this labelling is then stored as a separate [JSON file](Json_Regions_File_Format.md) in this repository, again, one per movie.   

This regions file can then be loaded and used for analysis.  We also provide a simple [Python module](https://github.com/CamHD-Analysis/pycamhd-motion-metadata) which provides a light OO wrapper around the JSON files.

# Low-Level

Here's a more complete diagram:

![](images/twenty_thousand_view_two.svg)


Movie processing is coordinated through a [job queue](http://python-rq.org) running on a Redis server.   A scheduled
"injector" program checks the raw data server and looks for files which haven't been processed yet.

Optical flow analysis is expensive, so it's spread out across multiple machines.   This is coordinated using [Docker swarms](https://docs.docker.com/engine/swarm/).  As they're all coordinated by RQ, multiple swarms can be processing data at one time.  Each swarm runs two different types of Docker images:

 * `lazycache` containers contain an instance of [Lazycache](https://github.com/amarburg/go-lazycache) a
  Go-based REST-ful service which:

   * Converts the OOI raw data server directory structure to machine-readable JSON
   * Reads movie metadata (length, size) from the OOI raw data server
   * Extracts individual frames from movies on the OOI raw data server.

  Lazycache is the secret sauce as it allows the rest of the processing to run (albeit a bit slowly)
    without having a local copy of the data.



  * The other nodes run a Python script from [camhd-motion-analysis-deploy](https://github.com/CamHD-Analysis/camhd-motion-analysis-deploy).  This client waits for jobs to be available in the RQ database.   Right now, it's a wrapper around some C++ code based on [OpenCV](https://opencv.org) and [Ceres](http://ceres-solver.org).   Yeah, ugly, I know.   The end result is the [optical flow file](Json_Optical_Flow_File_Format.md).


  * The static region analysis is run manually right now, as the results require more careful quality control.   It's all initiated from the [make_regions_file.py script](https://github.com/CamHD-Analysis/CamHD_motion_metadata/blob/master/scripts/make_regions_files.py),
  but it actually proceeds in two steps.   The first step identifies the static regions --- this is cheap --- then writes the results to
  a [regions file](Json_Regions_File_Format.md) with static regions, but without labels.

   The second step labels the static regions, and re-writes the regions file.


  * Once the regions file has been created, there are a couple of post-processing scripts:

     * [make_regions_proof_sheet.py](https://github.com/CamHD-Analysis/CamHD_motion_metadata/blob/master/scripts/make_regions_proof_sheet.py) reads one or more regions files and produces an HTML-based "proof sheet" which can be used to check data quality.

    * [regions_to_datapackage.py](https://github.com/CamHD-Analysis/CamHD_motion_metadata/blob/master/scripts/regions_to_datapackage.py) reads all of the  regions JSON  files and produces a CSV file which complies with the [Frictionless Data](http://frictionlessdata.io) specification.  This file is stored as as `regions.csv` in the  [datapackage/](https://github.com/CamHD-Analysis/CamHD_motion_metadata/tree/master/datapackage) directory.   The directory also contains scripts and examples on how to use this data.
