#!/usr/bin/env python3

"""
The runner script to automate the process of creating region files for new set of videos.
1. Samples random frames (prob 0.5) from recent month's validated regions files.
2. Retrains the scene_tag_classification CNN models on the recent data.
# TODO: Complete the description.

Usage: (Running from the root directory of the repository.)
python scripts/utils/process_regions_files.py --config <path to regions_file_process_config.json>

# TODO: Add the sample config after creating.
# Sample Config is available at: <REPOSITORY_ROOT>/

# Set CAMHD_SCENETAG_DATA_DIR environment variable to the directory as a root data directory.

"""
import pycamhd.lazycache as camhd
import pycamhd.motionmetadata as mmd

from collections import defaultdict

import argparse
import logging
import os
import shutil
import subprocess

CAMHD_SCENETAG_DATA_DIR = os.environ.get("CAMHD_SCENETAG_DATA_DIR", None)

# TODO: This is sample code to running another python script using subprocess.
# Use a list of args instead of a string
input_files = ['file1', 'file2', 'file3']
my_cmd = ['cat'] + input_files
with open('myfile', "w") as outfile:
    subprocess.call(my_cmd, stdout=outfile)


def get_args():
    parser = argparse.ArgumentParser(description="The runner script to automate the process of creating region files "
                                                 "for new set of videos.")
    parser.add_argument('--config',
                        required=True,
                        help="The path to regions file process config json file")
    parser.add_argument('--lazycache-url',
                        dest='lazycache',
                        default=os.environ.get("LAZYCACHE_URL", None),
                        help='URL to Lazycache repo server. Default: Environment variable LAZYCACHE_URL.')
    parser.add_argument("--log",
                        default="INFO",
                        help="Specify the log level. Default: INFO.")

    args = parser.parse_args()

    # Set up the Lazycache connection.
    args.qt = camhd.lazycache(args.lazycache)

    return args


def merge_dataset_dirs(dataset_dirs, output_dir):
    label_counts = defaultdict(int)
    os.makedirs(output_dir)

    labels = os.listdir(dataset_dirs[0])
    for label in labels:
        os.makedirs(os.path.join(output_dir, label))

    for dataset_dir in dataset_dirs:
        for label in labels:
            for f in os.listdir(os.path.join(dataset_dir, label)):
                label_counts[label] += 1
                shutil.copy(os.path.join(dataset_dir, label, f), os.path.join(output_dir, label, f))

    print("The datasets %s have been copied to output_dir: %s" % (str(dataset_dirs), output_dir))
    print("The data distribution in combined dataset: %s" % label_counts)


if __name__ == "__main__":
    args = get_args()
    logging.basicConfig(level=args.log.upper())

    if not CAMHD_SCENETAG_DATA_DIR:
        raise ValueError("The CAMHD_SCENETAG_DATA_DIR needs to be set in the environment.")
    if not os.path.exists(CAMHD_SCENETAG_DATA_DIR):
        logging.warning("The CAMHD_SCENETAG_DATA_DIR was not found. Creating a new directory: %s"
                        % CAMHD_SCENETAG_DATA_DIR)
        os.makedirs(CAMHD_SCENETAG_DATA_DIR)

    # Call scripts in order and log messages.
    # TODO
