

import numpy as np
import json
import time
from os import path
import pandas as pd


def clean_json( j ):

    if "frame_stats" in j:
        stats = j["frame_stats"]
        frame_num_key = "frame_number"
        optical_flow_key = "similarity"
    else:
        stats = j["frameStats"]
        frame_num_key = "frameNumber"
        optical_flow_key = "opticalFlow"

    frame_num = [ f[frame_num_key] for f in stats]
    similarities = [ f[optical_flow_key] for f in stats ]

    stats = pd.DataFrame(similarities, index=frame_num).sort_index()

    return stats

def select_valid( stats ):
    return stats[ stats.valid == True ]

def flatten_structure( valid ):

    # Break the similarity structure out into columns
    #similarity = pd.DataFrame.from_records( valid.similarity, valid.index )

    ## Convert center columns to center_x, center_y
    valid = pd.concat( [valid.center.apply( pd.Series ), valid.drop('center', axis=1)], axis=1) \
                .rename( columns={ 0: 'center_x', 1: 'center_y '} )

    valid = pd.concat( [valid.similarity.apply( pd.Series ), valid.drop('similarity', axis=1)], axis=1) \
                .rename( columns={ 0: 'scale', 1: 'theta', 2: 'trans_x', 3: 'trans_y'} )

    valid['trans'] = valid.trans_x**2 + valid.trans_y**2

    return valid


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


def classify_regions( valid, static ):

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




def region_analysis( jin ):
    stats = clean_json( jin )
    valid = flatten_structure( select_valid( stats ))

    stable = valid.loc[lambda df: df.trans < 100].loc[ lambda df: (df.scale-1).abs() < 0.01 ]


    stable_regions = contiguous_region( stable )
    classify = classify_regions( valid, stable_regions )

    classify.sort(key=lambda x: x["startFrame"])

    #regions_filename = metadata_repo + path.splitext(data_filename)[0] + '_regions.json'

    ## Write metainformation
    json_out = { 'movie': jin['movie'],
                 'contents': { 'regions': '1.1' },
                'regions': classify }

    return json_out
