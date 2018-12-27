

import logging
import json

from .timer import *
from .find_regions import *
from .classify_regions import *
#from .similarity_analysis import *


import pycamhd.motionmetadata as mdd


class RegionFileMaker:
    # RegionFileMaker is the top level class called by make_regions_file.
    #


    def __init__(self, force=False, dryrun=False,
                 noclassify=False, first=None,
                 gt_library=None, use_cnn=False, lazycache=None):

        self.force = force
        self.dryrun = dryrun
        self.noclassify = noclassify
        self.first = first
        self.gt_library = gt_library
        self.use_cnn = use_cnn
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
                            regions = RegionClassifier(None, self.lazycache).classify_regions_cnn(regions,
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

        #regions.squash_scene_tag_sandwiches()

        regions.json['performance'] = {'timing': timing}

        # Write results
        if not self.dryrun:
            logging.info("Created the regions_file (classified): %s" % outfile)
            regions.save_json(outfile)
