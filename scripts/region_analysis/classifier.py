

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

import numpy as np

from dask import compute, delayed
import dask.threaded


class CompareResult:

    def __init__(self, tag, score ):
        self.tag = tag
        self.score = score


class Classifier:

    def __init__( self ):
        self.img_cache = {}
        self.imgs = {}

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
