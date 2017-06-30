

import numpy as np
import json
import time
from os import path
import pandas as pd

find_regions_version = "1.0"

from .region_file import *


def contiguous_region(series, delta = 10):
    series['dt'] = series.index.to_series().diff(1).fillna(0)
    series['block'] = (series.index.to_series().diff(1) > (delta*1.01) ).cumsum()
    #print(series)

    blocks = series.groupby('block')
    #print(blocks.groups)

    static_regions = []
    for name,group in blocks:
        static_regions += [ [ np.asscalar(group.index.min()), np.asscalar(group.index.max()) ] ]

    ## Drop static regions which are too short
    static_regions = [r for r in static_regions if (r[1]-r[0] > 1)]

    return static_regions


def analyze_regions( valid, static ):

    regions = []
    for r in static:
        regions.append( {"startFrame": r[0],
                        "endFrame": r[1],
                        "type": "static",
                        "stats": calc_stats(valid, r) } )

    ## Now fill in the regions between the static sections
    for i in range(0, len(static)-1):
        start = static[i][1]+10;    ## Hm, 10 is hard coded right now...
        end = static[i+1][0];

        bounds = [start,end]

        region = analyze_bounds( valid, bounds )
        if region: regions.append( region )

    return regions


def calc_stats( series, bounds ):
    subset = series.iloc[lambda df: df.index >= bounds[0]].iloc[lambda df: df.index < bounds[1]]

    return {
        "scaleMean": subset.scale.mean(),
        "txMean": subset.trans_x.mean(),
        "tyMean": subset.trans_y.mean(),
        "size": np.asscalar(subset.size)
    }


def analyze_bounds( series, bounds ):
    ## heuristics for now
    #print(bounds)

    stats = calc_stats( series, bounds )

    out = {"startFrame": bounds[0],
            "endFrame": bounds[1],
           "type": "unknown",
          "stats": stats}

    if stats["size"] < 2:
        out["type"] = "short"
        return out

    if stats["scaleMean"] > 1.05: out["type"] = "zoom_in"
    if stats["scaleMean"] < 0.95: out["type"] = "zoom_out"

    ## Ugliness
    if stats["txMean"] > 10:
        if stats["tyMean"] > 10:
            out["type"] = "NW"
        elif stats["tyMean"] < -10:
            out["type"] = "SW"
        else:
            out["type"] = "W"
    elif stats["txMean"] < -10:
        if stats["tyMean"] > 10:
            out["type"] = "NE"
        elif stats["tyMean"] < -10:
            out["type"] = "SE"
        else:
            out["type"] = "E"
    elif stats["tyMean"] > 10:
            out["type"] = "N"
    elif stats["tyMean"] < -10:
            out["type"] = "S"


    return out


def find_regions(oflow):

    stable = oflow.valid.loc[lambda df: df.trans < 100].loc[ lambda df: (df.scale-1).abs() < 0.01 ]

    stable_regions = contiguous_region(stable)
    classify = analyze_regions(oflow.valid, stable_regions)

    classify.sort(key=lambda x: x["startFrame"])

    # Write metainformation
    return RegionFile.from_optical_flow(oflow, regions=classify)
