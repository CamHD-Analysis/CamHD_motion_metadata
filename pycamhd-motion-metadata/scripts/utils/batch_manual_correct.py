#!/usr/bin/env python3

"""
This is helper script to correct a batch of static_regions which have been misclassified in a specific pattern.

"""

import pycamhd.motionmetadata as mmd

import argparse
import os
import re


DATA_DIR = "/home/bhuvan/Projects/CamHD_motion_metadata/RS03ASHS/PN03B/06-CAMHDA301"
INFERRED_BY = "matchByHand"


def get_args():
    parser = argparse.ArgumentParser(description="Helper script to correct a batch of static_regions which have been "
                                                 "misclassified in a specific pattern.")
    parser.add_argument('--pred',
                        required=True,
                        help="The predicted scene_tag which has been misclassified.")
    parser.add_argument('--actual',
                        required=True,
                        help="The actual true scene_tag to which the scene_tag needs to be updated.")
    parser.add_argument('--year-month',
                        required=True,
                        help="The year and month being referred, for example: '201903'.")
    parser.add_argument('--deployment',
                        required=True,
                        help="The deployment version.")
    parser.add_argument('--wrong-regions',
                        required=True,
                        help="The path to the file containing the list of static regions which have been misclassified "
                             "in this specific pattern. Each line should contain a single region file in the format: "
                             "'startFrame -- endFrame (dd T HH | <scene_tag_without_deployment>)' "
                             "for example: '25419 -- 25829 (28 T 15 | p1_z0)'.")
    args = parser.parse_args()

    return args


def correct_regions(args):
    root_dir = os.path.join(DATA_DIR, args.year_month[:4], args.year_month[4:])

    with open(args.wrong_regions) as fp:
        for line in fp:
            line = line.strip()
            match = re.match(r'(\d+) -- (\d+) \((\d+) T (\d+) \| (p\d_z\d|unknown)\)', line)
            toks = match.groups()

            regions_file_path = os.path.join(
                root_dir,
                toks[2],
                "CAMHDA301-%s%sT%s1500_optical_flow_regions.json" % (args.year_month, toks[2], toks[3])
            )

            regions_file = mmd.RegionFile.load(regions_file_path)

            cur_scene_tag = "%s_%s" % (args.deployment, toks[4]) if toks[4] != "unknown" else "unknown"
            corrected_scene_tag = args.actual

            cur_region = None
            for r in regions_file.static_regions(scene_tag=cur_scene_tag):
                if r.start_frame == int(toks[0]) and r.end_frame == int(toks[1]):
                    cur_region = r
                    break

            cur_region.set_scene_tag(corrected_scene_tag, inferred_by=INFERRED_BY)

            regions_file.save_json(regions_file_path)
            print("Corrected scene tag regions file: %s" % regions_file_path)


if __name__ == "__main__":
    args = get_args()
    correct_regions(args)
