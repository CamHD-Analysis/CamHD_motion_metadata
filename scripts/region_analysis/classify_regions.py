

import logging
import random

import numpy as np

from operator import attrgetter

def classify_regions( regionsj, classifier, lazycache, first_n = None,
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
        ref_img = classifier.preprocess_image(ref_img)

        ## Parallelize in dask
        results = classifier.classify( ref_img, test_count = test_count )

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
