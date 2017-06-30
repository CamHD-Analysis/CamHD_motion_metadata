

import os
import os.path as path
import glob
import random

import imreg_dft as ird

import logging

import random

import re
import json

import pycamhd.lazycache as camhd

from .classifier import *
from .region_file import *


root_name_pattern = re.compile("CAMHDA301-[0-9T]*Z")
img_pattern = re.compile("(d\d*_p\d*_z\d*)/(CAMHDA301-[0-9T]*Z)_(\d*)\.")


class GTImage:

    def __init__(self, path):
        img_match = img_pattern.search(path)
        if not img_match:
            self.valid = False
            return

        self.path = path
        self.tag = img_match.group(1)
        self.basename = img_match.group(2)
        self.frame = int(img_match.group(3))
        self.valid = True

    @property
    def abspath(self):
        return path.abspath(self.path)


class GroundTruthLibrary:

    def __init__(self, lazycache=camhd.lazycache()):
        self.img_cache = {}
        self.imgs = {}

        self.regions = {}
        self.gt_library = {}
        self.lazycache = lazycache

    def load_ground_truth(self, ground_truth_file,
                          img_path="classification/images/"):

        with open(ground_truth_file) as f:
            gt_files = json.load(f)

        cached_images = glob.iglob("%s/**/*.png" % img_path)

        for gt_file in gt_files:

            # Load gt_images with all of the identified regions in the files
            regions = RegionFile.load(gt_file)

            # gt_root = root_name_pattern.search(gt_file)
            #
            # if not gt_root:
            #     continue
            # gt_root = gt_root.group(0)

            imgs = {}

            self.regions[regions.basename] = regions

            for r in regions.static_regions():
                if r.scene_tag is None:
                    raise Exception("Ground truth file \"%s\" contains static "
                                    "region without scene tag" % gt_file)

                if r.scene_tag is 'unknown':
                    raise Exception("Unclassified static segment in ground "
                                    "truth file \"%s\"" % gt_file)

                imgs[r.scene_tag] = []

            logging.info("Checking GT cache for image files "
                         "from %s" % (regions.basename))

            for img_path in cached_images:
                img = GTImage(img_path)

                if not img.valid or img.basename is not regions.basename:
                    continue

                imgs[img.tag].append(img.abspath)

            self.gt_library[regions.basename] = imgs

        if len(self.gt_library) != len(gt_files):
            raise Exception("Error loading ground truth library")

    def aggregate_images(self, keys):
        imgs = {}
        for key in keys:
            logging.info("Using %s as ground truth" % key)
            for tag, gtimgs in self.gt_library[key].items():
                if tag not in imgs:
                    imgs[tag] = []

                imgs[tag].extend(gtimgs)

        return imgs

    def download_new_gt_image(self, basename, frame, tag):
        mov = self.regions[basename].mov
        img = self.lazycache.get_frame(mov, frame, format='png')

        outfile = "classification/images/%s/%s_%08d.png" %\
                  (tag, basename, frame)
        logging.info("Saving new ground truth file to %s" % outfile)

        os.makedirs(path.dirname(outfile), exist_ok=True)
        with open(outfile, 'wb') as f:
            img.save(f)

        self.gt_library[basename][tag].append(GTImage(outfile))

    def supplement_gt_images(self, basenames, short_tags):

        for tag, count in short_tags.items():
            logging.info("I need to draw %d more %s" % (count, tag))

            tries = 0
            while count > 0 and tries < 10:
                tries += 1

                # Select the ground truth file to draw a new image from
                bn = random.sample(basenames, 1)[0]

                if bn not in self.regions:
                    raise Exception("Can't find the regions for "
                                    "ground truth file \"%s\"" % gt)

                # Find relevant region(s) in the file
                matching_regions = self.regions[bn].static_regions(scene_tag=tag)

                if len(matching_regions) == 0:
                    continue

                logging.info("%s has %d regions of tag %s" %\
                             (bn, len(matching_regions), tag))

                # Draw a region from the matching regions
                region = random.sample(matching_regions, 1)[0]

                frame = region.draw()

                logging.info("Retrieving frame %d from %s region %s which spans from %d to %d"
                             % (frame, bn, tag, region.start_frame, region.end_frame))

                self.download_new_gt_image(bn, frame, tag)
                count -= 1

    def select(self, regions):

        # TODO. For now, just select a random ground truth in the library...
        use_gts = random.sample(self.regions.keys(), 1)

        imgs = self.aggregate_images(use_gts)

        MIN_IMAGES = 5

        def collect_short_tags(imgs, min_images=MIN_IMAGES):
            short_tags = {}
            for tag, gtimgs in imgs.items():
                logging.info("  For tag \"%s\", have %d ground truth images" %
                             (tag, len(gtimgs)))

                deficit = MIN_IMAGES - len(gtimgs)
                if deficit > 0:
                    short_tags[tag] = deficit
            return short_tags

        short_tags = collect_short_tags(imgs)

        # If there aren't enough images, get some more
        if len(short_tags) > 0:
            self.supplement_gt_images(use_gts, short_tags)
            imgs = self.aggregate_images(use_gts)
            short_tags = collect_short_tags(imgs)

        if len(short_tags) > 0:
            raise Exception("Couldn't produce enough ground truth images")

        return Classifier(imgs, use_gts)
