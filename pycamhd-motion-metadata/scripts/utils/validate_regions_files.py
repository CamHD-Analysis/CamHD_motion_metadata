#!/usr/bin/env python3

"""
Prints a summary of validation report for the given regions files to the console.

Usage: (Running from the root directory of the repository.)
python scripts/utils/validate_regions_files.py ../RS03ASHS/PN03B/06-CAMHDA301/2018/07/2[56789]

"""

import argparse
import glob
import logging
import os

import pycamhd.motionmetadata as mmd

OPTIMAL_NUM_REGIONS = 39
NUM_REGIONS_LOWER_THRESH = 30
NUM_REGIONS_UPPER_THRESH = 50


def get_args():
    parser = argparse.ArgumentParser(description="Prints a summary of validation report for the given regions files to the console.")
    parser.add_argument('input',
                        metavar='N',
                        nargs='*',
                        help='Files or paths to process.')
    parser.add_argument('--outfile',
                        help='The output file path.')
    parser.add_argument("--log",
                        default="WARN",
                        help="Specify the log level. Default: WARN.")

    return parser.parse_args()


def validate_regions_files(args):
    out_fp = None
    if args.outfile:
        out_fp = open(args.outfile, "w")
        out_fp.write("Optimal Num Regions in a video: %s\n" % OPTIMAL_NUM_REGIONS)

    not_found_list = []
    less_regions_list = []
    more_regions_list = []

    def _process(infile):
        logging.debug("Checking for optical flow file: {}".format(infile))
        regions_file_path = "%s_regions%s" % os.path.splitext(infile)
        if not os.path.exists(regions_file_path):
            not_found_list.append(regions_file_path)
            if out_fp:
                out_fp.write("Num Regions for %s: N/A\n" % regions_file_path)
            return

        regions = mmd.RegionFile.load(regions_file_path)
        num_static_regions = len(regions.static_regions())
        if out_fp:
            out_fp.write("Num Regions for %s: %d\n" % (regions_file_path, num_static_regions))

        if num_static_regions <= NUM_REGIONS_LOWER_THRESH:
            less_regions_list.append(regions_file_path)
        elif num_static_regions >= NUM_REGIONS_UPPER_THRESH:
            more_regions_list.append(regions_file_path)


    for pathin in args.input:
        for infile in glob.iglob(pathin):
            if os.path.isdir(infile):
                infiles_path = os.path.join(infile, "*_optical_flow.json")
                for f in glob.iglob(infiles_path):
                    _process(f)
            else:
                _process(infile)

    if out_fp:
        out_fp.write("\n\n### SUMMARY ###")
        out_fp.write("\n\nNo Regions File found for: %d\n" % len(not_found_list))
        out_fp.write("\n".join(not_found_list))
        out_fp.write("\n\nLess than %s Regions File found for: %d\n" % (NUM_REGIONS_LOWER_THRESH, len(less_regions_list)))
        out_fp.write("\n".join(less_regions_list))
        out_fp.write("\n\nMore than %s Regions File found for: %d\n" % (NUM_REGIONS_UPPER_THRESH, len(more_regions_list)))
        out_fp.write("\n".join(more_regions_list))
        out_fp.close()

    return not_found_list, less_regions_list, more_regions_list


if __name__ == "__main__":
    args = get_args()
    logging.basicConfig(level=args.log.upper())
    not_found_list, less_regions_list, more_regions_list = validate_regions_files(args)

