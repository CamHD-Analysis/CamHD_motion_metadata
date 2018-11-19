#!/usr/bin/env python3

"""
Postprocess the regions files to modify the scene_tag based on prior sequencing order.
This script can be run after the make_regions_proof_sheet.py script. to load the images from
the images dir created by the make_regions_proof_sheet.py script.

# TODO: Extend the script to work independently to download the images.

Usage: (Running from the root directory of the repository.)
python scripts/utils/postprocess_regions_files.py ../RS03ASHS/PN03B/06-CAMHDA301/2018/08/0[456789] --img_path ../classification/proofsheets/20180804_20180809/images/

"""

import pycamhd.lazycache as camhd
import pycamhd.motionmetadata as mmd

from skimage.filters import threshold_minimum
from skimage.io import imread
from skimage.morphology import erosion, square

import argparse
import glob
import logging
import os


# TODO: Find the thresholds using some image processing method.
# Threshold represents proportion of positive pixels after otsu_threshold and erosion on grayscale image
# for the scene (lower bound).
scene_tag_thresholds = {
    "d5A_p4_z1": 0.009
}

def get_args():
    parser = argparse.ArgumentParser(description="Postprocess the regions files to modify the scene_tag based "
                                                 "on prior sequencing order.")
    parser.add_argument('input',
                        metavar='N',
                        nargs='*',
                        help='Files or paths to process.')
    parser.add_argument('--scene',
                        default="d5A_p4",
                        help="The scene for which the respective scene_tags (various zooms) need to be corrected."
                             " Defaults to scene: d5A_p4.")
    parser.add_argument('--img_path',
                        required=True,
                        help="The path containing the images. "
                             "Provide path to the images folder in the output folder of make_regions_proof_sheet.py.")
    parser.add_argument('--overwrite',
                        action="store_true",
                        help="Overwrite the existing regions_file to include the modifications based on "
                             "the sequence postprocessing.")
    parser.add_argument('--lazycache-url', dest='lazycache',
                        default=os.environ.get("LAZYCACHE_URL", None),
                        help='URL to Lazycache repo server (only needed if classifying)')
    parser.add_argument("--log",
                        default="INFO",
                        help="Specify the log level. Default: INFO.")
    return parser.parse_args()


def _correct_sequencing_region_zoom_d5A_p4(regions_file, img_path, qt):
    """
    Note that this catches only the first occurrence of the initial and the final scene_tags.

    """
    # TODO: Current supported scene is d5A_p4.
    scene = "d5A_p4"
    inferred_by = "p4SequenceCheck"

    def _get_foreground_proportion(img_path):
        """
        Applies OTSU threshold on the image followed by an erosion, then takes the proportion of positive pixels.

        """
        img = imread(img_path, as_gray=True)
        thresh = threshold_minimum(img)
        img_binary = img > thresh
        eroded_img = erosion(img_binary, square(3))
        return eroded_img.sum() / eroded_img.size


    url = regions_file.mov
    ZOOM_ORDER = ["z0", "z1", "z2", "z0"]
    initial_scene_tag = "%s_%s" % (scene, ZOOM_ORDER[0])
    end_scene_tag = "%s_%s" % (scene, ZOOM_ORDER[-1])

    initial_scene_index = None
    end_scene_index = None
    print (initial_scene_tag, end_scene_tag)
    for i, region in enumerate(regions_file.static_regions()):
        print (region.scene_tag)
        if initial_scene_index is None and region.scene_tag == initial_scene_tag:
            initial_scene_index = i
        elif end_scene_index is None and region.scene_tag == end_scene_tag:
            end_scene_index = i

    if initial_scene_index is None or end_scene_index is None:
        logging.info("The initial or the end scene_tag is not found. Skipping the file: %s" % (regions_file.basename))
        return


    # TODO: Assuming only two mid scenes exist which are z1 and z2.
    z1_scene_tag = "%s_%s" % (scene, "z1")
    z2_scene_tag = "%s_%s" % (scene, "z2")

    z1_found = False
    z2_found = False
    mid_scene_indices = range(initial_scene_index + 1, end_scene_index)

    # TODO: Hard threshold: If more than 8 mid_scenes, then return.
    if len(mid_scene_indices) >= 8:
        return

    for i in mid_scene_indices:
        region = regions_file.static_at(i)
        sample_frame = region.start_frame + 0.5 * (region.end_frame - region.start_frame)

        # TODO: The imageext hardcoded to jpg as it is the default in the make_regions_proof_sheet.py script.
        sample_frame_path_thumbnail = os.path.join(img_path, "%s_%d_thumbnail.%s"
                                                   % (os.path.splitext(os.path.basename(url))[0], sample_frame, "jpg"))
        if not os.path.exists(sample_frame_path_thumbnail):
            # TODO: img_size taken from the default of make_regions_proof_sheet.py script.
            img_size = (320, 240)
            sample_frame_path = os.path.join(img_path, "%s_%d.%s"
                                             % (os.path.splitext(os.path.basename(url))[0], sample_frame, "jpg"))
            logging.info("Fetching frame %d from %s for contact sheet" % (sample_frame, os.path.basename(url)))
            img = qt.get_frame(url, sample_frame, format="jpg")
            img.save(sample_frame_path)
            img.thumbnail(img_size)  # PIL.thumbnail preserves aspect ratio
            img.save(sample_frame_path_thumbnail)

        if z1_scene_tag not in scene_tag_thresholds:
            raise ValueError("The scene_tag %s is not supported by the scene_tag_thresholds threshold check."
                             % z1_scene_tag)

        foreground_proportion = _get_foreground_proportion(sample_frame_path_thumbnail)
        logging.info("Foreground proportion of region (%s, %s) is: %s (thumbnail path: %s)"
                     % (region.start_frame, region.end_frame, foreground_proportion, sample_frame_path_thumbnail))
        is_z1 = foreground_proportion > scene_tag_thresholds[z1_scene_tag]

        if is_z1:
            if z2_found:
                logging.warning("p4_z1 was found after finding p4_z2, but marking as p4_z2. It could be an anomaly.")
                if region.scene_tag != z2_scene_tag:
                    region.set_scene_tag(z2_scene_tag, inferred_by=inferred_by)
                    logging.info("Setting region (%s-%s) to scene_tag: %s" % (region.start_frame,
                                                                              region.end_frame,
                                                                              z2_scene_tag))
            else:
                if region.scene_tag != z1_scene_tag:
                    region.set_scene_tag(z1_scene_tag, inferred_by=inferred_by)
                    logging.info("Setting region (%s-%s) to scene_tag: %s" % (region.start_frame,
                                                                              region.end_frame,
                                                                              z1_scene_tag))
                z1_found = True
        else:
            if region.scene_tag != z2_scene_tag:
                region.set_scene_tag(z2_scene_tag, inferred_by=inferred_by)
                logging.info("Setting region (%s-%s) to scene_tag: %s" % (region.start_frame,
                                                                          region.end_frame,
                                                                          z2_scene_tag))
            z2_found = True

    # Logging.
    if not z1_found and not z2_found:
        logging.warning("p4_z1 and p4_z2 were not found.")

    if not z1_found:
        logging.warning("p4_z1 was not found.")
    if not z2_found:
        logging.warning("p4_z2 was not found.")


def postprocess_using_sequencing_prior(args):
    # TODO: Currently, supports only scene d5A_p4.
    if args.scene != "d5A_p4":
        raise NotImplementedError("Supported scene are: p4.")

    def _process(infile):
        logging.info("Postprocessing the regions file: {}".format(infile))
        regions_file = mmd.RegionFile.load(infile)
        _correct_sequencing_region_zoom_d5A_p4(regions_file, args.img_path, args.qt)

        if args.overwrite:
            logging.warning("Overwriting the regions_file: %s" % regions_file.mov)
            regions_file.save_json(infile)

    for pathin in args.input:
        for infile in glob.iglob(pathin):
            if os.path.isdir(infile):
                infile = os.path.join(infile, "*_regions.json")
                for f in glob.iglob(infile):
                    _process(f)
            else:
                _process(infile)



if __name__ == "__main__":
    args = get_args()
    logging.basicConfig(level=args.log.upper())
    args.qt = camhd.lazycache(args.lazycache)
    postprocess_using_sequencing_prior(args)
