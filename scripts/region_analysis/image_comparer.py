

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

from operator import attrgetter

from dask import compute, delayed
import dask.threaded
# import dask.multiprocessing


class CompareResult:

    def __init__(self, tag, error):
        self.tag = tag
        self.rms = error


class ImageComparer:

    def __init__(self, paths, gt_files=[]):
        self.img_cache = {}
        self.paths = paths
        self.gt_files = gt_files

    def tags(self):
        return self.paths.keys()

    def paths(self):
        return self.paths

    def image(self, name):

        if name in self.img_cache.keys():
            return self.img_cache[name]

        # Else eagerload
        logging.info("Eagerloading %s" % name)
        test_img = skd.load(name)
        self.img_cache[name] = self.preprocess_image(test_img)

        return self.img_cache[name]

    def preprocess_image(self, img):
        return skimage.color.rgb2gray(skt.rescale(img, 0.25, mode='constant'))

    def classify(self, test_images, test_count):

        jobs = []

        for test_img in test_images:
            for tag in self.tags():
                for ref_img in self.sample_images(tag,test_count):
                    jobs.append(delayed(self.compare_images)(ref_img,test_img,tag))

        logging.info("Performing %d comparisons" % len(jobs))

        res = compute(*jobs, get=dask.threaded.get)

        results = {}

        for r in res:
            #logging.info("%s : %f" % (r.tag, r.rms))

            if r.tag not in results:
                results[r.tag] = []

            results[r.tag].append(r.rms)

        for tag, vals in results.items():
            logging.info("%s: %s" % (tag, vals))

        all_results = []

        for tag, res in results.items():
            # sort the resulting errors
            r = sorted(res)

            # drop first and last
            r = r[1:-1]

            all_results.append(CompareResult(tag, np.mean(r)))

        return sorted(all_results, key=attrgetter('rms'))

    def sample_paths(self, tag, count):
        ct = min(count, len(self.paths[tag]))
        return random.sample(self.paths[tag], count)

    def sample_images(self, tag, count):
        return [self.image(p) for p in self.sample_paths(tag, count)]

    def compare_images(self, ref_img, test_img, tag=None):
        # Choose an arbitrary image for now
        # logging.info("Class %s has %d samples, sampling %d times" % (tag, len(self.imgs[tag]), count) )

        errors = []

        # Deprecated imreg_dft-based method
        # Odds = 0 : don't consider image rotated by 180
        # result = ird.translation(test_img, ref_img, odds=0)

        (shift, rms, phase) = skf.register_translation(ref_img, test_img)

        return CompareResult( tag, rms )
