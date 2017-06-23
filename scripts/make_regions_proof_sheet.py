#!/usr/bin/env python3


import glob
import logging
import argparse
import os.path as path
import os
import json

import region_analysis as ra


#import camhd_motion_analysis as ma


parser = argparse.ArgumentParser(description='Generate HTML proofs')

parser.add_argument('input', metavar='N', nargs='*',
                    help='Files or paths to process')

parser.add_argument('--force', dest='force', action='store_true', help='Force re-download of images')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--output-dir', dest='outdir', nargs='?', default='_html/', help='Directory for output')

parser.add_argument('--lazycache-url', dest='lazycache', default=os.environ.get("LAZYCACHE_URL", "http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files"),
                    help='URL to Lazycache repo server (only needed if classifying)')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )


import pycamhd.lazycache as camhd
qt = camhd.lazycache( args.lazycache )

# classifier = ra.Classifier()
# classifier.load( "classification/images/" )


for pathin in args.input:
    for infile in glob.iglob( pathin, recursive=True):


        with open(infile) as data_file:
            jin = json.load( data_file )

        mov = jin["movie"]
        url = mov['URL']
        name = path.splitext( path.basename( url ))[0]

        html_file = args.outdir + "%s.html" % name
        img_path  = args.outdir + name + "/"

        os.makedirs( img_path, exist_ok = True )


        with open(html_file, 'w') as html:
            html.write("<html><body>\n")
            html.write("<h2>%s</h2>\n\n" % name)

            html.write("<table>\n<tr><th>Start Frame</th><th>End Frame</th><th>Classification</th><th>Sample Image</th</tr>\n")
            #><th>Reference image from class</th>\n")

            for r in jin["regions"]:

                if r['type'] != "static":
                    continue

                html.write("<tr>")
                html.write("<td>%d</td><td>%d</td>" % (r['startFrame'], r['endFrame']) )

                if "sceneTag" in r.keys():
                    html.write("<td>%s</td>" % r["sceneTag"])
                else:
                    html.write("<td><<b>unclassified</b></td>")

                sample_frame = r['startFrame'] + 0.5 * (r['endFrame'] - r['startFrame'])

                img_file = img_path + "%d.png" % sample_frame
                if args.force or not path.exists( img_file ):
                    logging.info("Fetching frame %d from %s for contact sheet" % (sample_frame, name))
                    img = qt.get_frame( url, sample_frame, format='png' )
                    img.save( img_file )

                relapath = path.relpath( img_file, path.dirname(html_file) )
                html.write("<td><img width=640 src=\"%s\"/></td>" % (relapath) )

                # html.write("<td>")
                # if "sceneTag" in r.keys() and len(r['sceneTag']) > 0:
                #     first = r['sceneTag'][0]
                #     if  first in classifier.tags():
                #         paths = classifier.sample_paths( first, 3 )
                #
                #         relapaths = [ path.relpath(p, path.dirname(html_file) ) for p in paths]
                #
                #         for r in relapaths:
                #             html.write("<img width=640 src=\"%s\"/>" % r)
                #
                # html.write("</td>")
                html.write("</tr>\n")


            html.write("</table>")
            html.write("</body></html>")
