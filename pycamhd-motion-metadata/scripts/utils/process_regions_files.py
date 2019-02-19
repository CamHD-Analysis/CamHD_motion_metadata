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

from collections import defaultdict

import argparse
import copy
import json
import logging
import os
import random
import shutil
import subprocess
import sys
import time

CAMHD_MOTION_METADATA_DIR = os.environ.get("CAMHD_MOTION_METADATA_DIR", None)
CAMHD_SCENETAG_DATA_DIR = os.environ.get("CAMHD_SCENETAG_DATA_DIR", None)

# Paths relative to CAMHD_SCENETAG_DATA_DIR.
RELATIVE_TRAIN_DATA_DIR = "scene_classification_data"
RELATIVE_MODEL_DIR = "trained_classification_models"

# Note: If the classification model is updated, this config also needs to be updated.
DEFAULT_CNN_MODEL_CONFIG = {
    "model_name": "<>",
    "model_path": "<>",
    "type": "classification",
    "input_shape": [256, 256, 3],
    "rescale": True,
    "classes": [
        "d5A_p0_z0",
        "d5A_p0_z1",
        "d5A_p0_z2",
        "d5A_p1_z0",
        "d5A_p1_z1",
        "d5A_p2_z0",
        "d5A_p2_z1",
        "d5A_p3_z0",
        "d5A_p3_z1",
        "d5A_p3_z2",
        "d5A_p4_z0",
        "d5A_p4_z1",
        "d5A_p4_z2",
        "d5A_p5_z0",
        "d5A_p5_z1",
        "d5A_p5_z2",
        "d5A_p6_z0",
        "d5A_p6_z1",
        "d5A_p6_z2",
        "d5A_p7_z0",
        "d5A_p7_z1",
        "d5A_p8_z0",
        "d5A_p8_z1"
    ]
}


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


def _run(cmd_list, logfile, py_script=False, restrict_gpu=None, no_write=False, allow_error=False):
    cmd = []
    if restrict_gpu:
        cmd.append("CUDA_VISIBLE_DEVICES=%s" % restrict_gpu)

    if py_script:
        cmd.append(sys.executable)

    cmd.extend(cmd_list)
    cmd_str = " ".join(cmd)

    with open(logfile, "a") as outfile:
        logging.info("Executing command: %s" % cmd_str)
        if not no_write:
            error_code = subprocess.call(cmd, stdout=outfile, stderr=outfile)
            if error_code != 0 and not allow_error:
                raise RuntimeError("The cmd failed at runtime with error_code %s: %s" % (error_code, cmd_str))

            return error_code


def merge_dataset_dirs(base_train_data_dir, new_reg_train_data_dir, output_dir, base_train_data_prob=1):
    def _sample_prob(prob):
        """
        Returns True or False based on the given probability. Bernoulli trial with given probability.

        """
        r = random.uniform(0, 1)
        # TODO: Check if this is correctly sampling.
        if r <= prob:
            return True

        return False

    label_counts = defaultdict(int)
    os.makedirs(output_dir)

    labels = os.listdir(base_train_data_dir)
    for label in labels:
        os.makedirs(os.path.join(output_dir, label))

    for i, dataset_dir in enumerate([base_train_data_dir, new_reg_train_data_dir]):
        for label in labels:
            for f in os.listdir(os.path.join(dataset_dir, label)):
                # The i == 0 condition ensures that sampling probability is applied only to base_train_data_dir.
                if i == 0 and not _sample_prob(base_train_data_prob):
                    continue

                label_counts[label] += 1
                shutil.copy(os.path.join(dataset_dir, label, f), os.path.join(output_dir, label, f))

    logging.info("The base_train_data_dir %s and new_reg_train_data_dir %s have been merged to output_dir: %s"
                 % (base_train_data_dir, new_reg_train_data_dir, output_dir))
    logging.info("The data distribution in combined dataset: %s" % label_counts)


def process_config(config, args):
    def _get_next_model_version(current_model_name, deployment):
        # TODO: Define better model name versioning convention.
        if deployment not in current_model_name:
            new_model_name = "scene_classifier_cnn-%s-v0.1" % deployment
        else:
            cur_version_id = int(current_model_name.split(".")[1])
            next_version = cur_version_id + 1
            new_model_name = "scene_classifier_cnn-%s-v0.%d" % (deployment, next_version)

        return new_model_name

    def _get_monthly_input_optical_flow_files_wild_card(year, month, deployment):
        if deployment == "d5A":
            rel_path_wild_cards = ["RS03ASHS/PN03B/06-CAMHDA301/%s/%s/0[456789]" % (year, month),
                                   "RS03ASHS/PN03B/06-CAMHDA301/%s/%s/1[123456789]" % (year, month),
                                   "RS03ASHS/PN03B/06-CAMHDA301/%s/%s/2[123456789]" % (year, month),
                                   "RS03ASHS/PN03B/06-CAMHDA301/%s/%s/3[01]" % (year, month)]

            rel_path_long_regions_wild_card = ("RS03ASHS/PN03B/06-CAMHDA301/%s/%s/*/*T000000_optical_flow_regions.json"
                                               % (year, month))
        else:
            raise ValueError("Deployment not supported: %s" % deployment)

        optical_flow_files_wild_cards = [os.path.join(CAMHD_MOTION_METADATA_DIR, x) for x in rel_path_wild_cards]
        long_regions_wild_card = os.path.join(CAMHD_MOTION_METADATA_DIR, rel_path_long_regions_wild_card)
        return " ".join(optical_flow_files_wild_cards), long_regions_wild_card

    scene_tag_train_data_dir = os.path.join(CAMHD_SCENETAG_DATA_DIR, RELATIVE_TRAIN_DATA_DIR)
    scene_tag_model_dir = os.path.join(CAMHD_SCENETAG_DATA_DIR, RELATIVE_MODEL_DIR)

    deployment = config["deployment"]

    prev_start_time = time.time()
    logging.info("Started Process Regions files from config: \n%s" % str(config))

    # Call scripts in order and log messages.
    # 1. Sample data from new_data month
    logging.info("STEP: Sample data from new validated region files.")
    py_file = os.path.join(CAMHD_MOTION_METADATA_DIR,
                           "pycamhd-motion-metadata",
                           "scripts",
                           "utils",
                           "sample_random_data.py")
    new_reg_train_data_dir = os.path.join(scene_tag_train_data_dir, config["new_reg_train_data_dirname"])
    cmd_list = [
        py_file,
        os.path.expandvars(config["new_validated_reg_files"]),
        "--scenes",
        "d5A_p0_z0,d5A_p0_z1,d5A_p0_z2,d5A_p1_z0,d5A_p1_z1,d5A_p2_z0,d5A_p2_z1,d5A_p3_z0,d5A_p3_z1,d5A_p3_z2,"
        "d5A_p4_z0,d5A_p4_z1,d5A_p4_z2,d5A_p5_z0,d5A_p5_z1,d5A_p5_z2,d5A_p6_z0,d5A_p6_z1,d5A_p6_z2,d5A_p7_z0,"
        "d5A_p7_z1,d5A_p8_z0,d5A_p8_z1",
        "--prob",
        str(config["new_reg_sampling_prob"]),
        "--output",
        new_reg_train_data_dir,
        "--width 256",
        "--height 256"
    ]
    _run(cmd_list, args.logfile, py_script=True, no_write=args.no_write)

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    # 2. Merge data with base data.
    logging.info("STEP: Merge the train datasets.")
    base_train_data_dir = os.path.join(scene_tag_train_data_dir, config["base_train_data_dirname"])
    merged_train_data_dir = os.path.join(scene_tag_train_data_dir, config["merged_train_data_dirname"])
    base_train_data_prob = config["base_train_data_prob"]
    if not args.no_write:
        merge_dataset_dirs(base_train_data_dir,
                           new_reg_train_data_dir,
                           merged_train_data_dir,
                           base_train_data_prob=base_train_data_prob)
    else:
        logging.info("The base_train_data_dir %s and new_reg_train_data_dir %s will be merged to output_dir: %s"
                     % (base_train_data_dir, new_reg_train_data_dir, merged_train_data_dir))

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    # 3. Train the CNN on the new train data.
    # TODO: Add Transfer learning support.
    logging.info("STEP: Train the CNN on the new train data.")
    classifiers_meta_file = os.path.join(CAMHD_MOTION_METADATA_DIR,
                                         "pycamhd-motion-metadata",
                                         "pycamhd",
                                         "region_analysis",
                                         "scene_tag_classifiers_meta.json")
    with open(classifiers_meta_file) as fp:
        classifiers_meta_dict = json.load(fp)

    new_model_name = _get_next_model_version(classifiers_meta_dict["latest_model"], deployment)
    py_file = os.path.join(CAMHD_MOTION_METADATA_DIR,
                           "pycamhd-motion-metadata",
                           "pycamhd",
                           "region_analysis",
                           "train_cnn_scene_classifier.py")
    model_outfile = os.path.join(scene_tag_model_dir, "%s.hdf5" % new_model_name)
    cmd_list = [
        py_file,
        "--func train_cnn",
        "--data-dir",
        merged_train_data_dir,
        "--classes SCENE_TAGS",
        "--deployment",
        deployment,
        "--val-split",
        str(config.get("val_split", 0.25)),
        "--epochs",
        str(config.get("epochs", 100)),
        "--batch-size",
        str(config.get("batch_size", 8)),
        "--model-outfile",
        model_outfile
    ]
    _run(cmd_list, args.logfile, py_script=True, restrict_gpu="0", no_write=args.no_write)

    model_config = copy.copy(DEFAULT_CNN_MODEL_CONFIG)
    model_config["model_name"] = new_model_name
    model_config["model_path"] = os.path.join("$CAMHD_SCENETAG_DATA_DIR",
                                              RELATIVE_MODEL_DIR,
                                              os.path.basename(model_outfile))
    classifiers_meta_dict["trained_models"][new_model_name] = model_config
    if not args.no_write:
        with open(classifiers_meta_file, "w") as fp:
            json.dump(classifiers_meta_dict, fp, indent=4, sort_keys=True)

    # XXX: Using 'warning' to highlight important informational log.
    logging.info("The Model re-training has completed, and the new model is saved at %s. "
                 "And the classifier_meta_file is updated: %s."
                 % (model_outfile, classifiers_meta_file))
    logging.warning("The new trained model can be shared by uploading to the Google Drive.")
    logging.warning("The train and validation split of the current train data can be deleted.")

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    # 4. Make region files for input_optical_flow_files.
    logging.info("STEP: Make region files for input_optical_flow_files.")
    long_regions_files = None
    if "monthly" in config:
        year, month = config["monthly"].split("-")
        input_optical_flow_files_wild_card, long_regions_files = \
            _get_monthly_input_optical_flow_files_wild_card(year, month, deployment)
    else:
        input_optical_flow_files_wild_card = os.path.expandvars(config["input_optical_flow_files"])

    py_file = os.path.join(CAMHD_MOTION_METADATA_DIR,
                           "pycamhd-motion-metadata",
                           "scripts",
                           "make_regions_files.py")
    cmd_list = [
        py_file,
        input_optical_flow_files_wild_card,
        "--use-cnn"
    ]
    _run(cmd_list, args.logfile, py_script=True, no_write=args.no_write)

    if long_regions_files:
        cmd_list = ["rm", long_regions_files]
        _run(cmd_list, args.logfile, py_script=False, no_write=args.no_write)

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    # 5. Create Validation Report.
    logging.info("STEP: Create Validation Report.")
    py_file = os.path.join(CAMHD_MOTION_METADATA_DIR,
                           "pycamhd-motion-metadata",
                           "scripts",
                           "utils",
                           "validate_regions_files.py")
    cmd_list = [
        py_file,
        input_optical_flow_files_wild_card,
        "--outfile",
        os.path.expandvars(config["validation_report_path"])
    ]
    _run(cmd_list, args.logfile, py_script=True, no_write=args.no_write)

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    # 6. Create Proofsheet.
    logging.info("STEP: Create Proofsheet.")
    py_file = os.path.join(CAMHD_MOTION_METADATA_DIR,
                           "pycamhd-motion-metadata",
                           "scripts",
                           "make_regions_proof_sheet.py")
    cmd_list = [
        py_file,
        input_optical_flow_files_wild_card,
        "--output",
        os.path.expandvars(config["proofsheet_path"])
    ]
    _run(cmd_list, args.logfile, py_script=True, no_write=args.no_write)

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    logging.info("Completed Processing Regions files and the proofsheets have been generated.")
    logging.warning("The proofsheets can be used to manually validate and correct the region files scene_tags.")
    logging.warning("The corrected and validated regions files need to be pushed to the Git Repository.")

    # 7. Generate Performance Evaluation Report.
    py_file = os.path.join(CAMHD_MOTION_METADATA_DIR,
                           "pycamhd-motion-metadata",
                           "scripts",
                           "utils",
                           "get_performance_metrics.py")
    cmd_list = [
        "python",
        py_file,
        input_optical_flow_files_wild_card,
        "--labels",
        os.path.join(CAMHD_MOTION_METADATA_DIR,
                     "classification",
                     "labels",
                     "%s_labels.json" % deployment),
        "--outfile",
        os.path.join(CAMHD_MOTION_METADATA_DIR,
                     "classification",
                     "performance_evaluation",
                     "model_eval-%s.csv" % config["name"])
    ]
    logging.warning("Use the following command to get generate the Performance Evaluation Report: \n%s"
                    % " ".join(cmd_list))
    logging.warning("The Performance Evaluation Report need to be generated and pushed to the Git Repository.")

    cur_time = time.time()
    logging.info("Time taken for complete processing (sec): %s" % (cur_time - prev_start_time))


if __name__ == "__main__":
    args = get_args()
    logging.basicConfig(filename=args.logfile,
                        filemode='a',
                        format='[%(asctime)s - [%(levelname)s]: %(message)s',
                        datefmt='%H:%M:%S',
                        level=args.log)

    if not os.path.exists(args.config):
        raise ValueError("The regions file process config does not exists: %s" % args.config)

    with open(args.config) as fp:
        config = json.load(fp)

    # Checking the environment variables.
    if not CAMHD_MOTION_METADATA_DIR:
        raise ValueError("The CAMHD_MOTION_METADATA_DIR variable needs to be set in the environment.")

    if not CAMHD_SCENETAG_DATA_DIR:
        raise ValueError("The CAMHD_SCENETAG_DATA_DIR variable needs to be set in the environment.")

    if not os.path.exists(CAMHD_SCENETAG_DATA_DIR):
        raise ValueError("The $CAMHD_SCENETAG_DATA_DIR does not exist: %s" % CAMHD_SCENETAG_DATA_DIR)

    # TODO: Add mailing support.
    process_config(config, args)

