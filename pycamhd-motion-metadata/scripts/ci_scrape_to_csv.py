#!/usr/bin/env python3
#
# TODO:   Parse CamHD filename into UTC time and add to CSV file

import glob
import logging
import argparse
import os.path as path
import os
import csv
import json
import re
import datetime

parser = argparse.ArgumentParser(description='Convert JSON scrape files to a flat CSV format')

parser.add_argument('input', metavar='inputfiles', nargs='+',
                    help='JSON files to process')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--output', dest='outfile', nargs='?', default='movie_metadata.csv', help='Output .csv file')

args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )

logging.info("Outfile is %s" % args.outfile)

datetimere = re.compile("CAMHDA301-(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})")


with open(args.outfile, 'w') as f:
    csv_file = csv.writer(f)

    csv_file.writerow(["mov_basename","date_time","num_frames","duration","file_size"])

    for json_file in args.input:

        with open(json_file) as f:
            j = json.load(f)

            for url,data in j.items():
                mov = path.splitext(path.basename(url))[0]

                if 'NumFrames' not in data:
                    logging.warning("Error with movie %s" % mov)
                    continue

                match = re.match(datetimere, mov)

                dt = None
                if match:
                    dt = datetime.datetime(int(match.group(1)), int(match.group(2)),
                                             int(match.group(3)), int(match.group(4)),
                                             int(match.group(5)), int(match.group(6))).isoformat()
                else:
                    logging.warning("Error parsing date from %s" % mov )

                csv_file.writerow( [mov, dt, data['NumFrames'], data['Duration'], data['FileSize']] )
