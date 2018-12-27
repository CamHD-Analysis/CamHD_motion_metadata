
from keras.models import load_model
from scipy.stats import mode
from skimage.transform import resize

import logging
import random
import json
import os

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


# TODO: The probability thresholds could be taken from model_config.
CNN_PROBABILITY_THRESH = 0.90

DEFAULT_CLASSIFIER_CONFIG_RELATIVE_PATH = os.path.join("trained_classification_models",
                                                       "scene_classification_vgg16_8.json")
DEFAULT_CLASSIFIER_HDF5_RELATIVE_PATH   = os.path.join("trained_classification_models",
                                                       "scene_classification_vgg16_8.hdf5")

DEFAULT_CNN_MODEL_CONFIG_PATH = os.path.join(os.path.dirname(__file__), DEFAULT_CLASSIFIER_CONFIG_RELATIVE_PATH)
with open(DEFAULT_CNN_MODEL_CONFIG_PATH) as fp:
    DEFAULT_MODEL_CONFIG = json.load(fp)

DEFAULT_MODEL_CONFIG["model_path"] = os.path.join(os.path.dirname(__file__), DEFAULT_CLASSIFIER_HDF5_RELATIVE_PATH)
DEFAULT_CLASSIFIER = load_model(DEFAULT_MODEL_CONFIG["model_path"])


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

                ref_img = self.lazycache.get_frame(regions.mov, frame, format='np')
                ref_img = self.comparer.preprocess_image(ref_img)
                #images.append(ref_img)
                ref_images.append(ref_img)

            self.images[i] = ref_images
            results = self.comparer.classify(ref_images, test_count=test_count)

            max_test_ratio = 1.05

            if len(results) == 0:
                logging.info("No good results")
                r.set_scene_tag("unknown")
            elif len(results) == 1:
                logging.info("Only one good result")
                r.set_scene_tag(results[0].tag, inferred_by="matchToGroundTruth")
            else:
                best_result = results[0]
                second_result = results[1]

                if best_result == 0.0:
                    logging.info("Best result has score of 0")
                    r.set_scene_tag(best_result.tag, inferred_by="matchToGroundTruth")
                else:
                    # Use simple ratio test
                    ratio = second_result.rms / best_result.rms
                    logging.info("1st/2nd best labels: %s, %s" % (best_result.tag, second_result.tag))
                    logging.info("1st/2nd best scores: %f, %f    : ratio = %f" % (best_result.rms, second_result.rms, ratio))
                    if ratio > max_test_ratio:
                        logging.info("Using label \"%s\" for %d to %d" % (best_result.tag,r.start_frame,r.end_frame))
                        r.set_scene_tag(best_result.tag, inferred_by="matchToGroundTruth")
                    else:
                        logging.info("Unable to determine best fit")
                        r.set_scene_tag("unknown")

            # Document lowest RMS errors in the JSON file
            scene_tag_guesses = {}

            if len(results) > 0:
                threshold = results[0].rms * 1.5
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


    def classify_regions_cnn(self, regions, cnn_model_config_path=None, first=None, ref_samples=(0.4, 0.5, 0.6)):
        """
        Classify the regions of the given RegionFile and assign the scene_tags.

        :param regions: The RegionFile object created from the video regions_file.
        :param cnn_model_config_path: The path to the trained CNN model config file (JSON). Default: None, the default
                                      classifier files from the modules train_classification_models will be used.
        :param first: The number of regions to process. Default: None, which implies all static regions.
        :param ref_samples: The frames of the region as a pct of region length to be considered for classification.
        :return: The updated regions (RegionFile object) with the scene_tag predictions.

        """
        if cnn_model_config_path is None:
            logging.info("Using the default scene_tag classifier at: %s" % DEFAULT_CNN_MODEL_CONFIG_PATH)
            model_config = DEFAULT_MODEL_CONFIG
            classifier = DEFAULT_CLASSIFIER
        else:
            with open(cnn_model_config_path) as fp:
                model_config = json.load(fp)

            classifier = load_model(model_config["model_path"])

        num_to_process = len(regions.static_regions())

        if first:
            num_to_process = min(first, num_to_process)

        for i in range(num_to_process):

            r = regions.static_at(i)

            logging.info("Attempting to classify region from %d to %d" % (r.start_frame, r.end_frame))

            ref_images = []

            for sample_pct in ref_samples:
                frame = r.frame_at(sample_pct)
                logging.info("Retrieving test frame %d" % frame)

                ref_img = self.lazycache.get_frame(regions.mov, frame, format='np')
                resized_image = resize(ref_img, model_config["input_shape"]) * 255
                resized_image = resized_image.astype(np.uint8)
                if model_config["rescale"] is True:
                    resized_image = resized_image * (1.0 / 255)

                ref_images.append(resized_image)

            self.images[i] = ref_images
            input_tensor = np.asarray(ref_images)
            pred_probas = classifier.predict(input_tensor)
            pred_classes = np.argmax(pred_probas, axis=1)

            class_probas = []
            for i, pred_class in enumerate(pred_classes):
                class_probas.append(pred_probas[i][pred_class])

            # TODO: Change these to debug logs:
            logging.info("Unique pred_classes: %s" % len(set(pred_classes)))
            logging.info("pred_classes: %s, pred_probas: %s" % (str(pred_classes), str(class_probas)))

            majority_class = mode(pred_classes)[0][0]
            majority_class_avg_proba = 0
            for pred_class, class_proba in zip(pred_classes, class_probas):
                if pred_class == majority_class:
                    majority_class_avg_proba += class_proba

            majority_class_avg_proba = majority_class_avg_proba / len(ref_samples)

            if majority_class_avg_proba < CNN_PROBABILITY_THRESH:
                majority_class_label = "unknown"
            else:
                majority_class_label = model_config["classes"][majority_class]

            r.set_scene_tag(majority_class_label, inferred_by="cnn-%s" % model_config["model_name"])

        # Try to free up the classifier allocated resources.
        del classifier

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
                logging.info("Comparing to prevGood: %f" % prevResult.rms)

                if prevResult.rms < rms_threshold:
                    regions.static_at(i).set_scene_tag(regions.static_at(prevGood).scene_tag,
                                                            inferred_by="similarityToPrevNeighbor")
                    logging.info("Inferred tag %s by comparison to previous "
                                 "good match" %
                                 regions.static_at(prevGood).scene_tag)
                    continue
                else:
                    logging.info("Unknown region %d does not match "
                                 "previous region %d rms = %f" %
                                 (i, prevGood, prevResult.rms))

            elif nextGood is not None:
                # TODO: use ImageComparer instead
                nextResult = self.comparer.compare_images(self.images[nextGood][0], self.images[i][0])
                logging.info("Comparing to nextGood: %f" % nextResult.rms)

                if nextResult.rms < rms_threshold:
                    regions.static_at(i).set_scene_tag( regions.static_at(nextGood).scene_tag,
                                                                inferred_by="similarityToNextNeighbor")
                    logging.info("Inferred tag %s by comparison to previous "
                                "good match" % regions.static_at(nextGood).scene_tag)
                    continue
                else:
                    logging.info("Unknown region %d does not match "
                                "next region %d, rms = %f" % (i, nextGood, nextResult.rms))


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

                        region.set_scene_tag( REFERENCE_SEQUENCE[k+eta],
                                                    inferred_by="sequence")

                        logging.info("Inferred type %s by sequence" % regions.static_at(i).scene_tag)

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
