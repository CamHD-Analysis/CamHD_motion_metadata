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

parser.add_argument('input', metavar='inputfiles', nargs='+',
                    help='Regions files to process')

parser.add_argument('--force', dest='force', action='store_true', help='Force re-download of images')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--output', dest='outfile', nargs='?', default='_html/proof.html', help='Output .html file')

parser.add_argument('--image-size', dest='imgsize', nargs='?', default='320x240')

parser.add_argument('--lazycache-url', dest='lazycache', default=os.environ.get("LAZYCACHE_URL", "http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files"),
                    help='URL to Lazycache repo server (only needed if classifying)')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )


import pycamhd.lazycache as camhd
qt = camhd.lazycache( args.lazycache )

img_size = args.imgsize.split('x')
img_size = ( int(img_size[0]), int(img_size[1]))
print(img_size)

# classifier = ra.Classifier()
# classifier.load( "classification/images/" )

tags = []
images = []
urls = []

for pathin in args.input:
    for infile in glob.iglob( pathin, recursive=True):

        with open(infile) as data_file:
            jin = json.load( data_file )

            if 'regions' not in jin:
                logging.info("No regions in file %s" % infile)
                continue

            url = jin['movie']['URL']
            urls.append(url)

            idx = 0
            for r in jin["regions"]:
                if r['type'] != 'static':
                    continue

                if 'sceneTag' not in r:
                    logging.info("Hm, static regions aren't tagged")
                    continue

                sceneTag = r['sceneTag']

                logging.info("%s (%d,%d): %s" % (url, r['startFrame'], r['endFrame'], sceneTag))

                if idx >= len(images):
                    tags.append(sceneTag)
                    images.append( {url: r })
                elif sceneTag == tags[idx]:
                    images[idx][url] = r
                else:
                    logging.info("Tag doesn't match order...")

                    for i in range(idx,len(tags)):
                        if sceneTag == tags[i]:
                            images[i][url] = r
                            idx = i
                            break


                # On success
                idx += 1

img_path  = path.dirname(args.outfile) + "/images/"
os.makedirs(img_path, exist_ok=True)


html_file = args.outfile
with open(html_file, 'w') as html:
    html.write("<html><body>\n")
    html.write("<h2>Proof sheet</h2>\n\n")

    html.write("<table>\n<tr><th>Scene Tag</th>")
    for name in urls:
        html.write("<th>%s</th>" % path.basename(name))
    html.write("</tr>\n")
    #><th>Reference image from class</th>\n")

    for row in range(len(images)):
        html.write("<tr>")
        html.write("<td>%s</td>" % (tags[row]) )

        for url in urls:
            if url not in images[row]:
                html.write("<td></td>")
                continue

            region = images[row][url]

            sample_frame = region['startFrame'] + 0.5 * (region['endFrame'] - region['startFrame'])

            img_file = img_path + "%s_%d.jpg" % (path.splitext(path.basename(url))[0], sample_frame)
            thumb_file = img_path + "%s_%d_thumbnail.jpg" % (path.splitext(path.basename(url))[0], sample_frame)

            if args.force or not path.exists( img_file ) or not path.exists( thumb_file ):
                logging.info("Fetching frame %d from %s for contact sheet" % (sample_frame, path.basename(url)))
                img = qt.get_frame( url, sample_frame, format='jpg' )
                img.save( img_file )
                img.thumbnail( img_size )  # PIL.thumbnail preserves aspect ratio

                img.save( thumb_file )

            relapath = path.relpath( img_file, path.dirname(html_file) )
            relathumb = path.relpath( thumb_file, path.dirname(html_file) )

            html.write("<td><a href=\"%s\"><img src=\"%s\"/></a><br>%d -- %d</td>" % (relapath,relathumb,region['startFrame'],region['endFrame']) )


        html.write("</tr>")

    # for r in jin["regions"]:
    #
    #     if r['type'] != "static":
    #         continue
    #
    #     html.write("<tr>")
    #     html.write("<td>%d</td><td>%d</td>" % (r['startFrame'], r['endFrame']) )
    #
    #     if "sceneTag" in r.keys():
    #         html.write("<td>%s</td>" % r["sceneTag"])
    #     else:
    #         html.write("<td><<b>unclassified</b></td>")
    #
    #
    #     img_file = img_path + "%d.png" % sample_frame
    #     if args.force or not path.exists( img_file ):
    #         logging.info("Fetching frame %d from %s for contact sheet" % (sample_frame, name))
    #         img = qt.get_frame( url, sample_frame, format='png' )
    #         img.save( img_file )
    #
    #     relapath = path.relpath( img_file, path.dirname(html_file) )
    #     html.write("<td><img width=640 src=\"%s\"/></td>" % (relapath) )
    #
    #     # html.write("<td>")
    #     # if "sceneTag" in r.keys() and len(r['sceneTag']) > 0:
    #     #     first = r['sceneTag'][0]
    #     #     if  first in classifier.tags():
    #     #         paths = classifier.sample_paths( first, 3 )
    #     #
    #     #         relapaths = [ path.relpath(p, path.dirname(html_file) ) for p in paths]
    #     #
    #     #         for r in relapaths:
    #     #             html.write("<img width=640 src=\"%s\"/>" % r)
    #     #
    #     # html.write("</td>")
    #     html.write("</tr>\n")


    html.write("</table>")
    html.write("</body></html>")
