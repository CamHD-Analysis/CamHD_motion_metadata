#!/usr/bin/env python3

"""
Prints a summary of validation report for the given regions files to the console.

Usage: (Running from the root directory of the repository.)
python scripts/utils/validate_regions_files.py ../RS03ASHS/PN03B/06-CAMHDA301/2018/07/2[56789] --outfile <outfile path>

"""

from collections import defaultdict

import argparse
import glob
import logging
import os
import shutil

import pycamhd.lazycache as camhd
import pycamhd.motionmetadata as mmd

OPTIMAL_NUM_REGIONS = 39
NUM_REGIONS_LOWER_THRESH = 30
NUM_REGIONS_UPPER_THRESH = 50

IMAGE_RESOLUTION = (426, 240)

def get_args():
    parser = argparse.ArgumentParser(description="Prints a summary of validation report for the given regions files to the console.")
    parser.add_argument('input',
                        metavar='N',
                        nargs='*',
                        help='Files or paths to process.')
    parser.add_argument('--outfile',
                        help='The output file path. If not provided, output will be printed to the console.')
    parser.add_argument('--scene-val',
                        action='store_true',
                        help='Set this flag if sceneTag classification validation directory needs to be created.')
    parser.add_argument('--scene-val-dir',
                        help='The output directory to which the classified regions need to be written.')
    parser.add_argument('--frame-cache-dir',
                        help='Path to the directory where the frames (at 0.5) for the regions have been stored.')
    parser.add_argument("--image-format",
                        dest="imageext",
                        default='jpg',
                        help='The image file extension of the images in the frame-cache-dir.')
    parser.add_argument('--lazycache-url',
                        dest='lazycache',
                        default=os.environ.get("LAZYCACHE_URL", None),
                        help='URL to Lazycache repo server. Default: Environment variable LAZYCACHE_URL.')
    parser.add_argument("--log",
                        default="INFO",
                        help="Specify the log level. Default: WARN.")

    args = parser.parse_args()
    args.qt = camhd.lazycache(args.lazycache)
    if args.scene_val:
        if not args.scene_val_dir:
            raise ValueError("If scene-val flag is set, the scene-val-dir argument needs to be provided.")
        if not args.frame_cache_dir:
            raise ValueError("If scene-val flag is set, the frame-cache-dir argument needs to be provided.")
        if os.path.exists(args.scene_val_dir):
            raise ValueError("The scene-val-dir already exists.")

    return args


def validate_regions_files(args):
    def print_or_write(out_fp, output_string):
        if out_fp:
            out_fp.write(output_string)
        else:
            print(output_string)


    out_fp = None
    if args.outfile:
        out_fp = open(args.outfile, "w")
        print_or_write(out_fp, "Optimal Num Regions in a video: %s\n" % OPTIMAL_NUM_REGIONS)

    if args.scene_val:
        scene_to_img_file_dict = defaultdict(list)
        os.makedirs(args.scene_val_dir)
        os.makedirs(args.frame_cache_dir, exist_ok=True)

    num_optical_flow_files = 0
    num_regions_files = 0
    not_found_list = []
    less_regions_dict = {}
    more_regions_dict = {}

    def _process(infile):
        nonlocal num_optical_flow_files
        nonlocal num_regions_files
        # Check if it is from T000000 and ignore those files:
        if "T000000" in os.path.basename(infile):
            logging.info("Ignoring the T000000 regions file: %s" % infile)
            return

        num_optical_flow_files += 1
        logging.debug("Checking for optical flow file: {}".format(infile))
        regions_file_path = "%s_regions%s" % os.path.splitext(infile)
        if not os.path.exists(regions_file_path):
            not_found_list.append(regions_file_path)
            print_or_write(out_fp, "Num Regions for %s: N/A\n" % regions_file_path)
            return

        num_regions_files += 1
        regions = mmd.RegionFile.load(regions_file_path)
        num_static_regions = len(regions.static_regions())
        print_or_write(out_fp, "Num Regions for %s: %d\n" % (regions_file_path, num_static_regions))

        if num_static_regions <= NUM_REGIONS_LOWER_THRESH:
            less_regions_dict[regions_file_path] = num_static_regions
        elif num_static_regions >= NUM_REGIONS_UPPER_THRESH:
            more_regions_dict[regions_file_path] = num_static_regions

        if not args.scene_val:
            return

        # Updating scene_to_img_file_dict for creating scene_val_dir.
        url = regions.mov
        for region in regions.static_regions():
            sample_frame = region.start_frame + 0.5 * (region.end_frame - region.start_frame)
            img_file_name = "%s_%d.%s" % (os.path.splitext(os.path.basename(url))[0], sample_frame, args.imageext)
            img_file_path = os.path.join(args.frame_cache_dir, img_file_name)
            if not os.path.exists(img_file_path):
                img = args.qt.get_frame(url, sample_frame, format=args.imageext,
                                        width=IMAGE_RESOLUTION[0], height=IMAGE_RESOLUTION[1])
                img.save(img_file_path)

            scene_to_img_file_dict[region.scene_tag].append(img_file_path)


    for pathin in args.input:
        for infile in glob.iglob(pathin):
            if os.path.isdir(infile):
                infiles_path = os.path.join(infile, "*_optical_flow.json")
                for f in glob.iglob(infiles_path):
                    _process(f)
            else:
                _process(infile)

    # Format the Summary.
    summary_str = []
    summary_str.append("\n\n### SUMMARY ###")
    summary_str.append("\nNumber of Optical Flow Files found (ignoring T000000 files): %d" % num_optical_flow_files)
    summary_str.append("\nNumber of Regions Files found: %d" % num_regions_files)
    summary_str.append("\n\nNo Regions File found (but Optical Flow file exists) for: %d\n" % len(not_found_list))
    summary_str.append("\n".join(not_found_list))
    summary_str.append("\n\nLess than %s static regions found in a Regions File: %d\n"
                       % (NUM_REGIONS_LOWER_THRESH, len(less_regions_dict)))
    summary_str.append("\n".join(["%s: %d" % x for x in less_regions_dict.items()]))
    summary_str.append("\n\nMore than %s static regions found in a Regions File: %d\n"
                       % (NUM_REGIONS_UPPER_THRESH, len(more_regions_dict)))
    summary_str.append("\n".join(["%s: %d" % x for x in more_regions_dict.items()]))

    print_or_write(out_fp, "".join(summary_str))

    if out_fp:
        out_fp.close()

    if args.scene_val:
        for scene_tag, img_file_list in scene_to_img_file_dict.items():
            cur_scene_dir = os.path.join(args.scene_val_dir, scene_tag)
            os.makedirs(cur_scene_dir)
            for img_file in img_file_list:
                shutil.copy(img_file, os.path.join(cur_scene_dir, os.path.basename(img_file)))

        logging.info("The scene-val-dir has been created: %s" % args.scene_val_dir)

    return not_found_list, less_regions_dict, more_regions_dict


if __name__ == "__main__":
    args = get_args()
    logging.basicConfig(level=args.log.upper())
    validate_regions_files(args)
