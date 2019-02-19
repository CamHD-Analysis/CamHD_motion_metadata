
from keras.models import load_model
from scipy.stats import mode

import logging
import json
import os

import numpy as np

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
CNN_PROBABILITY_THRESH = 0.20

# TODO: A better way to manage models and model_configs?
CLASSIFIERS_META_FILE = "scene_tag_classifiers_meta.json"

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
                            Default: Three frames at (0.4, 0.5, 0.6) will be chosen.
                            TODO: Change this to a single frame at 0.5, to reduce time taken for processing.
        :return: The updated regions (RegionFile object) with the scene_tag predictions.

        """
        def _sequence_based_correction(prev_scene_tag, cur_pred_scene_tag):
            """
            The regions p2_z1 and p4_z2 look very similar (plain water), hence they are corrected based on sequence.

            """
            is_corrected = False
            if prev_scene_tag is None:
                return cur_pred_scene_tag, is_corrected

            deployment = prev_scene_tag.split("_")[0]
            p2_z0_tag = "%s_p2_z0" % deployment
            p2_z1_tag = "%s_p2_z1" % deployment
            p4_z1_tag = "%s_p4_z1" % deployment
            p4_z2_tag = "%s_p4_z2" % deployment
            plain_water_tag = "%s_plain_water" % deployment

            if cur_pred_scene_tag in (p2_z1_tag, plain_water_tag) and prev_scene_tag in (p4_z1_tag, p4_z2_tag):
                is_corrected = True
                return p4_z2_tag, is_corrected

            if cur_pred_scene_tag in (p4_z2_tag, plain_water_tag) and prev_scene_tag in (p2_z0_tag, p2_z1_tag):
                is_corrected = True
                return p2_z1_tag, is_corrected

            return cur_pred_scene_tag, is_corrected

        CAMHD_SCENETAG_DATA_DIR = os.environ.get("CAMHD_SCENETAG_DATA_DIR", None)
        if not CAMHD_SCENETAG_DATA_DIR:
            raise ValueError("The %s needs to be set in the environment while using CNN." % CAMHD_SCENETAG_DATA_DIR)
        if not os.path.exists(CAMHD_SCENETAG_DATA_DIR):
            raise ValueError("The $CAMHD_SCENETAG_DATA_DIR does not exist: %s" % CAMHD_SCENETAG_DATA_DIR)

        with open(CLASSIFIERS_META_FILE) as fp:
            classifiers_meta_dict = json.load(fp)

        latest_model = classifiers_meta_dict["latest_model"]
        model_config = classifiers_meta_dict["trained_models"][latest_model]
        classifier = load_model(os.path.expandvars(model_config["model_path"]))

        num_to_process = len(regions.static_regions())

        if first:
            num_to_process = min(first, num_to_process)

        prev_scene_tag = None
        for i in range(num_to_process):

            r = regions.static_at(i)

            logging.info("Attempting to classify region from %d to %d" % (r.start_frame, r.end_frame))

            ref_images = []

            for sample_pct in ref_samples:
                frame = r.frame_at(sample_pct)
                logging.info("Retrieving test frame %d" % frame)

                width, height = model_config["input_shape"][:2]
                ref_img = self.lazycache.get_frame(regions.mov, frame, format='png', width=width, height=height)
                ref_img = np.array(ref_img)

                if ref_img.shape != tuple(model_config["input_shape"]):
                    raise RuntimeError("The retrieved frame shape doesn't conform with model's input_shape: %s"
                                       % str(ref_img.shape))

                if model_config["rescale"] is True:
                    rescaled_image = ref_img * (1.0 / 255)
                    ref_images.append(rescaled_image)
                else:
                    ref_images.append(ref_img)

            self.images[i] = ref_images
            input_tensor = np.asarray(ref_images)
            pred_probas = classifier.predict(input_tensor)
            pred_classes = np.argmax(pred_probas, axis=1)

            class_probas = []
            for i, pred_class in enumerate(pred_classes):
                class_probas.append(pred_probas[i][pred_class])

            logging.info("Unique pred_classes: %s" % len(set(pred_classes)))
            logging.info("pred_classes: %s, pred_probas: %s" % (str(pred_classes), str(class_probas)))

            majority_class_by_cnn = mode(pred_classes)[0][0]
            majority_class_avg_proba_by_cnn = 0
            for pred_class, class_proba in zip(pred_classes, class_probas):
                if pred_class == majority_class_by_cnn:
                    majority_class_avg_proba_by_cnn += class_proba

            majority_class_avg_proba_by_cnn = majority_class_avg_proba_by_cnn / len(ref_samples)

            cur_pred_scene_tag_by_cnn = model_config["classes"][majority_class_by_cnn]
            cur_pred_scene_tag_sequence_corrected, is_corrected = _sequence_based_correction(prev_scene_tag,
                                                                                             cur_pred_scene_tag_by_cnn)

            if majority_class_avg_proba_by_cnn < CNN_PROBABILITY_THRESH:
                logging.info("The predicted scene_tag %s has lower average predicted probability: %s (threshold: %s). "
                             "Therefore, marking this region as 'unknown'."
                             % (cur_pred_scene_tag_by_cnn, majority_class_avg_proba_by_cnn, CNN_PROBABILITY_THRESH))
                majority_class_label = "unknown"
            else:
                majority_class_label = cur_pred_scene_tag_sequence_corrected

            prev_scene_tag = cur_pred_scene_tag_sequence_corrected

            inferred_by =  "cnn-%s" % model_config["model_name"]
            if is_corrected:
                inferred_by = "%s-sequence_corrected" % inferred_by

            # Set the scene tag for the region.
            r.set_scene_tag(majority_class_label, inferred_by=inferred_by)

            # Set the Predicted probabilities in sceneTagMeta.
            # TODO: Should we keep pred_probas of all the class_labels?
            # TODO: Should we keep the corrected scene_tag or the original scene_tag predicted by CNN?
            r.json['sceneTagMeta']["predProbas"] = {cur_pred_scene_tag_by_cnn: majority_class_avg_proba_by_cnn}

            # Set the 'algoFinalLabel' in the sceneTagMeta, which would contain the final scene_tag inferred
            # automatically through algorithmic postprocessing.
            # This helps to evaluate the overall algorithmic performance.
            r.json['sceneTagMeta']["algoFinalLabel"] = majority_class_label

        # TODO: Do we need to include any information in the depends section of the regions_file json?

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
