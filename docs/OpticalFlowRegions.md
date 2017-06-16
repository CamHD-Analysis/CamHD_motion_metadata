

## regions

`regions` metadata describes continuous sections of video which have been
determined to show the same kind of motion.  At the top level, the `regions`
object is an array of objects, each of which describes a region:

```
    ...
    "contents": {
        "regions": "1.0"
    },
    "regions": [
        {
            "startFrame": 580,
            "endFrame": 1050,
            "type": "static",
            "stats": {
                "scaleMean": 0.999919751891621,
                "txMean": -0.007306357788220547,
                "tyMean": -0.0038538576792083563,
                "size": 611
            }
        },
        ...
    },
...
}
```

Each region is described by `startFrame` and `endFrame` fields which give the beginning and end of the region in frames, a `type` label, and supplementary stats from the region extraction process.

The types are:

 * `static`:  camera is not moving or zooming
 * `zoom_in` or `zoom_out`:  camera is zooming.  If the camera is determined to be zooming, the translation is ignored
 * `N`,`NW`, `NE`, etc.:  camera is translating.  Directions are approximate with North being tilting upwards, South being tilting downward, East being panning rightward, etc.
 * `short`:  Segment is too short to determine motion
 * `unknown`:  Unable to determine motion
