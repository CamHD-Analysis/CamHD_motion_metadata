#!/usr/bin/env python3

import json
import logging
import argparse
import glob
import re

import pandas as pd
import numpy as np
import os
import os.path as path

import pycamhd.lazycache as camhd

parser = argparse.ArgumentParser(description='')

parser.add_argument('input', metavar='N', nargs='+',
                    help='*_classify.json file to analyze')

# parser.add_argument('--base-dir', dest='basedir', metavar='o', nargs='?',
#                     help='Base directory')

parser.add_argument('--output-dir', dest='outdir', metavar='o', nargs='?', default="_html/",
                    help='Directory for output')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

# parser.add_argument('--lazycache-url', dest='lazycache', default=os.environ.get("LAZYCACHE_URL", "http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files"),
#                     help='URL to Lazycache repo server')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )

#qt = camhd.lazycache( args.lazycache )

data = {}

for input_path in args.input:
    for infile in glob.iglob( input_path, recursive=True ):

        logging.info( "Processing %s" % infile)

        with open(infile) as input:
            class_map = json.load(input)

        for key,value in class_map.items():
            if value not in data.keys():
                data[value] = []

            data[value].append(key)



def write_subfile( tag, filename, imgs ):

    logging.info("Saving %s to %s" % (tag, filename))

    with open( filename, "w" ) as index:
        index.write("<html><body>\n")

        index.write("<h1>%s</h1>\n" % tag )

        for i in imgs:
            alt_tag = i
            relapath = "../" + i
            index.write("<img title=\"%s\" width=320 src=\"%s\">" %
                            (alt_tag, relapath))


        index.write("</body></html>")


os.makedirs( args.outdir, exist_ok=True )

index_path = args.outdir + "index.html"
with open( index_path, 'w' ) as index:

    index.write("<html><body>\n")
    index.write("<ul>\n")

    for tag in sorted(data):
        imgs = data[tag]

        safe_tag = tag.replace( '/', '_')

        index.write("<li><a href=\"%s.html\">%s</a>  (%d images)</li>" % (safe_tag,tag,len(imgs)) )

        write_subfile( tag, "%s%s.html" % (args.outdir,safe_tag), imgs )

    index.write("</ul></body></html>")
