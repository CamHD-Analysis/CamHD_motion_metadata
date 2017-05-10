# CamHD_motion_metadata

This repository stores supplementary metadata associated with the uncompressed video data from [CamHD](http://www.interactiveoceans.washington.edu/story/High_Definition_Video_Camera) stored at the [Ocean Observatories Initiative](http://oceanobservatories.org/) [raw data repository](https://rawdata.oceanobservatories.org/files/).

These metdata products are produced under the NSF OTIC-sponsored program [_Cloud-Capable Tools for CamHD Data Analysis_](https://camhd-analysis.github.io/public-www/).

The directory structure within this repository mirrors that of the raw data archive.  As we focus on CamHD, all of the metadata files is under the directory `RS03ASHS/PN03B/06-CAMHDA301/2016/01/01`.   Files are associated with video files by a common root name, while a suffix after an underscore gives the file type (described in greater detail below).  All metadata is stored in JSON-encoded text files, and all files use the `.json` extension.   

All files contain a JSON object at the top level, which contains at least these two keys:

`contents` will be an object containing string identifiers and semantic version numbers of the data type(s) within the file.  So, for example

```
{
  "contents" : { "movie", : "1.0", "optical_flow": "1.0" }
  ...
}
```

indicates the file contains "movie" data in the 1.0 file format and  "optical flow" data in the 1.0 file format.   Given the flexibility of JSON this could be determined by guess-and-check, but we provide this hint to quickly detect either breaking changes to file format or unexpected file contents.


## movie

The `movie` content type adds a top-level object `movie`:

```
{
  ...
  "movie": {
      "Duration": 839.338562011719,
      "NumFrames": 25155,
      "URL": "https://rawdata.oceanobservatories.org/files//RS03ASHS/PN03B/06-CAMHDA301/2016/01/01/CAMHDA301-20160101T000000Z.mov",
      "cacheURL": "https://camhd-app-dev.appspot.com/v1/org/oceanobservatories/rawdata/files/RS03ASHS/PN03B/06-CAMHDA301/2016/01/01/CAMHDA301-20160101T000000Z.mov"
  },
  ...
}
```

At present, this JSON is set from the the Lazycache movie metadata, including the duration in seconds, the number of frames, and the original raw data archive URL.   The `cacheURL` field gives the Lazycache URL used to retrieve the metadata.

## frame_stats

``frame_stats`` data is produced by the _frame_stats_ tool in the [camhd_motion_analysis](https://github.com/CamHD-Analysis/camhd_motion_analysis) project.  It iterates over frames in the movie and runs a set of analyses on each frame.    The `frame_stats` object at the top level is an array of objects.   Each object contains the frame number at the top-level:

```
{
  ...
  "frame_stats": [
    {
      "frame_number": 100
    },
    {
      ...
    },
    ...
  ],
  ...
}
```

NOTE the array is written as the movie is processed and _may not be in order._
