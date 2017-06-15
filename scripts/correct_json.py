#!/usr/bin/env python3
#
#  Macros and regexp to "correct" JSON files to newer formats
#

import glob
import logging
import argparse
import os.path
import subprocess


parser = argparse.ArgumentParser(description='correct JSON')

parser.add_argument('input', metavar='N', nargs='*', default=['RS03ASHS/**/*_optical_flow.json'],
                    help='Files or paths to process')

parser.add_argument('--dry-run', dest='dryrun', action='store_true', help='Dry run, don\'t actually process')

#parser.add_argument('--force', dest='force', action='store_true', help='')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')


parser.add_argument('--git-add', dest='gitadd', action='store_true', help='Run "git add" on resulting file')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )




for path in args.input:
    for infile in glob.iglob( path, recursive=True):
        # outfile = os.path.splitext(infile)[0] + "_regions.json"
        #
        # logging.info("Processing %s, Saving results to %s" % (infile, outfile) )
        #
        # if os.path.isfile( outfile ) and args.force == False:
        #     logging.warning("Skipping %s or run with --force to overwrite" % outfile )
        # elif args.dryrun == False:
        #     procout = subprocess.run( ["python3", REGION_ANALYSIS,
        #                                            "--output", outfile,
        #                                             infile ],
        #                             stdout=subprocess.PIPE,
        #                             stderr=subprocess.PIPE,
        #                             encoding='utf8' )
        #
        #     logging.info( "stdout: %s" % procout.stdout )
        #     logging.info( "stderr: %s" % procout.stderr )
        #
        #     if os.path.isfile( outfile ) and args.gitadd:
        #         subprocess.run( [ "git", "add", outfile ] )
