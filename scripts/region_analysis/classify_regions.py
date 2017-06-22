

import logging
import skimage.data as skd
import skimage.feature as skf
import skimage.transform as skt
import skimage.color
import skimage.io
import imreg_dft as ird
import random

import numpy as np

from dask import compute, delayed
import dask.threaded

from operator import attrgetter

class CompareResult:

    def __init__(self, tag, score ):
        self.tag = tag
        self.score = score


def compare_images( ref_img, classification, tag, count ):
    ## Choose an arbitrary image for now
    logging.info("Class %s has %d samples, sampling %d times" % (tag, len(classification[tag]), count) )

    scores = []

    for test_img_path in random.sample( classification[tag], min( count, len(classification[tag]) ) ):
        test_img = skd.load( test_img_path )
        test_img = skimage.color.rgb2gray(skt.rescale(test_img, 0.25, mode='constant' ))

        skimage.io.imsave( "/tmp/region_analysis/%s.png" % tag, test_img )

        logging.info("Comparing to class %s test image %s" % (tag, test_img_path) )

        #shifts,error,phasediff = skf.register_translation( test_img, ref_img )
        # logging.info("Relative to class %s, RMS error = %f, shifts = %f,%f" % (c, error, shifts[0], shifts[1]))
        #
        # ## Heuristic test to invalidate large shifts
        # if abs(shifts[0]) > 30 or abs(shifts[1]) > 30:
        #     logging.info("Large shift, discarding")
        #     continue

        # Odds = 0 : never consider image rotated by 180
        result = ird.translation(test_img, ref_img, odds=0)

        scores.append( float(result['success']) )


    ## Now manipulate samples
    scores = sorted(scores)

    ## Drop highest and lowest
    if len(scores) > 3:
        scores = scores[1:-1]

    return CompareResult( tag, np.mean(scores) )


def classify_regions( regionsj, classification, lazycache, first_n = None,
                        ref_samples = [0.3,0.5,0.7], test_count = 5 ):

    mov = regionsj["movie"]["URL"]
    regions = regionsj["regions"]

    if first_n:
        regions = regions[:first_n]

    for rjson in regions:
        logging.info(rjson["type"] )
        if rjson["type"] != "static":
            continue

        # Identify sample image within region
        sample = round( (rjson["startFrame"] + rjson["endFrame"]) * 0.5 )

        logging.info("Attempting to classify region from %d to %d" %(rjson["startFrame"], rjson["endFrame"]) )
        logging.info("Using test frame %d" % sample)

        ref_img = lazycache.get_frame( mov, sample )
        ref_img = skimage.color.rgb2gray(skt.rescale(ref_img, 0.25, mode='constant' ))

        skimage.io.imsave( "/tmp/region_analysis/ref.png", ref_img )

        ## Parallelize in dask
        values = [delayed( compare_images )(ref_img, classification, tag, count = test_count ) for tag in classification.keys() ]
        results = compute( *values, get=dask.threaded.get )

        def sort_key( result ):
            return float()

        results = sorted( results, key=attrgetter('score') )

        for r in results:
            logging.info("%s : %f" % (r.tag, r.score))

        ## Heuristic tests?
        test_ratio = 2

        scene_tag = 'unknown'
        scene_tag_guesses = {}

        first = results[-1]
        second = results[-2]

        ## Keep top 10%
        threshold = first.score * 0.9
        for r in results:
            if r.score > threshold:
                scene_tag_guesses[ r.tag ] = r.score

        ## Use simple ratio test
        ratio = first.score / second.score
        logging.info("1st/2nd best scores: %f, %f    : ratio = %f" % (first.score, second.score, ratio))
        if ratio > test_ratio:
            scene_tag = first.tag

        rjson['sceneTag'] = [scene_tag]
        rjson['sceneTagScore'] = scene_tag_guesses

    return regionsj
