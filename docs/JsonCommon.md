
# Common JSON file fields

All files contain a JSON object at the top level, which contains at least these two keys:

`contents` is an object containing string identifiers and semantic version
numbers of the data type(s) within the file.  So, for example

```
{
  "contents" : { "movie", : "1.0",
                 "frameStats": {
                   "opticalFlow": "1.1" } }
  ...
}
```

indicates the file contains "movie" data in the 1.0 file format and frameStats: a list of data about some or all of the frames in the video.   The frameStats data is version 1.1 of "opticalFlow data (described [here](OpticalFlow.md)).

Frame numbers are given in the Quicktime convention where the first frame in the movie is __1__,
and the last is __(number of frames)___.

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

At present, this JSON is set from the the Lazycache movie metadata, including
the duration in seconds, the number of frames, and the original
raw data archive URL.   The `cacheURL` field gives the Lazycache URL used
to retrieve the metadata (if applicable).
