#!/usr/bin/env python3

"""
Note: Run this from the project root directory to have the file_paths as required by the next modules.

"""

from datetime import datetime
from dateutil import rrule

import argparse
import glob
import json
import os
import random

METADATA_ROOT_DIR_CAMHD_SUFFIX = "PN03B/06-CAMHDA301" # RS03ASHS will be the root.

def get_args():
    parser = argparse.ArgumentParser(description="Samples the ground truth region files for scene_tag classification."
                                                 "The user needs to ensure that the ground truth region files exist "
                                                 "for the given range od days.")

    parser.add_argument("--root",
                        required=True,
                        help="The root data dir where the metadata is stored - path to RS03ASHS directory.")
    parser.add_argument("--from-date",
                        required=True,
                        help="The start date for sampling the ground truth region files in yyyymmdd format.")
    parser.add_argument("--to-date",
                        required=True,
                        help="The end date for sampling the ground truth region files in yyyymmdd format.")
    parser.add_argument("--count",
                        default=10,
                        help="The number of ground truth files to be sampled.")
    parser.add_argument("--outfile",
                        required=True,
                        help="The path to the target_file to which the output needs to be written.")

    args = parser.parse_args()
    return args


def _get_ymd_ranges(from_date, to_date):
    def _get_ymd(valid_date_string):
        year = valid_date_string[:4]
        month = valid_date_string[4:6]
        day = valid_date_string[6:8]

        return (year, month, day)

    # Validate the date_string.
    for date_string in [from_date, to_date]:
        try:
            if len(date_string) != 8:
                raise ValueError("The date string needs to be in format: yyyymmdd.")

            datetime.strptime(date_string,'%Y%m%d')
        except ValueError as e:
            raise ValueError("The date string is not valid: {}. Excepetion: {}".format(date_string, e))

    required_dates = []
    for dt in rrule.rrule(rrule.DAILY,
                          dtstart=datetime.strptime(from_date, '%Y%m%d'),
                          until=datetime.strptime(to_date, '%Y%m%d')):
        required_dates.append(dt.strftime('%Y%m%d')) 

    required_dates = [_get_ymd(x) for x in required_dates]
    return required_dates


def sample_ground_truth_files(data_root_dir, from_date, to_date, count):
    """
    Samples the ground truth files from the given range of days.

    """
    all_region_files = []
    required_dates = _get_ymd_ranges(from_date, to_date)
    for date_ymd in required_dates:
        file_search_str = os.path.join(args.root,
                                       METADATA_ROOT_DIR_CAMHD_SUFFIX,
                                       date_ymd[0],
                                       date_ymd[1],
                                       date_ymd[2],
                                       "*_regions.json")
        all_region_files.extend(glob.glob(file_search_str))

    random.shuffle(all_region_files)

    return all_region_files[:count]


def write_ground_truth_file(args):
    sampled_region_files = sample_ground_truth_files(args.root, args.from_date, args.to_date, args.count)
    if os.path.exists(args.outfile):
        raise ValueError("The outfile already exists: {}".format(args.outfile))

    with open(args.outfile, "w") as fp:
        json.dump(sampled_region_files, fp, indent=2)


if __name__ == "__main__":
    args = get_args()
    write_ground_truth_file(args)
