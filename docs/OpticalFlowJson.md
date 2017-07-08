
## frameStats

``frameStats`` data is produced by the _frame_stats_ tool in the
[camhd_motion_analysis](https://github.com/CamHD-Analysis/camhd_motion_analysis)
project.  It iterates over frames in the movie and runs a set of analyses
on each frame.    The `frameStats` object at the top level is an array
of objects.   Each object contains the frame number at the top-level:

```
{
  ...
  "frameStats": [
    {
      "frameNumber": 100,
      ....
    },
    {
      "frameNumber": 200,
      ...
    },
    ...
  ],
  ...
}
```

NOTE the array is written as the movie is processed and _may not be in order._  
Also, the frames present depends on the algorithm(s) used to generate
the frame stats.
