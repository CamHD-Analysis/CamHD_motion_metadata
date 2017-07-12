

import logging
import random
import json

import numpy as np

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



class RegionClassifier:

    def __init__(self, comparer, lazycache):
        self.comparer = comparer
        self.lazycache = lazycache
        self.images = {}

    def classify_regions(self, regions, first=None,
                         ref_samples=(0.4, 0.5, 0.6), test_count=3):

        count = 0

        num_to_process = len(regions.static_regions())

        if first:
            num_to_process = min(first, num_to_process)

        for i in range(num_to_process):

            r = regions.static_at(i)

            logging.info("Attempting to classify region from "
                         "%d to %d" % (r.start_frame, r.end_frame))

            ref_images = []

            for sample_pct in ref_samples:
                frame = r.frame_at(sample_pct)
                logging.info("Retrieving test frame %d" % frame)

                ref_img = self.lazycache.get_frame(regions.mov, frame)
                ref_img = self.comparer.preprocess_image(ref_img)
                #images.append(ref_img)
                ref_images.append(ref_img)

            self.images[i] = ref_images
            results = self.comparer.classify(ref_images, test_count=test_count)

            max_test_ratio = 1.2

            best_result = results[0]
            second_result = results[1]

            # Use simple ratio test
            ratio = second_result.rms / best_result.rms
            logging.info("1st/2nd best scores: %f, %f    : ratio = %f" % (best_result.rms, second_result.rms, ratio))
            if ratio > max_test_ratio:
                logging.info("Using label of \"%s\"" % best_result.tag)
                r.set_scene_tag(best_result.tag, inferred_by="matchToGroundTruth")
            else:
                logging.info("Unable to determine best fit")
                r.set_scene_tag("unknown")

            # Document lowest RMS errors in the JSON file
            scene_tag_guesses = {}
            threshold = best_result.rms * 1.5
            for res in results:
                if res.rms < threshold:
                    scene_tag_guesses[res.tag] = res.rms

            r.json['sceneTagMeta']['topTenPct'] = scene_tag_guesses

        regions = self.infer_from_neighbors(regions, num_to_process=num_to_process)

        regions = self.infer_from_sequence(regions, num_to_process=num_to_process)

        gt_file_revs = {}
        for gt_file in self.comparer.gt_files:
            gt_file_revs[gt_file] = git_revision(gt_file)

        regions.json['depends']['classifyRegions'] = {'groundTruth': gt_file_revs}

        return regions


    def infer_from_neighbors(self, regions, num_to_process=None):

        if not num_to_process:
            num_to_process = len(regions)

        # Second pass
        for i in range(num_to_process):

            region = regions.static_at(i)

            if not region.unknown:
                continue

            logging.info("Trying to re-evaluate region %d from %d to %d" %
                         (i, region.start_frame, region.end_frame))

            prevGood = prev_good(regions, i)
            nextGood = next_good(regions, i)

            # Try to infer from similarity
            rms_threshold = 0.2
            if prevGood is not None:

                # TODO: use ImageComparer instead
                prevResult = self.comparer.compare_images(self.images[prevGood][0], self.images[i][0])
                logging.info("Comparing to nextGood: %f" % prevResult.rms)

                if prevResult.rms < rms_threshold:
                    regions.static_at(i).json[i].set_scene_tag(regions.static_at(prevGood).scene_tag,
                                                            inferred_by="similarityToPrevNeighbor")
                    logging.info("Inferred tag %s by comparison to previous "
                                 "good match" %
                                 regions.static_at(prevGood).scene_tag)
                    continue
                else:
                    logging.info("Unknown region %d not a good match for "
                                 "previous %d rms = %f" %
                                 (i, prevGood, prevResult.rms))

            elif nextGood is not None:
                # TODO: use ImageComparer instead
                nextResult = self.comparer.compare_images(self.images[nextGood][0], self.images[i][0])
                logging.info("Comparing to nextGood: %f" % nextResult.rms)

                if nextResult.rms < rms_threshold:
                    regions.static_at(i).json[i].set_scene_tag( regions.static_at(nextGood).scene_tag,
                                                                inferred_by="similarityToNextNeighbor")
                    logging.info("Inferred tag %s by comparison to previous "
                                "good match" % regions.static_at(nextGood).scene_tag)
                    continue
                else:
                    logging.info("Unknown region %d not a good match for "
                                "previous %d, rms = %f" % (i, nextGood, nextResult.rms))


        return regions


    def infer_from_sequence(self, regions, num_to_process=None):

        if not num_to_process:
            num_to_process = len(regions)

        for i in range(num_to_process):

            region = regions.static_at(i)
            if not region.unknown:
                continue

            prevGood = prev_good(regions, i)
            nextGood = next_good(regions, i)

            # Try to infer from sequence
            # TODO Skip the corner cases for now
            if prevGood is not None and nextGood is not None:
                logging.info("Region %d is unknown and has good neighbors, trying to infer from sequence" % i)
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

                        logging.info("Inferred type %s by sequence" % regions.static_at(i).scene_tag)

                        region.set_scene_tag( REFERENCE_SEQUENCE[k+eta],
                                                    inferred_by="sequence")

                        break

            else:
                logging.info("For region %d, No classified regions before _and_ after, skipping inference from sequence" % i)

        return regions


def prev_good(regions, i):
    prevGood = None
    for j in reversed(range( 0, i )):
        if regions.static_regions()[j].scene_tag != 'unknown':
            prevGood = j
            break
    return prevGood

def next_good(regions, i):
    nextGood = None
    for j in range(i+1, len(regions.static_regions())):
        if regions.static_regions()[j].scene_tag != 'unknown':
            nextGood = j
            break
    return nextGood
