

import logging
import json

from .timer import *
from .optical_flow_file import *
from .find_regions import *


class RegionFileMaker:

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

            oflow = OpticalFlowFile(infile)

            with Timer() as t:
                regions = find_regions(oflow)
            timing['regionAnalysis'] = t.interval

            # if 'versions' not in jout:
            #     jout['versions'] = {}
            regions.json['versions']['findRegions'] = find_regions_version

            regions.json['performance'] = {'timing': timing}

            # Write results as a checkpoint
            if not self.dryrun:
                regions.save_json(outfile)

            if not self.noclassify:
                with Timer() as t:
                    classifier = self.gt_library.select(regions)

                    classify_regions(regions,
                                     classifier,
                                     lazycache=self.qt,
                                     first_n=self.first)

                timing['classification'] = t.interval

                regions.json['versions']['classifyRegions'] = classify_regions_version

        timing['elapsedSeconds'] = full_time.interval

        regions.json['performance'] = {'timing': timing}

        # Write results
        if not self.dryrun:
            regions.save_json(outfile)
