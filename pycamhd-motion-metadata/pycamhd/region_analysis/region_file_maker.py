#!/usr/bin/env python3

import pycamhd.motionmetadata as mdd

from .find_regions import find_regions, find_regions_version
from .classify_regions import classify_regions_version, RegionClassifier
#from .similarity_analysis import *

from .timer import Timer
import logging
import os


class RegionFileMaker:
    # RegionFileMaker is the top level class called by make_regions_file.
    def __init__(self, force=False, dryrun=False, noclassify=False, first=None, gt_library=None,
                 use_cnn=False, cnn_classifier=None, cnn_model_config=None, lazycache=None):
        self.force = force
        self.dryrun = dryrun
        self.noclassify = noclassify
        self.first = first
        self.gt_library = gt_library

        if use_cnn:
            if not cnn_classifier or not cnn_model_config:
                raise ValueError("If the 'use_cnn' argument is True, then the 'cnn_classifier' and 'cnn_model_config' "
                                 "must be provided.")

        self.use_cnn = use_cnn
        self.cnn_classifier = cnn_classifier
        self.cnn_model_config = cnn_model_config

        self.lazycache = lazycache

    def make_region_file(self, infile, outfile):
        logging.info("Processing %s, Saving results to %s" % (infile, outfile))

        timing = {}
        with Timer() as full_time:

            oflow = mdd.OpticalFlowFile(infile)

            if oflow.valid.empty:
                logging.info("It doesn't look like there are any regions in this optical flow file")
                return

            with Timer() as t:
                regions = find_regions(oflow)
            timing['regionAnalysis'] = t.interval

            regions.json['versions']['findRegions'] = find_regions_version

            regions.squash_gaps( delta=30 )

            regions.json['performance'] = {'timing': timing}

            # Write results as a checkpoint
            if not self.dryrun:
                logging.info("Created the regions_file (unclassified): %s" % outfile)
                regions.save_json(outfile)

            if not self.noclassify:
                try:
                    if self.use_cnn:
                        with Timer() as t:
                            # TODO: By default the RegionClassifier uses a trained CNN model,
                            # TODO: therefore, we send None for comparer. A better way of defaulting this behaviour and
                            # TODO: providing custom CNN models can be allowed.
                            region_classifier = RegionClassifier(None, self.lazycache)
                            regions = region_classifier.classify_regions_cnn(regions,
                                                                             classifier=self.cnn_classifier,
                                                                             model_config=self.cnn_model_config,
                                                                             first=self.first)
                            logging.info("Classified url: %s" % regions.mov)
                    else:
                        with Timer() as t:
                            classifier = self.gt_library.select(regions)
                            regions = RegionClassifier(classifier, self.lazycache).classify_regions(regions,
                                                                                                    first=self.first)
                            logging.info("Classified url: %s" % regions.mov)

                    timing['classification'] = t.interval

                    regions.json['versions']['classifyRegions'] = classify_regions_version
                except:
                    if not self.dryrun:
                        os.remove(outfile)

                    logging.error("Encountered an error while classifying regions. "
                                  "Deleted the regions_file to maintain consistency: %s" % outfile)
                    raise

        timing['elapsedSeconds'] = full_time.interval

        # regions.squash_scene_tag_sandwiches()

        regions.json['performance'] = {'timing': timing}

        # Write results
        if not self.dryrun:
            logging.info("Created the regions_file (classified): %s" % outfile)
            regions.save_json(outfile)
