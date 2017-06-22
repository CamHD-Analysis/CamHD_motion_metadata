

import logging
import random

import numpy as np

from operator import attrgetter

def classify_regions( regionsj, classifier, lazycache, first_n = None,
                        ref_samples = (0.4,0.5,0.6), test_count = 5 ):

    mov = regionsj["movie"]["URL"]
    regions = regionsj["regions"]

    if first_n:
        regions = regions[:first_n]

    for rjson in regions:
        logging.info(rjson["type"] )
        if rjson["type"] != "static":
            continue

        # Identify sample image within region
        votes = {}
        all_results = []

        logging.info("Attempting to classify region from %d to %d" %(rjson["startFrame"], rjson["endFrame"]) )


        for sample_pct in ref_samples:
            sample = round( rjson["startFrame"] + sample_pct * (rjson["endFrame"]-rjson["startFrame"]))
            logging.info("Using test frame %d" % sample)

            ref_img = lazycache.get_frame( mov, sample )
            ref_img = classifier.preprocess_image(ref_img)

            results = classifier.classify( ref_img, test_count = test_count )

            results = sorted( results, key=attrgetter('score') )

            for r in results:
                logging.info("%s : %f" % (r.tag, r.score))

            all_results += results

            ## Heuristic tests?
            test_ratio = 2

            scene_tag = 'unknown'

            first = results[-1]
            second = results[-2]

            ## Use simple ratio test
            ratio = first.score / second.score
            logging.info("1st/2nd best scores: %f, %f    : ratio = %f" % (first.score, second.score, ratio))
            if ratio > test_ratio:
                scene_tag = first.tag

            ## Combine results with a simple voting scheme
            votes[ scene_tag ] = votes[scene_tag]+1 if scene_tag in votes.keys() else 1


        # This is terrible code, I'm sure there's a more Python-idiomatic way to do it
        # Check votes
        scene_tag = "unkown"

        votes_max = max( votes.values() )
        if votes_max > 1:
            for t in votes.keys():
                if votes[t] == votes_max:
                    scene_tag = t

        all_results = sorted( all_results, key=attrgetter('score') )
        first = all_results[-1]

        ## Find the guesses:
        ## Keep top 10%
        scene_tag_guesses = {}
        threshold = first.score * 0.9
        for r in all_results:
            if r.score > threshold:
                if r.tag in scene_tag_guesses.keys():
                    scene_tag_guesses[r.tag].append(r.score)
                else:
                    scene_tag_guesses[r.tag] = [r.score]

        rjson['sceneTag'] = [scene_tag]
        rjson['sceneTagScore'] = scene_tag_guesses

    return regionsj
