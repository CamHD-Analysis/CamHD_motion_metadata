#!/usr/bin/env python3

import pycamhd.region_analysis as ra
import pycamhd.lazycache as camhd

from keras.models import load_model

import argparse
import glob
import json
import logging
import os
import subprocess


CLASSIFIERS_META_FILE = os.path.join("$CAMHD_MOTION_METADATA_DIR",
                                     "pycamhd-motion-metadata",
                                     "pycamhd",
                                     "region_analysis",
                                     "scene_tag_classifiers_meta.json")


def get_args():
    parser = argparse.ArgumentParser(description='Generate _optical_flow_region.json files from _optical_flow.json files')

    parser.add_argument('input', metavar='N', nargs='*',
                        help='Files or paths to process')

    parser.add_argument('--dry-run', dest='dryrun', action='store_true',
                        help='Dry run, don\'t actually process')

    parser.add_argument('--force', dest='force', action='store_true', help='Remake existing files (will not overwrite ground truth files)')

    parser.add_argument('--force-unclassified', dest='forceunclassified',
                        action='store_true',
                        help="Force rebuild of file only if it hasn't been classified")

    parser.add_argument('--no-classify', dest='noclassify', action='store_true',
                        help="Don't attempt to classify static regions")

    parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                        help='Logging level')

    parser.add_argument('--first', metavar='first', nargs='?', type=int,
                        help='')

    parser.add_argument("--ground-truth", dest="groundtruth",
                        default="classification/ground_truth.json")

    parser.add_argument("--use-cnn",
                        action="store_true",
                        help="Flag to use the trained CNN model for region classification. "
                             "If this flag is set, then the --ground-truth argument is ignored. "
                             "If this flag is not set, the 'matchByGroundTruth' algorithm will be used for "
                             "region classification.")

    parser.add_argument("--cnn-model-config",
                        default=None,
                        help="The path to the scene tag classifier CNN model config json file."
                             "Default: The config corresponding to the latest model in the"
                             "classifiers_meta_file (scene_tag_classifiers_meta.json).")

    parser.add_argument('--git-add', dest='gitadd', action='store_true',
                        help='Run "git add" on resulting file')

    parser.add_argument('--lazycache-url', dest='lazycache',
                        default=os.environ.get("LAZYCACHE_URL", None),
                        help='URL to Lazycache repo server (only needed if classifying)')

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = get_args()
    logging.basicConfig(level=args.log.upper())

    cnn_classifier = None
    gt_library = None
    qt = None
    if not args.noclassify:
        qt = camhd.lazycache(args.lazycache, verbose=True)

        if not args.use_cnn:
            gt_library = ra.GroundTruthLibrary(qt)
            gt_library.load_ground_truth(args.groundtruth)

    cnn_classifier = None
    if args.use_cnn:
        # This is needed because the paths to model files in the CLASSIFIERS_META_FILE (scene_tag_classifiers_meta.json)
        # refer to the trained model files relative to the path set in the CAMHD_SCENETAG_DATA_DIR environment variable.
        CAMHD_SCENETAG_DATA_DIR = os.environ.get("CAMHD_SCENETAG_DATA_DIR", None)
        if not CAMHD_SCENETAG_DATA_DIR:
            raise ValueError("The %s needs to be set in the environment while using CNN." % CAMHD_SCENETAG_DATA_DIR)
        if not os.path.exists(CAMHD_SCENETAG_DATA_DIR):
            raise ValueError("The $CAMHD_SCENETAG_DATA_DIR does not exist: %s" % CAMHD_SCENETAG_DATA_DIR)

        if not args.cnn_model_config:
            if not os.environ.get("CAMHD_MOTION_METADATA_DIR", None):
                raise ValueError("The CAMHD_MOTION_METADATA_DIR needs to be set in the environment "
                                 "when '--use-cnn' flag is set.")

            with open(os.path.expandvars(CLASSIFIERS_META_FILE)) as fp:
                classifiers_meta_dict = json.load(fp)

            latest_model = classifiers_meta_dict["latest_model"]
            args.cnn_model_config = classifiers_meta_dict["trained_models"][latest_model]

        cnn_classifier = load_model(os.path.expandvars(args.cnn_model_config["model_path"]))

    for inpath in args.input:
        if os.path.isdir(inpath):
            inpath += "**/*_optical_flow.json"

        logging.info("Checking %s" % inpath)
        for infile in sorted(glob.iglob(inpath, recursive=True)):
            outfile = os.path.splitext(infile)[0] + "_regions.json"

            if os.path.isfile(outfile):
                if gt_library and outfile in gt_library.files.values():
                    logging.info("%s is a ground truth file, skipping..." % outfile)
                    continue
                elif args.forceunclassified and not ra.is_classified(outfile):
                    logging.info("%s exists but isn't classified, overwriting" % outfile)
                elif args.force is True:
                    logging.info("%s exists, overwriting" % outfile)
                else:
                    logging.warning("%s exists, run with --force to overwrite" % outfile)
                    continue

            ra.RegionFileMaker(first=args.first,
                               dryrun=args.dryrun,
                               force=args.force,
                               noclassify=args.noclassify,
                               gt_library=gt_library,
                               lazycache=qt,
                               use_cnn=args.use_cnn,
                               cnn_classifier=cnn_classifier,
                               cnn_model_config=args.cnn_model_config).make_region_file(infile, outfile)

            if os.path.isfile(outfile) and args.gitadd:
                subprocess.run(["git", "add", outfile])
