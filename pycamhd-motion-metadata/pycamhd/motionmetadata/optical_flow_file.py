

import json
from os import path
import subprocess

import pandas as pd

from .git_utils import *


def clean_json(j):

    if "frame_stats" in j:
        stats = j["frame_stats"]
        frame_num_key = "frame_number"
        optical_flow_key = "similarity"
    elif "frameStats" in j:
        stats = j["frameStats"]
        frame_num_key = "frameNumber"
        optical_flow_key = "opticalFlow"
    else:
        raise Exception("File does not appear to contain optical flow data")

    frame_num = [f[frame_num_key] for f in stats]
    similarities = [f[optical_flow_key] for f in stats]

    stats = pd.DataFrame(similarities, index=frame_num).sort_index()

    return stats


def select_valid(stats):
    return stats[stats.valid == True]


def flatten_structure(valid):

    # Break the similarity structure out into columns
    #similarity = pd.DataFrame.from_records( valid.similarity, valid.index )

    # Convert center columns to center_x, center_y
    valid = pd.concat([valid.center.apply(pd.Series),
                       valid.drop('center', axis=1)], axis=1) \
                       .rename(columns={0: 'center_x', 1: 'center_y '})

    valid = pd.concat([valid.similarity.apply( pd.Series),
                      valid.drop('similarity', axis=1)], axis=1) \
                      .rename(columns={0: 'scale', 1: 'theta',
                                        2: 'trans_x', 3: 'trans_y'})

    if not 'trans_x' in valid or not 'trans_y' in valid:
        return pd.DataFrame({'valid' : []})

    valid['trans'] = valid.trans_x**2 + valid.trans_y**2

    return valid


class OpticalFlowFile:

    def __init__(self, filename, flatten = True):
        self.filename = filename

        with open(filename) as f:
            self.json = json.load(f)

        if flatten:
            stats = clean_json(self.json)
            self.valid = flatten_structure(select_valid(stats))

        self.mov = self.json['movie']['URL']
        self.basename = path.splitext(path.basename(self.mov))[0]

    def path(self):
        return self.filename

    def git_rev(self):
        return git_revision(self.filename)
