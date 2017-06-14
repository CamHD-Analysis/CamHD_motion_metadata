
import glob
import logging
import argparse
import os.path
import subprocess

REGION_ANALYSIS = "../camhd_motion_analysis/python/region_analysis.py"

parser = argparse.ArgumentParser(description='CamHD RQ Worker.')

parser.add_argument('--dry-run', dest='dryrun', action='store_true', help='Dry run')

parser.add_argument('--force', dest='force', action='store_true', help='')

parser.add_argument('--log', metavar='log', nargs='?', default='WARNING',
                    help='Logging level')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )

for infile in glob.iglob("**/*_optical_flow.json", recursive=True):
    outfile = os.path.splitext(infile)[0] + "_regions.json"

    logging.info("Processing %s, Saving results to %s" % (infile, outfile) )

    if os.path.isfile( outfile ) and args.force == False:
        logging.warning("Skipping %s, it already exists" % outfile )
    elif args.dryrun == False:
        procout = subprocess.run( ["python3", REGION_ANALYSIS,
                                               "--output", outfile,
                                                infile ],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                encoding='utf8' )

        logging.info(procout.stdout )
        #logging.info(procout.stderr )
