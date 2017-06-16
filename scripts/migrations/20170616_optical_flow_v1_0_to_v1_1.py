#!/usr/bin/env python3
#
# Modifies *_optical_flow.json files in-place to match changes to JSON format
# made in https://github.com/CamHD-Analysis/camhd_motion_analysis/commit/53dd3c975d46076b4e7158b5145e05d9b4e12f95
#
#

import glob
import logging
import argparse
import os.path
import json


parser = argparse.ArgumentParser(description='Migrate optical flow files from v1.0 to v1.1 format')

parser.add_argument('input', metavar='N', nargs='*',
                    help='Files or paths to process')

parser.add_argument('--dry-run', dest='dryrun', action='store_true', help='Dry run, don\'t actually process')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--git-add', dest='gitadd', action='store_true', help='Run "git add" on resulting file')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )


def json_rename( j, old, new ):
    if old in j:
        j[new] = j[old]
        del j[old]
    return j


def migrate( jinput ):

    ##--- Rewrite contents block --
    ## Rename contents/frame_stats to contents/frameStats
    contents = jinput["contents"]

    json_rename( contents, "frame_stats", "frameStats" )

    ## Drop the extra "contents" layer from contents/frameStats/contents/...
    if "contents" in jinput["contents"]["frameStats"]:
        jinput["contents"]["frameStats"] = jinput["contents"]["frameStats"]["contents"]

    json_rename( contents["frameStats"], "optical_flow", "opticalFlow" )

    ## Drop the timing block, it's not correct in Dask-parallelized operations
    if "timing" in jinput:
        del jinput["timing"]

    ## Rewrite optical flow block in frame stats
    similarity_keys = ["center", "flowScale", "fromFrame", "toFrame", "imgScale", "valid", "similarity"]

    # Rename frame_stats to frameStats
    json_rename(jinput, "frame_stats", "frameStats")

    for f in jinput["frameStats"]:

        json_rename( f, "frame_number", "frameNumber")
        json_rename( f, "similarity", "opticalFlow" )

        ## Timing information is bogus when it exists
        if "performance" in f:
            del f["performance"]


    return jinput


for path in args.input:
    for inpath in glob.iglob( path, recursive=True):

        with open( inpath ) as infile:
            jinput = json.load( infile )

        joutput = migrate( jinput )

        if args.dryrun:
            continue

        with open( inpath, 'w') as outfile:
            json.dump(joutput, outfile, indent=2)
