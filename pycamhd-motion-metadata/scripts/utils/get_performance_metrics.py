#!/usr/bin/env python3

"""
Generate the confusion matrix from a given set of regions files which have been validated (QC).

Usage: (Running from the root directory of the repository.)
python scripts/utils/get_performance_metrics.py ../RS03ASHS/PN03B/06-CAMHDA301/2018/07/2[56789] --labels ../classification/labels/d5A_labels.json --outfile ../temp_out.csv --cm-plot

"""

import argparse
import glob
import itertools
import json
import logging
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

from sklearn.metrics import accuracy_score, confusion_matrix

def get_args():
    parser = argparse.ArgumentParser(description="Get the performance metrics for given set of processed (validated) regions files.")

    parser.add_argument('input',
                        metavar='N',
                        nargs='*',
                        help='Files or paths to process.')
    parser.add_argument('--labels',
                        required=True,
                        help='The file path containing the list of labels. The same order of labels will be inferred.')
    parser.add_argument('--outfile',
                        help='The file path (CSV) to which the output needs to be written to.')
    parser.add_argument('--cm-plot',
                        action="store_true",
                        help='The file path to which the confusion_matrix plot needs to be saved.')
    parser.add_argument("--log",
                        default="WARN",
                        help="Specify the log level. Default: WARN.")

    return parser.parse_args()


def _get_pred_true_labels(regions_file_path):
    pred_true_labels = []

    with open(regions_file_path) as fp:
        regions_doc = json.load(fp)

    regions = regions_doc["regions"]
    for region in regions:
        if region["type"] != "static":
            continue

        scene_tag_meta = region["sceneTagMeta"]
        true_label = region["sceneTag"]

        if "topTenPct" in scene_tag_meta:
            # Correlation based classification:
            # These are the errors mapped to each of the labels predicted (includes only top labels).
            meta_pred_dict = scene_tag_meta["topTenPct"]
            pred_label = min(meta_pred_dict.items(), key=lambda x: x[1])[0]
        elif "algoFinalLabel" in scene_tag_meta:
            pred_label = scene_tag_meta["algoFinalLabel"]
        elif "predProbas" in scene_tag_meta:
            # CNN based classification: these contain predicted probabilities.
            meta_pred_dict = scene_tag_meta["predProbas"]
            pred_label = max(meta_pred_dict.items(), key=lambda x: x[1])[0]
        else:
            logging.info("Predicted label couldn't be found for region from %s to %s for region URL: %s"
                         % (region.start_frame, region.end_frame, region.mov))
            continue

        pred_true_labels.append((pred_label, true_label))

    return pred_true_labels


def _get_num_match_by_hand(regions_file_path):
    cur_num_match_by_hand = 0

    with open(regions_file_path) as fp:
        regions_doc = json.load(fp)

    regions = regions_doc["regions"]
    for region in regions:
        if region["type"] != "static":
            continue

        scene_tag_meta = region["sceneTagMeta"]
        if scene_tag_meta["inferredBy"] == "matchByHand":
            cur_num_match_by_hand += 1

    return cur_num_match_by_hand


def _format_write_conf_mat(conf_mat, labels, fp):
    conf_mat_object = np.array(conf_mat, dtype=object)
    temp_mat = np.vstack((np.array(labels, dtype=object), conf_mat_object))
    labels_header = np.array([["conf_mat"] + labels], dtype=object).reshape((-1, 1))
    printable_mat = np.hstack((labels_header, temp_mat))

    for row in printable_mat:
        line = ",".join([str(x) for x in row]) + "\n"
        fp.write(line)


def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.

    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        logging.info("Normalized confusion matrix")
    else:
        logging.info('Confusion matrix, without normalization')

    logging.debug(cm)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()


def get_performance_metrics(args):
    all_pred_true_labels = []
    all_num_match_by_hand_list = []

    def _process(infile):
        logging.info("Reading from {}".format(infile))
        cur_pred_true_labels = _get_pred_true_labels(infile)
        all_pred_true_labels.extend(cur_pred_true_labels)
        cur_num_match_by_hand = _get_num_match_by_hand(infile)
        all_num_match_by_hand_list.append(cur_num_match_by_hand)
        logging.info("The length of current pred_true_labels is: {}".format(len(cur_pred_true_labels)))

    for pathin in args.input:
        for infile in glob.iglob(pathin):
            if os.path.isdir(infile):
                infile = os.path.join(infile, "*_regions.json")
                for f in glob.iglob(infile):
                    _process(f)
            else:
                _process(infile)

    # The pred_true_labels from all the target validated regions files have been collected.
    total_num_static_regions = len(all_pred_true_labels)
    overall_algo_accuracy = 1 - float(sum(all_num_match_by_hand_list)) / total_num_static_regions

    labels_file = args.labels
    with open(labels_file) as fp:
        labels = json.load(fp)

    y_pred = [x[0] for x in all_pred_true_labels]
    y_true = [x[1] for x in all_pred_true_labels]

    accuracy = accuracy_score(y_true, y_pred)
    conf_mat = confusion_matrix(y_true, y_pred, labels=labels)

    # Format and output the confusion matrix.
    fp = open(args.outfile, "w") if args.outfile else sys.stdout
    header_lines = [
        "Overall Algorithm Accuracy,{}".format(overall_algo_accuracy),
        "Total Accuracy,{}".format(accuracy),
        "Total scenes,{}".format(total_num_static_regions)
    ]
    fp.write("\n".join(header_lines) + "\n\n")
    _format_write_conf_mat(conf_mat, labels, fp)
    fp.close()

    if args.cm_plot:
        np.set_printoptions(precision=2)
        plt.figure()
        plot_confusion_matrix(conf_mat, classes=labels, title='Confusion Matrix')
        # TODO: Should we save this or just show the plot and let the user decide whether to save?
        plt.show()


if __name__ == "__main__":
    args = get_args()
    logging.basicConfig(level=args.log.upper())
    get_performance_metrics(args)
