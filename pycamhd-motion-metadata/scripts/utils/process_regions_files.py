#!/usr/bin/env python3

"""
The runner script to automate the process of creating region files for new set of videos.
Note: Ensure to run this on a new branch taken from updated master.

# Set following environments variables:
1. CAMHD_MOTION_METADATA_DIR: The path to the local clone of the repository.
2. CAMHD_SCENETAG_DATA_DIR: The data directory to store train data and trained models.

STEP 1: Sample data from new validated region files.
STEP 2: Merge the train datasets.
STEP 3: Train the CNN on the new train data.
STEP 4: Make region files for input_optical_flow_files.
STEP 5: Create Validation Report.
STEP 6: Create Proofsheet.

After completing these steps by running this script, the following tasks need to be done:
MANUAL Steps (These steps appear as warnings in the logs):
1.1 The classifier_meta_file (scene_tag_classifiers_meta.json) would be updated and need be pushed to Git Repository.
1.2 The new trained model need be shared by uploading to the Google Drive.
1.3 The train and validation split of the current train data can be deleted.

2.1 The validation report would be created, and need to be pushed to Git Repository.

3.1 The proofsheets can be used to manually validate and correct the region files scene_tags.
3.2 The corrected and validated regions files need to be pushed to the Git Repository.
3.3 The Performance Evaluation Report need to be generated and pushed to the Git Repository.

Usage: (Running from the root directory of the repository.)
    python process_regions_files.py --config <path to regions_file_process_config.json> --logfile <path_to_logfile>

# Region Files Process Config (JSON file) documentation:
{
    "version": 0.1,       # The version id for the process workflow.
    "deployment": "d5A",  # The deployment tag.
    "name": "201901",     # The name as an identifier for this config file.

    # A bash wildcard referring to the regions files which have been recently validated, but not included in training.
    "new_validated_reg_files": "$CAMHD_MOTION_METADATA_DIR/RS03ASHS/PN03B/06-CAMHDA301/2018/12/*",

    # Name of the directory for train data sampled from 'new_validated_reg_files'.
    # It will be stored in $CAMHD_SCENETAG_DATA_DIR/scene_classification_data.
    "new_reg_train_data_dirname": "set_201812",

    # Probability to be used while sampling frames from 'new_validated_reg_files'.
    "new_reg_sampling_prob": 0.5,

    # Name of the directory containing the train data to which the data from 'new_reg_train_data_dirname'
    # needs to be appended. It could be the train data from the previous model training.
    # It will be taken from (prefixed with) $CAMHD_SCENETAG_DATA_DIR/scene_classification_data.
    "base_train_data_dirname": "set_201811_train_data",

    # Probability to be used while sampling train data from 'base_train_data_dirname'.
    "base_train_data_prob": 0.5,

    # Name of the directory for merged train data including train data
    # from 'base_train_data_dirname' and 'new_reg_train_data_dirname'.
    # It will be stored in $CAMHD_SCENETAG_DATA_DIR/scene_classification_data.
    "merged_train_data_dirname": "set_201812_train_data",

    "val_split": 0.25,    # Optional. The proportion of train data from 'merged_train_data_dirname' to be used as validation data. Defaulted to 100.
    "epochs": 100,        # Optional. The number of epochs. Defaulted to 100.
    "batch_size": 8,      # Optional. The batch-size for training. Defaulted to 8.
    "restrict_gpu": "0",  # Optional. The GPU core id to be used. Defaulted to system's $CUDA_VISIBLE_DEVICES value. If not set, all GPU cores will be utilized.

    # The new trained model will be stored at $CAMHD_SCENETAG_DATA_DIR/trained_classification_models.
    # Corresponding model_config will be updated in the classifier_meta_file (scene_tag_classifiers_meta.json).
    # The model version will be inferred by taking the next model version from the current 'latest_model' version.

    # A bash wildcard referring to the optical flow files for which the regions files need to be generated.
    "input_optical_flow_files": "$CAMHD_MOTION_METADATA_DIR/RS03ASHS/PN03B/06-CAMHDA301/2019/01/0[456789] $CAMHD_MOTION_METADATA_DIR/RS03ASHS/PN03B/06-CAMHDA301/2019/01/1[123456789] $CAMHD_MOTION_METADATA_DIR/RS03ASHS/PN03B/06-CAMHDA301/2019/01/2[123456789] $CAMHD_MOTION_METADATA_DIR/RS03ASHS/PN03B/06-CAMHDA301/2019/01/3[01]",

    # Optional. If 'monthly' key is provided, the 'input_optical_flow_files' will be automatically inferred
    # with respect to the $CAMHD_MOTION_METADATA_DIR. The above example contains inferred value from 'monthly': '2019-01'.
    "monthly": "2019-01",

    # The output path for the validation report of the regions files.
    "validation_report_path": "$CAMHD_MOTION_METADATA_DIR/regions_files_validation_reports/201901.txt",

    # The output path for the proofsheets required for manual verification of the regions files.
    "proofsheet_path": "$CAMHD_SCENETAG_DATA_DIR/proofsheets/201901/raw.html"
}

# The sample Region Files Process Config is available at:
    $CAMHD_MOTION_METADATA_DIR/pycamhd-motion-metadata/examples/sample_region_files_process_config.json

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
    parser.add_argument("--start-step",
                        type=int,
                        default=1,
                        help="Specify the step number from which the execution should start. Default: 1.")
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


def bernoulli_trial(prob):
    """
    Conducts Bernoulli trial and returns True or False based on the given probability.

    """
    r = random.uniform(0, 1)
    if r <= prob:
        return True

    return False


def _run(cmd_list, logfile, py_script=False, restrict_gpu=None, no_write=False, allow_error=False):
    """
    Executes a command through python subprocess and logs the STDOUT and STDERR to the logfile provided.

    """
    cmd = []
    custom_env = os.environ.copy()
    if restrict_gpu:
        logging.info("Setting CUDA_VISIBLE_DEVICES=%s" % str(restrict_gpu))
        custom_env["CUDA_VISIBLE_DEVICES"] = str(restrict_gpu)

    if py_script:
        cmd.append(sys.executable)

    cmd.extend(cmd_list)
    cmd_str = " ".join(cmd)

    with open(logfile, "a") as outfile:
        if not no_write:
            logging.info("Executing command: %s" % cmd_str)
            error_code = subprocess.call(cmd, stdout=outfile, stderr=outfile, env=custom_env)
            if error_code != 0 and not allow_error:
                raise RuntimeError("The cmd failed at runtime with error_code %s: %s" % (error_code, cmd_str))

            return error_code
        else:
            logging.info("Executing command (no-write): %s" % cmd_str)


def merge_dataset_dirs(base_train_data_dir, new_reg_train_data_dir, output_dir, base_train_data_prob=1):
    """
    Merges the scene_tag classification train data sets.

    """
    label_counts = defaultdict(int)
    os.makedirs(output_dir)

    labels = os.listdir(base_train_data_dir)
    for label in labels:
        os.makedirs(os.path.join(output_dir, label))

    for i, dataset_dir in enumerate([base_train_data_dir, new_reg_train_data_dir]):
        for label in labels:
            for f in os.listdir(os.path.join(dataset_dir, label)):
                # The i == 0 condition ensures that sampling probability is applied only to base_train_data_dir.
                if i == 0 and not bernoulli_trial(base_train_data_prob):
                    continue

                label_counts[label] += 1
                shutil.copy(os.path.join(dataset_dir, label, f), os.path.join(output_dir, label, f))

    logging.info("The base_train_data_dir %s and new_reg_train_data_dir %s have been merged to output_dir: %s"
                 % (base_train_data_dir, new_reg_train_data_dir, output_dir))
    logging.info("The data distribution in combined dataset: %s" % label_counts)


def process_config(config, args):
    """
    Processes an automated series of tasks to process raw optical flow files to regions files
    with scene_tag classification by reading parameters from the config file provided.

    """
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
    cur_step_num = 1
    logging.info("STEP %s: Sample data from new validated region files." % cur_step_num)
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
        "--width",
        "256",
        "--height",
        "256"
    ]
    no_write = args.no_write or (cur_step_num < args.start_step)
    _run(cmd_list, args.logfile, py_script=True, no_write=no_write)

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    # 2. Merge data with base data.
    cur_step_num = 2
    logging.info("STEP %s: Merge the train datasets." % cur_step_num)
    base_train_data_dir = os.path.join(scene_tag_train_data_dir, config["base_train_data_dirname"])
    merged_train_data_dir = os.path.join(scene_tag_train_data_dir, config["merged_train_data_dirname"])
    base_train_data_prob = config["base_train_data_prob"]

    no_write = args.no_write or (cur_step_num < args.start_step)
    if not no_write:
        merge_dataset_dirs(base_train_data_dir,
                           new_reg_train_data_dir,
                           merged_train_data_dir,
                           base_train_data_prob=base_train_data_prob)
        logging.info("The base_train_data_dir %s and new_reg_train_data_dir %s are merged to output_dir: %s"
                     % (base_train_data_dir, new_reg_train_data_dir, merged_train_data_dir))
    else:
        logging.info("The base_train_data_dir %s and new_reg_train_data_dir %s would be merged to output_dir: %s"
                     % (base_train_data_dir, new_reg_train_data_dir, merged_train_data_dir))

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    # 3. Train the CNN on the new train data.
    cur_step_num = 3
    # TODO: Add Transfer learning support.
    logging.info("STEP %s: Train the CNN on the new train data." % cur_step_num)
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
        "--func",
        "train_cnn",
        "--data-dir",
        merged_train_data_dir,
        "--classes",
        "SCENE_TAGS",
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
    no_write = args.no_write or (cur_step_num < args.start_step)
    _run(cmd_list, args.logfile, py_script=True, restrict_gpu=config.get("restrict_gpu"), no_write=no_write)

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
    logging.info("The Model re-training has completed, and the new model is saved at %s. " % model_outfile)
    logging.warning("The classifier_meta_file is updated and can be pushed to Git Repository: %s."
                    % classifiers_meta_file)
    logging.warning("The new trained model can be shared by uploading to the Google Drive.")
    logging.warning("The train and validation split of the current train data can be deleted.")

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    # 4. Make region files for input_optical_flow_files.
    cur_step_num = 4
    logging.info("STEP %s: Make region files for input_optical_flow_files." % cur_step_num)
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
    no_write = args.no_write or (cur_step_num < args.start_step)
    _run(cmd_list, args.logfile, py_script=True, no_write=no_write)

    if long_regions_files:
        cmd_list = ["rm", long_regions_files]
        _run(cmd_list, args.logfile, py_script=False, no_write=no_write)

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    # 5. Create Validation Report.
    cur_step_num = 5
    logging.info("STEP %s: Create Validation Report." % cur_step_num)
    validation_report_path = os.path.expandvars(config["validation_report_path"])
    py_file = os.path.join(CAMHD_MOTION_METADATA_DIR,
                           "pycamhd-motion-metadata",
                           "scripts",
                           "utils",
                           "validate_regions_files.py")
    cmd_list = [
        py_file,
        input_optical_flow_files_wild_card,
        "--outfile",
        validation_report_path
    ]
    no_write = args.no_write or (cur_step_num < args.start_step)
    _run(cmd_list, args.logfile, py_script=True, no_write=no_write)
    logging.warning("The validation report has been created, and can be pushed to Git Repository: %s."
                    % validation_report_path)

    cur_time = time.time()
    logging.info("Time taken for the step (sec): %s" % (cur_time - prev_start_time))
    prev_start_time = cur_time

    # 6. Create Proofsheet.
    cur_step_num = 6
    logging.info("STEP %s: Create Proofsheet." % cur_step_num)
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
    no_write = args.no_write or (cur_step_num < args.start_step)
    _run(cmd_list, args.logfile, py_script=True, no_write=no_write)

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

