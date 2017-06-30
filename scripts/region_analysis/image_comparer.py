

import os
import os.path as path
import glob
import random

import skimage.data as skd
import skimage.feature as skf
import skimage.transform as skt
import skimage.color
import skimage.io

import logging

import re
import json

import numpy as np

from dask import compute, delayed
import dask.threaded
# import dask.multiprocessing


class CompareResult:

    def __init__(self, tag, error):
        self.tag = tag
        self.rms = error


class ImageComparer:

    def __init__(self, images, gt_files=[]):
        self.img_cache = {}
        self.imgs = images
        self.gt_files = gt_files

    def tags(self):
        return self.imgs.keys()

    def images(self):
        return self.imgs

    def image(self, name):

        if name in self.img_cache.keys():
            return self.img_cache[name]

        # Else eagerload
        test_img = skd.load(name)
        self.img_cache[name] = self.preprocess_image(test_img)

        return self.img_cache[name]

    def preprocess_image(self, img):
        return skimage.color.rgb2gray(skt.rescale(img, 0.25, mode='constant'))

    def classify(self, ref_img, test_count):
        values = [delayed(self.compare_images)(ref_img, tag, count=test_count) for tag in self.tags() ]
        results = compute(*values, get=dask.threaded.get)

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

        errors = []

        for test_img in self.sample_images( tag, count ):

            # Deprecated imreg_dft-based method
            # Odds = 0 : don't consider image rotated by 180
            #result = ird.translation(test_img, ref_img, odds=0)

            (shift,rms,phase) = skf.register_translation(test_img, ref_img)

            #print(shift,rms)

            # TODO:  Reimplement shift-based

            errors.append(rms)

        # Now aggregate samples
        errors = sorted(errors)

        # Drop highest and lowest
        if len(errors) > 3:
            errors = errors[1:-1]

        return CompareResult( tag, np.mean(errors) )
