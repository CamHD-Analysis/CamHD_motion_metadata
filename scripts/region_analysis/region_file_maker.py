

import logging
import json

from .timer import *
from .find_regions import *
from .classify_regions import *
from .similarity_analysis import *


import pycamhd.motionmetadata as mdd


class RegionFileMaker:
    # RegionFileMaker is the top level class called by make_regions_file.
    #


    def __init__(self, force=False, dryrun=False,
                 noclassify=False, first=None,
                 gt_library=None, lazycache=None):

        self.force = force
        self.dryrun = dryrun
        self.noclassify = noclassify
        self.first = first
        self.gt_library = gt_library
        self.lazycache = lazycache


    def make_region_file(self, infile, outfile):

        logging.info("Processing %s, Saving results to %s" % (infile, outfile))

        timing = {}
        with Timer() as full_time:

            oflow = mdd.OpticalFlowFile(infile)

            with Timer() as t:
                regions = find_regions(oflow)
            timing['regionAnalysis'] = t.interval

            regions.json['versions']['findRegions'] = find_regions_version

            regions.squash_gaps( delta=30 )


            regions.json['performance'] = {'timing': timing}

            # Write results as a checkpoint
            if not self.dryrun:
                regions.save_json(outfile)

            if not self.noclassify:
                with Timer() as t:
                    classifier = self.gt_library.select(regions)

                    regions = RegionClassifier( classifier, self.lazycache ).classify_regions(regions, first=self.first)


                timing['classification'] = t.interval

                regions.json['versions']['classifyRegions'] = classify_regions_version

        timing['elapsedSeconds'] = full_time.interval

        #regions.squash_scene_tag_sandwiches()

        regions.json['performance'] = {'timing': timing}

        # Write results
        if not self.dryrun:
            regions.save_json(outfile)
