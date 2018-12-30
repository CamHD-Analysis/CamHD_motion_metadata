#!/usr/bin/env python3

"""
Postprocess the regions files to modify the scene_tag based on prior sequencing order.
This script can be run after the make_regions_proof_sheet.py script. to load the images from
the images dir created by the make_regions_proof_sheet.py script.

# TODO: Extend the script to work independently to download the images.

Usage: (Running from the root directory of the repository.)
python scripts/utils/postprocess_regions_files.py ../RS03ASHS/PN03B/06-CAMHDA301/2018/08/0[456789]
    --image-path ../classification/proofsheets/20180804_20180809/images/

"""

import pycamhd.lazycache as camhd
import pycamhd.motionmetadata as mmd

from skimage.filters import threshold_yen
from skimage.io import imread
from skimage.morphology import erosion, square

import argparse
import glob
import logging
import os


# Threshold represents proportion of positive pixels after "yen" threshold (skimage) and erosion on grayscale image
# for the scene (lower bound).
FOREGROUND_PROPORTION_THRESHOLDS = {
    "d5A_p4_z1": 0.0135
}

# TODO: Hard threshold: If more than 8 mid_scenes, then scene correction is skipped.
MAX_MID_SCENES = 8


def get_args():
    parser = argparse.ArgumentParser(description="Postprocess the regions files to modify the scene_tag based "
                                                 "on prior sequencing order.")
    parser.add_argument('input',
                        metavar='N',
                        nargs='*',
                        help='Files or paths to process.')
    parser.add_argument('--deployment',
                        default="d5A",
                        help="The deployment prefix. Defaults to scene: d5A.")
    parser.add_argument('--image-path',
                        dest='img_path',
                        required=True,
                        help="The path to the folder containing the images. "
                             "Provide path to the 'images' folder in the output folder of make_regions_proof_sheet.py.")
    parser.add_argument('--image-size',
                        dest='img_size',
                        nargs='?',
                        default='320x240',
                        help="The size of the thumbnail image to refer. Default: 320x240.")
    parser.add_argument('--image-ext',
                        dest='img_ext',
                        default='jpg',
                        help="The image file extension. Default: jpg.")
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

    args = parser.parse_args()

    # Set up the Lazycache connection.
    args.qt = camhd.lazycache(args.lazycache)

    # Parse the img_size argument.
    toks = args.img_size.split("x")
    args.img_size = (int(toks[0]), int(toks[1]))

    return args


def _correct_sequencing_region_zoom_p4(regions_file, img_path, img_ext, deployment):
    """
    Note that this catches only the first occurrence of the initial and the final scene_tags.

    """
    region = "p4"
    scene = "%s_%s" % (deployment, region)
    inferred_by = "p4SequenceCheck"

    def _get_foreground_proportion(sample_frame_img_path):
        """
        Applies OTSU threshold on the image followed by an erosion, then takes the proportion of positive pixels.

        """
        img = imread(sample_frame_img_path, as_grey=True)
        thresh = threshold_yen(img)
        img_binary = img > thresh
        eroded_img = erosion(img_binary, square(3))
        return eroded_img.sum() / eroded_img.size


    url = regions_file.mov
    ZOOM_ORDER = ["z0", "z1", "z2", "z0"]
    initial_scene_tag = "%s_%s" % (scene, ZOOM_ORDER[0])
    end_scene_tag = "%s_%s" % (scene, ZOOM_ORDER[-1])

    initial_scene_index = None
    end_scene_index = None
    logging.debug(initial_scene_tag, end_scene_tag)
    for i, region in enumerate(regions_file.static_regions()):
        logging.debug(region.scene_tag)
        if initial_scene_index is None and region.scene_tag == initial_scene_tag:
            initial_scene_index = i
        elif end_scene_index is None and region.scene_tag == end_scene_tag:
            end_scene_index = i

    if initial_scene_index is None or end_scene_index is None:
        logging.warning("The initial or the end scene_tag is not found. Skipping the file: %s"
                        % (regions_file.basename))
        return

    # TODO: Assuming only two mid scenes exist which are z1 and z2.
    z1_scene_tag = "%s_%s" % (scene, "z1")
    z2_scene_tag = "%s_%s" % (scene, "z2")

    z1_found = False
    z2_found = False
    mid_scene_indices = range(initial_scene_index + 1, end_scene_index)

    if len(mid_scene_indices) >= MAX_MID_SCENES:
        logging.warning("Skipping the regions file as there are more than %s mid scenes: %s" % (MAX_MID_SCENES, url))
        return

    for i in mid_scene_indices:
        region = regions_file.static_at(i)
        sample_frame = region.start_frame + 0.5 * (region.end_frame - region.start_frame)
        sample_frame_path_thumbnail = os.path.join(img_path, "%s_%d_thumbnail.%s"
                                                   % (os.path.splitext(os.path.basename(url))[0],
                                                      sample_frame,
                                                      img_ext))

        foreground_proportion = _get_foreground_proportion(sample_frame_path_thumbnail)
        logging.info("Foreground proportion of region (%s, %s) is: %s (thumbnail path: %s)"
                     % (region.start_frame, region.end_frame, foreground_proportion, sample_frame_path_thumbnail))
        is_z1 = foreground_proportion > FOREGROUND_PROPORTION_THRESHOLDS[z1_scene_tag]

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

    # Logging warnings.
    if not z1_found and not z2_found:
        logging.warning("p4_z1 and p4_z2 were not found.")
    if not z1_found:
        logging.warning("p4_z1 was not found.")
    if not z2_found:
        logging.warning("p4_z2 was not found.")


def _correct_sequencing_region_zoom_p5_z0(regions_file, img_path, img_ext, deployment):
    """
    This corrected only the scenes followed by p5_z2 which are marked as p8_z0 to p5_z0.

    """
    inferred_by = "p5z0SequenceCheck"

    incorrect_scene = "p8_z0"
    incorrect_scene_tag = "%s_%s" % (deployment, incorrect_scene)

    correct_scene = "p5_z0"
    correct_scene_tag = "%s_%s" % (deployment, correct_scene)

    num_static_regions = len(regions_file.static_regions())

    # Case 1: Correction of of p8_z0 -> p5_z0 after processing the zooms of p5.
    context_scene = "p5_z2"
    context_scene_tag = "%s_%s" % (deployment, context_scene)

    prev_scene_tag = None
    i = 0
    while (prev_scene_tag != context_scene_tag and i < num_static_regions):
        prev_scene_tag = regions_file.static_at(i).scene_tag
        i += 1

    # p5_z2 may not have been found.
    if i >= num_static_regions:
        return

    # The static scene at i now refers to the static scene tag after the context_scene_tag.
    # TODO: Multiple consecutive incorrect scenes could also be corrected.
    region = regions_file.static_at(i)
    if region.scene_tag == incorrect_scene_tag:
        region.set_scene_tag(correct_scene_tag, inferred_by=inferred_by)
        logging.info("Setting region (%s-%s) to scene_tag: %s" % (region.start_frame,
                                                                  region.end_frame,
                                                                  correct_scene_tag))

    # Case 2: Correction of of p8_z0 -> p5_z0 before processing the zooms of p5.
    context_scene = "p5_z1"
    context_scene_tag = "%s_%s" % (deployment, context_scene)

    # Finding the first occurrence of context (p5_z1).
    for i in range(num_static_regions):
        if regions_file.static_at(i).scene_tag == context_scene_tag:
            break

    # The static scene at i - 1 now refers to the static scene tag before the context_scene_tag.
    region = regions_file.static_at(i - 1)
    if region.scene_tag == incorrect_scene_tag:
        region.set_scene_tag(correct_scene_tag, inferred_by=inferred_by)
        logging.info("Setting region (%s-%s) to scene_tag: %s" % (region.start_frame,
                                                                  region.end_frame,
                                                                  correct_scene_tag))


def _correct_sequencing_region_zoom_p0_z1(regions_file, img_path, img_ext, deployment):
    """
    This corrected only the scenes followed by (p6_z0 followed by p0_z0) which are marked as p6_z0 to p0_z1.

    """
    inferred_by = "p0z1SequenceCheck"

    incorrect_scene = "p6_z0"
    incorrect_scene_tag = "%s_%s" % (deployment, incorrect_scene)

    correct_scene = "p0_z1"
    correct_scene_tag = "%s_%s" % (deployment, correct_scene)

    context_scene_1 = "p6_z0"
    context_scene_1_tag = "%s_%s" % (deployment, context_scene_1)
    context_scene_2 = "p0_z0"
    context_scene_2_tag = "%s_%s" % (deployment, context_scene_2)

    num_static_regions = len(regions_file.static_regions())

    prev_scene_tag = None
    for i in range(num_static_regions):
        cur_scene_tag = regions_file.static_at(i).scene_tag

        if prev_scene_tag != context_scene_1_tag:
            prev_scene_tag = cur_scene_tag
            continue

        if regions_file.static_at(i + 1).scene_tag == context_scene_2_tag:
            # Next region is context_2, and the region after that is the one that needs to be checked.
            i += 2
            break

    # Context may not have been found.
    if i >= num_static_regions:
        return

    # The static scene at i now refers to the static scene tag after the context has been found.
    # TODO: Multiple consecutive incorrect scenes could also be corrected.
    region = regions_file.static_at(i)
    if region.scene_tag == incorrect_scene_tag:
        region.set_scene_tag(correct_scene_tag, inferred_by=inferred_by)
        logging.info("Setting region (%s-%s) to scene_tag: %s" % (region.start_frame,
                                                                  region.end_frame,
                                                                  correct_scene_tag))


def _get_all_sample_frames(regions_file, img_path, qt, img_size=(320, 240), img_ext="jpg"):
    """
    Checks whether a sample frame exists for each static region. If not, it downloads and creates a thumbnail.

    """
    for region in regions_file.static_regions():
        url = regions_file.mov

        sample_frame = region.start_frame + 0.5 * (region.end_frame - region.start_frame)
        sample_frame_path_thumbnail = os.path.join(img_path, "%s_%d_thumbnail.%s"
                                                   % (os.path.splitext(os.path.basename(url))[0],
                                                      sample_frame,
                                                      img_ext))

        if not os.path.exists(sample_frame_path_thumbnail):
            sample_frame_path = os.path.join(img_path, "%s_%d.%s"
                                             % (os.path.splitext(os.path.basename(url))[0], sample_frame, img_ext))
            logging.info("Fetching frame %d from %s for contact sheet" % (sample_frame, os.path.basename(url)))
            img = qt.get_frame(url, sample_frame, format=img_ext)
            img.save(sample_frame_path)
            img.thumbnail(img_size)  # PIL.thumbnail preserves aspect ratio
            img.save(sample_frame_path_thumbnail)


def postprocess(args):
    # TODO: The postprocessing algorithms need to be verified for each new deployment.
    if args.deployment != "d5A":
        logging.warning("The postprocessing algorithms have been checked for deployment d5A."
                        "It has not been verified for the current provided deployment: %s" % args.deployment)

    def _process(infile):
        logging.info("Postprocessing the regions file: {}".format(infile))
        regions_file = mmd.RegionFile.load(infile)
        logging.info("Getting all sample frames.")
        _get_all_sample_frames(regions_file, args.img_path, args.qt, args.img_size, args.img_ext)

        # TODO: Currently, supports only scene d5A_p4.
        # Postprocess1:
        logging.info("Postprocess1: Correcting scene_tags for d5A_p4 based on prior ordering of z1 and z2.")
        _correct_sequencing_region_zoom_p4(regions_file, args.img_path, args.img_ext, args.deployment)

        # Postprocess2:
        # logging.info("Postprocess2: Correcting scene_tags for p8_z0 to p5_z0 for scenes followed by p5_z2.")
        # _correct_sequencing_region_zoom_p5_z0(regions_file, args.img_path, args.img_ext, args.deployment)

        # Postprocess3:
        # logging.info("Postprocess3: Correcting scene_tags for p6_z0 to p0_z1 for scenes having p6_z0 followed by p0_z0.")
        # _correct_sequencing_region_zoom_p0_z1(regions_file, args.img_path, args.img_ext, args.deployment)

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
    postprocess(args)
