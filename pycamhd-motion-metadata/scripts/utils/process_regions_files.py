#!/usr/bin/env python3

"""
The runner script to automate the process of creating region files for new set of videos.
Note: Ensure to run this on a new branch taken from updated master.

1. Samples random frames (prob 0.5) from recent month's validated regions files.
2. Retrains the scene_tag_classification CNN models on the recent data.
# TODO: Complete the description.

Usage: (Running from the root directory of the repository.)
python scripts/utils/process_regions_files.py --config <path to regions_file_process_config.json>

# TODO: Add the sample config after creating.
# Sample Config is available at: <REPOSITORY_ROOT>/

# Set following environments variables:
1. CAMHD_MOTION_METADATA_DIR: The path to the local clone of the repository.
2. CAMHD_SCENETAG_DATA_DIR: The data directory to store train data and trained models.

"""
import pycamhd.lazycache as camhd
import pycamhd.motionmetadata as mmd

from collections import defaultdict

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time

CAMHD_MOTION_METADATA_DIR = os.environ.get("CAMHD_MOTION_METADATA_DIR", None)
CAMHD_SCENETAG_DATA_DIR = os.environ.get("CAMHD_SCENETAG_DATA_DIR", None)
CAMHD_PYTHON_EXEC_PATH = sys.executable

SCENE_TAG_TRAIN_DATA_DIR = os.path.join(CAMHD_SCENETAG_DATA_DIR, "scene_classification_data")
SCENE_TAG_MODEL_DIR = os.path.join(CAMHD_SCENETAG_DATA_DIR, "trained_classification_models")

def get_args():
    parser = argparse.ArgumentParser(description="The runner script to automate the process of creating region files "
                                                 "for new set of videos. "
                                                 "Note: Ensure to run this on a new branch taken from updated master.")
    parser.add_argument('--config',
                        required=True,
                        help="The path to regions file process config json file")
    parser.add_argument("--logfile",
                        required=True,
                        help="Specify the path to the logfile.")
    parser.add_argument('--lazycache-url',
                        dest='lazycache',
                        default=os.environ.get("LAZYCACHE_URL", None),
                        help='URL to Lazycache repo server. Default: Environment variable LAZYCACHE_URL.')
    parser.add_argument("--log",
                        default="INFO",
                        help="Specify the log level. Default: INFO.")
    parser.add_argument("--no-write",
                        action="store_true",
                        help="Specify this flag to not executive any commands.")

    args = parser.parse_args()

    # Set up the Lazycache connection.
    args.qt = camhd.lazycache(args.lazycache)

    return args


def _run(cmd_list, logfile):
    cmd = "%s %s" % (sys.executable, " ".join(cmd_list))
    with open(logfile, "a") as outfile:
        logging.info("Executing command: %s" % cmd)
        subprocess.call(cmd, stdout=outfile)


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
    logging.basicConfig(filename=args.logfile,
                        filemode='a',
                        format='[%(asctime)s - [%(levelname)s]: %(message)s',
                        datefmt='%H:%M:%S',
                        level=args.log)

    start_time = time.time()
    logging.info("Started Process Regions files.")

    if not os.path.exists(args.config):
        raise ValueError("The regions file process config does not exists: %s" % args.config)

    with open(args.config) as fp:
        config = json.load(fp)

    for env_var in [CAMHD_MOTION_METADATA_DIR, CAMHD_SCENETAG_DATA_DIR]:
        if not env_var:
            raise ValueError("The %s needs to be set in the environment." % env_var)

    if not os.path.exists(CAMHD_SCENETAG_DATA_DIR):
        logging.warning("The CAMHD_SCENETAG_DATA_DIR was not found. Creating a new directory: %s"
                        % CAMHD_SCENETAG_DATA_DIR)
        os.makedirs(CAMHD_SCENETAG_DATA_DIR)

    # Call scripts in order and log messages.
    # 1. Sample data from new_data month
    # TODO
