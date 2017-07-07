

import logging
import random
import json

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


def classify_regions(regions, classifier, lazycache, first=None,
                     ref_samples=(0.4, 0.5, 0.6), test_count=3):

    mov = regions.mov

    # scenes = []
    images = []
    region_idx = []

    count = 0

    num_to_process = len(regions.static_regions())

    if first:
        num_to_process = min(first, num_to_process)

    for i in range(num_to_process):

        r = regions.static_at(i)

#        region_idx.append(idx)

        # Identify sample image within region
        votes = {}
        all_results = []

        logging.info("Attempting to classify region from "
                     "%d to %d" % (r.start_frame, r.end_frame))

        for sample_pct in ref_samples:
            frame = r.frame_at(sample_pct)
            logging.info("Retrieving test frame %d" % frame)

            ref_img = lazycache.get_frame(mov, frame)
            ref_img = classifier.preprocess_image(ref_img)
            images.append(ref_img)

            results = classifier.classify(ref_img, test_count=test_count)

            results = sorted(results, key=attrgetter('rms'))

            for res in results:
                logging.info("%s : %f" % (res.tag, res.rms))

            all_results += results

            max_test_ratio = 0.85
            scene_tag = 'unknown'

            # Results are now RMS ... lower is better
            best_result = results[0]
            second_result = results[1]

            # Use simple ratio test
            ratio = best_result.rms / second_result.rms
            logging.info("1st/2nd best scores: %f, %f    : ratio = %f" % (best_result.rms, second_result.rms, ratio))
            if ratio < max_test_ratio:
                scene_tag = best_result.tag

            votes[ scene_tag ] = votes[scene_tag]+1 if scene_tag in votes.keys() else 1


        # This is terrible code, I'm sure there's a more Python-idiomatic
        # way to do it Check votes
        scene_tag = "unkown"
        scene_meta = {'inferredBy': ""}

        votes_max = max(votes.values())
        if votes_max > 1:
            for t in votes.keys():
                if votes[t] == votes_max:
                    logging.info("Good match to %s" % t)
                    inference = None if t == 'unknown' else 'matchToGroundTruth'
                    r.set_scene_tag(t, inferred_by=inference)


        all_results = sorted(all_results, key=attrgetter('rms'))
        best_result = all_results[0]

        # Keep lowest RMS errors
        scene_tag_guesses = {}
        threshold = best_result.rms * 2
        for res in all_results:
            if res.rms < threshold:
                if res.tag in scene_tag_guesses.keys():
                    scene_tag_guesses[res.tag].append(res.rms)
                else:
                    scene_tag_guesses[res.tag] = [res.rms]

        r.json['sceneTagMeta']['topTenPct'] = scene_tag_guesses

    for i in range(num_to_process):

        region = regions.static_at(i)

        if not region.unknown:
            continue

        logging.info("Trying to re-evaluate region %d from %d to %d" % (i, region.start_frame, region.end_frame))

        prevGood = None
        nextGood = None
        for j in reversed(range( 0, i )):
            if regions.static_regions()[j].scene_tag != 'unknown':
                prevGood = j
                break

        for j in range( i+1, len(regions.static_regions()) ):
            if regions.static_regions()[j].scene_tag != 'unknown':
                nextGood = j
                break

        #logging.info("Prev good at %d, next good at %d" % (prevGood, nextGood))

        # Try to infer from similarity
        threshold = 0.95
        if prevGood is not None:
            print(prevGood,i,len(images))
            # TODO: use ImageComparer instead
            prevResult = ird.translation(images[prevGood], images[i], odds=0)

            logging.info("Comparing to prevGood: %f" % prevResult['success'])
            if prevResult['success'] > threshold:
                regions.static_at(i).json[i].set_scene_tag( regions.static_at(prevGood).scene_tag,
                                                            inferred_by="similarityToPrevNeighbor")
                logging.info("Inferred tag %s by comparison to previous good match" % regions.static_at(prevGood).scene_tag)
                continue
            else:
                logging.info("Unknown region %d not a good match for previous %d: %f" % (i,prevGood,prevResult['success']))
        elif nextGood is not None:
            # TODO: use ImageComparer instead
            nextResult = ird.translation(images[nextGood], images[i], odds=0)
            logging.info("Comparing to nextGood: %f" % nextResult['success'])
            if nextResult['success'] > threshold:
                regions.static_at(i).json[i].set_scene_tag( regions.static_at(nextGood).scene_tag,
                                                            inferred_by="similarityToNextNeighbor")
                logging.info("Inferred tag %s by comparison to previous good match" % regions.static_at(nextGood).scene_tag)
                continue
            else:
                logging.info("Unknown region %d not a good match for previous %d: %f" % (i,nextGood,nextResult['success']))


        # Try to infer from sequence
        # TODO Skip the corner cases for now
        if prevGood is not None and nextGood is not None:
            logging.info("Trying to infer by sequence")
            delta = nextGood - prevGood
            eta = i - prevGood

            if delta > 3:
                continue

            for k in range( 0, len(REFERENCE_SEQUENCE)-delta):
                logging.info("%s == %s   ; %s == %s" %
                             (REFERENCE_SEQUENCE[k],
                              regions.static_at(prevGood).scene_tag,
                              REFERENCE_SEQUENCE[k+delta],
                              regions.static_at(nextGood).scene_tag, ))

                if REFERENCE_SEQUENCE[k] == regions.static_at(prevGood).scene_tag and \
                   REFERENCE_SEQUENCE[k+delta] == regions.static_at(nextGood).scene_tag:
                    ## Well, this sucks


                    regions.static_at(nextGood).set_scene_tag( REFERENCE_SEQUENCE[k+etc],
                                                inferred_by="sequence")

                    logging.info("Inferred type %s by sequence" % regions.static_at(i).scene_tag)
                    break

        else:
            logging.info("No classified regions before _and_ after, skipping inference from sequence")


    gt_file_revs = {}
    for gt_file in classifier.gt_files:
        gt_file_revs[gt_file] = git_revision(gt_file)

    regions.json['depends']['classifyRegions'] = {'groundTruth': gt_file_revs}

    return regions
