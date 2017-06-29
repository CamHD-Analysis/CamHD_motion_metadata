

import os
import os.path as path
import glob
import random

import imreg_dft as ird

import logging

import re
import json

import pycamhd.lazycache as camhd

from .classifier import *

root_name_pattern = re.compile("CAMHDA301-[0-9T]*Z")
img_pattern = re.compile("(d\d*_p\d*_z\d*)/(CAMHDA301-[0-9T]*Z)_(\d*)\.")


class GroundTruthLibrary:

    def __init__(self, lazycache=camhd.lazycache()):
        self.img_cache = {}
        self.imgs = {}

        self.gt_urls = {}
        self.gt_regions = {}
        self.gt_library = {}
        self.lazycache = lazycache

    def load_ground_truth( self, ground_truth_file, img_path="classification/images/"):
        with open(ground_truth_file) as f:
            gt_json = json.load( f )

        all_gt_images = glob.iglob( "%s/**/*.png" % img_path )

        for gt_file in gt_json:
            gt_root = root_name_pattern.search(gt_file)

            if not gt_root:
                continue
            gt_root = gt_root.group(0)

            gt_images = {}

            # Load gt_images with all of the identified regions in the files
            gt = RegionFile( gt_file )

            self.gt_regions[gt_file] = gt.regions
            self.gt_urls[gt_file]    = gt.url

            for r in gt.static_regions:
                if 'sceneTag' not in r:
                    raise Exception( "Ground truth file \"%s\" contains static region without scene tag" % gt_file )

                if r['sceneTag'] == 'unknown':
                    raise Exception( "Unclassified static segment in ground truth file \"%s\"" % gt_file )

                gt_images[r['sceneTag']] = []


            logging.info("Checking GT file %s for root %s" % (gt_file, gt_root))

            for img_file in all_gt_images:
                img_match = img_pattern.search( img_file )
                if not img_match:
                    continue
                tag = img_match.group(1)
                img_root = img_match.group(2)
                frame = int(img_match.group(3))

                if img_root != gt_root:
                    continue

                gt_images[tag].append(path.abspath(img_file))

            self.gt_library[gt_file] = gt_images

        if len(self.gt_library) != len(gt_json):
            raise Exception("Error loading ground truth library")

    def aggregate_images(self, keys):
        imgs = {}
        for key in keys:
            logging.info("Using %s as ground truth" % key)
            for tag,gtimgs in self.gt_library[key].items():
                if tag not in imgs:
                    imgs[tag] = []

                imgs[tag].extend(gtimgs)

        return imgs


    def add_gt_image( self, gt, frame, tag ):
        url = self.gt_urls[gt]
        img = self.lazycache.get_frame( url, frame, format='png' )

        bname = path.splitext( path.basename( url ))[0]
        outfile = "classification/images/%s/%s_%08d.png" % (tag, bname, frame)
        logging.info("Saving new ground truth file to %s" % outfile)

        # if img.shape != (1080,1920,3):
        #      logging.warning("Something went wrong with getting the image (shape %s)" % str(img.shape) )
        #      continue

        os.makedirs(path.dirname(outfile), exist_ok=True)
        with open(outfile, 'wb') as f:
            img.save(f)

        self.gt_library[gt][tag].append(path.abspath(outfile))



    def supplement_gt_images(self, gts, tags):
        # Nothing for now

        for tag,count in tags.items():
            logging.info("I need to draw %d more %s" % (count, tag))

            tries = 0
            while count > 0 and tries < 10:
                tries += 1
                gt = random.sample(gts, 1)[0]

                if gt not in self.gt_regions:
                    raise Exception("Can't find the regions for ground truth file \"%s\"" % gt)

                ## Find relevant region(s) in the file
                matching_regions = []
                for r in self.gt_regions[gt]:
                    if r['type'] != 'static':
                        continue

                    if r['sceneTag'] == tag:
                        matching_regions.append( r )

                if len(matching_regions) == 0:
                    continue

                logging.info("In %s have %d regions of tag %s" % (gt, len(matching_regions), tag))

                use_region = random.sample(matching_regions, 1)[0]

                use_frame = use_region['startFrame'] + random.uniform(0.1,0.9) * (use_region['endFrame']-use_region['startFrame'])

                logging.info("Drawing from %d from %s regions from %d to %d" % (use_frame, gt, use_region['startFrame'], use_region['endFrame']))

                self.add_gt_image(gt, use_frame, tag)
                count -= 1

    def select(self, url):
        mov_root = root_name_pattern.search(url).group(0)

        # TODO. For now, just select a random ground truth in the library...
        use_gts = random.sample(self.gt_library.keys(), 1)

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
