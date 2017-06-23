

import logging
import random

import numpy as np
import imreg_dft as ird

from operator import attrgetter

from .git_utils import *

classify_regions_version = "1.1"

# Quick hack to have this hardcoded
REFERENCE_SEQUENCE = ["d2_p1_z0", "d2_p1_z1", "d2_p1_z0",
                      "d2_p0_z0", "d2_p2_z0", "d2_p2_z1", "d2_p2_z0",
                      "d2_p0_z0", "d2_p3_z0", "d2_p3_z1",
                      "d2_p3_z2", "d2_p3_z0", "d2_p0_z0",
                      "d2_p4_z0", "d2_p4_z1", "d2_p4_z2",
                      "d2_p4_z0", "d2_p0_z0", "d2_p5_z0",
                      "d2_p5_z1", "d2_p5_z2", "d2_p5_z0",
                      "d2_p0_z0", "d2_p6_z0", "d2_p6_z1",
                      "d2_p6_z2", "d2_p6_z0", "d2_p0_z0",
                      "d2_p0_z1", "d2_p0_z2", "d2_p0_z0",
                      "d2_p7_z0", "d2_p7_z1", "d2_p7_z0",
                      "d2_p0_z0", "d2_p8_z0", "d2_p8_z1",
                      "d2_p8_z0", "d2_p0_z0", "d2_p1_z0"]


def is_classified( file ):
    with open(file) as f:
        j = json.load(f)

    if "regions" not in j:
        return False

    for r in j["regions"]:
        if r['type'] != 'static':
            continue

        if 'sceneTag' not in r:
            return False


    return True

def classify_regions( regionsj, classifier, lazycache, first_n = None,
                        ref_samples = (0.4,0.5,0.6), test_count = 3 ):

    mov = regionsj["movie"]["URL"]
    regions = regionsj["regions"]

    ## These
    scenes = []
    images = []
    region_idx = []

    for idx in range(len(regions)):

        if first_n and len(scenes) >= first_n:
            break;

        rjson = regions[idx]
        if rjson["type"] != "static":
            continue

        region_idx.append(idx)

        # Identify sample image within region
        votes = {}
        all_results = []

        logging.info("Attempting to classify region from %d to %d" %(rjson["startFrame"], rjson["endFrame"]) )

        for sample_pct in ref_samples:
            sample = round( rjson["startFrame"] + sample_pct * (rjson["endFrame"]-rjson["startFrame"]))
            logging.info("Using test frame %d" % sample)

            ref_img = lazycache.get_frame( mov, sample )
            ref_img = classifier.preprocess_image(ref_img)
            images.append( ref_img )

            results = classifier.classify( ref_img, test_count = test_count )

            results = sorted( results, key=attrgetter('score') )

            for r in results:
                logging.info("%s : %f" % (r.tag, r.score))

            all_results += results

            # Heuristic tests?
            min_test_ratio = 2

            scene_tag = 'unknown'

            first = results[-1]
            second = results[-2]

            # Use simple ratio test
            ratio = first.score / second.score
            logging.info("1st/2nd best scores: %f, %f    : ratio = %f" % (first.score, second.score, ratio))
            if ratio > min_test_ratio:
                scene_tag = first.tag

            votes[ scene_tag ] = votes[scene_tag]+1 if scene_tag in votes.keys() else 1


        # This is terrible code, I'm sure there's a more Python-idiomatic
        # way to do it Check votes
        scene_tag = "unkown"
        scene_meta = { 'inferredBy': ""}

        votes_max = max(votes.values())
        if votes_max > 1:
            for t in votes.keys():
                if votes[t] == votes_max:
                    logging.info("Good match to %s" % t)
                    scene_tag = t
                    scenes.append(t)

                    if t != 'unknown':
                        scene_meta['inferredBy'] = "matchToGroundTruth"

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

        scene_meta['topTenPct'] = scene_tag_guesses

        rjson['sceneTag'] = scene_tag
        rjson['sceneTagMeta'] = scene_meta


    ## Now attempt to clean any unknowns
    logging.info(scenes)

    for i in range(len(scenes)):
        if scenes[i] != 'unknown':
            continue

        ri = region_idx[i]

        logging.info("Trying to re-evaluate region %d from %d to %d" % (i, regions[ri]['startFrame'], regions[ri]['endFrame']))

        prevGood = None
        nextGood = None
        for j in reversed(range( 0, i )):
            if scenes[j] != 'unknown':
                prevGood = j
                break

        for j in range( i+1, len(scenes) ):
            if scenes[j] != 'unknown':
                nextGood = j
                break

        #logging.info("Prev good at %d, next good at %d" % (prevGood, nextGood))

        # Try to infer from similarity
        threshold = 0.95
        if prevGood is not None:
            prevResult = ird.translation( images[prevGood], images[i], odds=0)

            logging.info("Comparing to prevGood: %f" % prevResult['success'])
            if prevResult['success'] > threshold:
                scenes[i] = scenes[prevGood]
                regions[ri]['sceneTag'] = scenes[prevGood]
                regions[ri]['sceneTagMeta']['inferredBy'] = "similarityToPrevNeighbor"
                logging.info("Inferred tag %s by comparison to previous good match" % scenes[i])
                continue
            else:
                logging.info("Unknown region %d not a good match for previous %d: %f" % (i,prevGood,prevResult['success']))
        elif nextGood is not None:
            nextResult = ird.translation( images[nextGood], images[i], odds=0)
            logging.info("Comparing to nextGood: %f" % nextResult['success'])
            if nextResult['success'] > threshold:
                scenes[i] = scenes[nextGood]
                regions[ri]['sceneTag'] = scenes[nextGood]
                regions[ri]['sceneTagMeta']['inferredBy'] = "similarityToNextNeighbor"
                logging.info("Inferred type %s by comparison to next good match" % scenes[i])
                continue
            else:
                logging.info("Unknown region %d not a good match for previous %d: %f" % (i,nextGood,nextResult['success']))


        # Try to infer from sequence
        # TODO Skip the corner cases for now
        if prevGood is not None and nextGood is not None:
            logging.info("Trying to infer by sequence")
            delta = nextGood - prevGood

            if delta > 3:
                continue

            for k in range( 0, len(REFERENCE_SEQUENCE)-delta ):
                logging.info("%s == %s   ; %s == %s" % (REFERENCE_SEQUENCE[k], scenes[prevGood],REFERENCE_SEQUENCE[k+delta],scenes[nextGood] ))

                if REFERENCE_SEQUENCE[k] == scenes[prevGood] and REFERENCE_SEQUENCE[k+delta] == scenes[nextGood]:
                    ## Well, this sucks
                    scenes[i] = REFERENCE_SEQUENCE[ k+(i-prevGood) ]
                    regions[ri]['sceneTag']= scenes[i]
                    regions[ri]['sceneTagMeta']['inferredBy'] = "sequence"
                    logging.info("Inferred type %s by sequence" % scenes[i])
                    break

        else:
            logging.info("No classified regions before _and_ after, skipping inference from sequence")


    gt_file_revs = {}
    for gt_file in classifier.gt_files:
        gt_file_revs[gt_file] = git_revision(gt_file)

    regionsj['depends']['classifyRegions'] = {'groundTruth': gt_file_revs}

    return regionsj
