

import os
import os.path as path
import glob
import random

import skimage.data as skd
import skimage.feature as skf
import skimage.transform as skt
import skimage.color
import skimage.io

import imreg_dft as ird

import logging

import re
import json

import numpy as np

from dask import compute, delayed
import dask.threaded

url_root = re.compile("CAMHDA301-[0-9T]*Z")
img_pattern = re.compile("(d\d*_p\d*_z\d*)/(CAMHDA301-[0-9T]*Z)_(\d*)\.")


class CompareResult:

    def __init__(self, tag, score ):
        self.tag = tag
        self.score = score



class Classifier:

    def __init__( self, images ):
        self.img_cache = {}
        self.imgs = images

    def tags( self ):
        return self.imgs.keys()

    def images( self ):
        return self.imgs


    def load( self, img_path ):
        if not path.exists(img_path):
            logging.fatal("Need %s to perform classification.  Run scripts/fetch_classification_images.py" % img_path)
            return

        for tag in os.listdir(img_path):
            if tag[0] == '.':
                continue

            if tag not in self.imgs:
                self.imgs[tag] = []

            for img in glob.iglob( "%s/%s/*.png" % (img_path,tag) ):
                self.imgs[tag].append( path.abspath(img) )

        logging.info("Loaded classifications tags: %s " % ', '.join( self.tags() ) )



    def image( self, name ):

        if name in self.img_cache.keys():
            return self.img_cache[name]

        ## Else eagerload
        test_img = skd.load( name )
        self.img_cache[name] = self.preprocess_image( test_img )

        return self.img_cache[name]

    def preprocess_image( self, img ):
        return skimage.color.rgb2gray(skt.rescale(img, 0.25, mode='constant' ))



    def classify( self, ref_img, test_count ):
        values = [delayed( self.compare_images )(ref_img, tag, count = test_count ) for tag in self.tags() ]
        results = compute( *values, get=dask.threaded.get )

        return results

    def sample_paths( self, tag, count ):
        ct = min( count, len( self.imgs[tag] ) )
        return [p for p in random.sample(self.imgs[tag], ct)]

    def sample_images( self, tag, count ):
        ct = min( count, len( self.imgs[tag] ) )
        return [self.image(p) for p in random.sample(self.imgs[tag], ct)]

    def compare_images( self, ref_img, tag, count ):
        ## Choose an arbitrary image for now
        #logging.info("Class %s has %d samples, sampling %d times" % (tag, len(self.imgs[tag]), count) )

        scores = []

        for test_img in self.sample_images( tag, count ):

            # Odds = 0 : don't consider image rotated by 180
            result = ird.translation(test_img, ref_img, odds=0)
            scores.append( float(result['success']) )


        ## Now manipulate samples
        scores = sorted(scores)

        ## Drop highest and lowest
        if len(scores) > 3:
            scores = scores[1:-1]

        return CompareResult( tag, np.mean(scores) )



class GroundTruthLibrary:

    def __init__( self ):
        self.img_cache = {}
        self.imgs = {}

        self.gt_library = {}

    def load_ground_truth( self, ground_truth_file, img_path = "classification/images/" ):
        with open( ground_truth_file ) as f:
            gt_json = json.load( f )

        all_gt_images = glob.iglob( "%s/**/*.png" % img_path )

        for gt_file in gt_json:
            gt_root = url_root.search(gt_file)

            if not gt_root:
                continue
            gt_root = gt_root.group(0)

            gt_images = {}

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

                if tag not in gt_images:
                    gt_images[tag] = []
                gt_images[tag].append( path.abspath(img_file) )


            self.gt_library[ gt_file ] = gt_images

        #print(self.gt_library)
    def aggregate_images( self, keys ):
        imgs = {}
        for key in keys:
            logging.info("Using %s as ground truth" % key)
            for tag,gtimgs in self.gt_library[key].items():
                if tag not in imgs:
                    imgs[tag] = []

                imgs[tag].extend(gtimgs)

        return imgs

    def supplement_gt_images( self, movs, tags ):
        ## Nothing for now
        for t in tags:
            logging.info("I need to draw more %s" % t)

    def select( self, url ):
        mov_root = url_root.search(url).group(0)

        ## For now, just select a random ground truth in the library...
        use_keys = random.sample( self.gt_library.keys(), 1 )

        imgs = self.aggregate_images( use_keys )

        MIN_IMAGES = 5
        short_tags = []
        for tag,gtimgs in imgs.items():
            logging.info("For tag \"%s\", have %d ground truth images" % (tag,len(gtimgs)) )
            if len(gtimgs) < MIN_IMAGES:
                short_tags.append(tag)

        ## If there aren't enough images, get some more
        if len(short_tags) > 0:
            self.supplement_gt_images( use_keys, short_tags )
            imgs = self.aggregate_images( use_keys )


        return Classifier( imgs )
