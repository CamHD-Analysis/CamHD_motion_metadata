#!/usr/bin/env python3


import glob
import logging
import argparse
import os.path as path
import os
import random
import re
import time

import pycamhd.region_analysis as ra

import pycamhd.lazycache as camhd
import pycamhd.motionmetadata as mmd

parser = argparse.ArgumentParser(description='Generate HTML proofs')

parser.add_argument('input', metavar='inputfiles', nargs='+',
                    help='Regions files to process')

parser.add_argument('--force', dest='force', action='store_true', help='Force re-download of images')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--output', dest='outfile', nargs='?', default='_html/proof.html', help='Output .html file')

parser.add_argument('--image-size', dest='imgsize', nargs='?', default='320x240')

parser.add_argument('--with-groundtruth', dest='groundtruth', action='store_true', 
            help = 'Whether or not to use ground truth files. Uses a hard coded sequence of tags otherwise.')

parser.add_argument("--ground-truth", dest="groundtruthfile",
                    default="classification/ground_truth.json")

parser.add_argument("--image-format", dest="imageext", default='jpg')

parser.add_argument('--lazycache-url', dest='lazycache', default=os.environ.get("LAZYCACHE_URL", None),
                    help='URL to Lazycache repo server (only needed if classifying)')

args = parser.parse_args()

IMAGE_RESOLUTION = (426, 240) # Preserves the 16:9 aspect ratio from the original 1920x1080 images.

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig( level=args.log.upper() )

logging.info("Outfile is %s" % args.outfile)

qt = camhd.lazycache( args.lazycache )

img_size = args.imgsize.split('x')
img_size = ( int(img_size[0]), int(img_size[1]))


## TODO.  This needs to be done in a more permanent way
blacklist = [ "CAMHDA301-20170915T184600_optical_flow_regions.json" ]


tags = []
images = []
urls = []

gt_urls = []

if args.groundtruth:
    gt_library = ra.GroundTruthLibrary()
    gt_library.load_ground_truth(args.groundtruthfile)

    gt_path = random.sample(gt_library.regions.keys(), 1)

    logging.info("Using ground truth image %s" % gt_path)

    url = gt_library.urls[gt_path[0]]

    for r in gt_library.regions[gt_path[0]].static_regions():
        tags.append(r.scene_tag.split('_',1)[1])
        images.append({url: [r]})

    urls.append(url)
    gt_urls.append(url)
else: # hard coded sequence
    REFERENCE_SEQUENCE = [
                      "p1_z0", "p1_z1", "p0_z0", 
                      "p2_z0", "p2_z1", "p2_z2", "p2_z0", "p0_z0", 
                      "p3_z0", "p3_z1", "p3_z2", "p3_z0", "p0_z0",
                      "p4_z0", "p4_z1", "p4_z2", "p4_z0", "p0_z0", 
                      "p5_z0", "p5_z1", "p5_z2", "p5_z0", "p0_z0", 
                      "p6_z0", "p6_z1", "p6_z2", "p6_z0", "p0_z0",
                      "p0_z1", "p0_z2", "p0_z0",
                      "p7_z0", "p7_z1", "p7_z0", "p0_z0", 
                      "p8_z0", "p8_z1", "p8_z0", "p0_z0", "p1_z0"]

    tags = REFERENCE_SEQUENCE
    images = [{} for i in range(len(tags))]
tags.append("excess") # handles overflow and scenarios where the algorithm fails

unknowns = {}

def scene_tag_match( a, b ):
    ## Disregard deployment
    astem = re.sub( r'd\d{1}_', "", a )
    bstem = re.sub( r'd\d{1}_', "", b )

    logging.debug("a    : %s;  b     = %s" % (a,b))
    logging.debug("astem: %s;  bstem = %s" % (astem,bstem))

    return astem == bstem


def _format_url(name):
    date, time = os.path.splitext(os.path.basename(name))[0].split('-')[1].split('T')
    res = "%s%s | %s T %s" % (date[:4], date[4:6], date[6:], time[:4])
    return res


def process( infile ):
    logging.info("Processing %s" % infile)

    regions = mmd.RegionFile.load(infile)

    mov = regions.mov

    # Skip if already processed  (handles ground truth files)
    if  mov in urls:
        return

    if os.path.basename(infile) in blacklist:
        return

    urls.append(mov)

    unknowns[mov] = []
    for tag in images:
        tag[mov] = []

    prevTag = None
    index = 0
    for r in regions.static_regions():

        # will do poorly if there are misclassifications or general mistakes in the order

        # classifications as unknown are preferred over misclassifications

        if r.unknown or not r.scene_tag or r.scene_tag == "unknown":
            unknowns[mov].append(r)
            continue

        scene_tag = r.scene_tag.split('_', 1)[1]

        if scene_tag == prevTag:
            images[index-1][mov].append(r)
            continue

        i = index

        success = False
        while i < len(images):
            # searches forwards for match
            if scene_tag_match(scene_tag, tags[i]):
                images[i][mov].append(r)
                index = i + 1
                prevTag = scene_tag
                success = True
                break
            else:
                i+=1
        
        if not success:
            # tries searching backwards instead if forward fails
            i = index

            while i>=0:
                if scene_tag_match(scene_tag, tags[i]):
                    images[i][mov].append(r)
                    prevTag = scene_tag
                    success = True
                    break
                else:
                    i-=1
            
            if not success: # attaches to overflow, not expected to occur
                images[len(images)-1][mov].append(r)

for pathin in args.input:
    for infile in glob.iglob(pathin):

        # Iterate again
        if path.isdir(infile):
            infile = os.path.join(infile, "*_regions.json")
            for f in glob.iglob(infile):
                process(f)
        else:
            process( infile )

maximum = 0
for tag in images:
    for mov,regions in tag.items():
        maximum = max(maximum,len(regions))

img_path  = path.dirname(args.outfile) + "/images/"
os.makedirs(img_path, exist_ok=True)

urls = sorted(urls)

base, ext = path.splitext(args.outfile)

for i in range(0,maximum):
    html_file = base + str(i) + ext

    logging.info("Saving to %s" % html_file)

    with open(html_file, 'w') as html:
        html.write("<html><body>\n")
        html.write("<h2>Proof sheet</h2>\n\n")

        html.write("<table>\n<tr><th>Scene Tag</th>")
        for name in urls:
            if name in gt_urls:
                html.write("<th>GROUND TRUTH<br>%s</th>" % _format_url(name))
            else:
                html.write("<th>%s</th>" % _format_url(name))


        html.write("</tr>\n")
        #><th>Reference image from class</th>\n")

        for row in range(len(images)):
            html.write("<tr>")
            html.write("<td>%s</td>" % (tags[row]) )

            for url in urls:
                if url not in images[row]:
                    html.write("<td></td>")
                    continue

                regions = images[row][url]

                if len(regions)<=i:
                    html.write("<td></td>")
                    continue
                    
                if len(regions) < 1:
                    html.write("<td></td>")
                    continue

                region = regions[i]

                sample_frame = region.frame_at(0.5)

                img_file = img_path + "%s_%d.%s" % (path.splitext(path.basename(url))[0], sample_frame, args.imageext)
                thumb_file = img_path + "%s_%d_thumbnail.%s" % (path.splitext(path.basename(url))[0], sample_frame, args.imageext)

                if args.force or not path.exists( img_file ) or not path.exists( thumb_file ):
                    logging.info("Fetching frame %d from %s for contact sheet" % (sample_frame, path.basename(url)))
                    img = qt.get_frame(url, sample_frame, format=args.imageext,
                                    width=IMAGE_RESOLUTION[0], height=IMAGE_RESOLUTION[1])
                    img.save( img_file )
                    img.thumbnail( img_size )  # PIL.thumbnail preserves aspect ratio

                    img.save( thumb_file )

                relapath = path.relpath( img_file, path.dirname(html_file) )
                relathumb = path.relpath( thumb_file, path.dirname(html_file) )

                caption = "%d -- %d" % (region.start_frame,region.end_frame)
                caption = "%s (%s | %s)" % (caption, _format_url(url).split('|')[1].strip(), tags[row])
                html.write("<td><a href=\"%s\"><img src=\"%s\"/></a><br>%s</td>" % (relapath,relathumb,caption) )


            html.write("</tr>")

        if i==0:

            html.write("<tr><th>Scene Tag</th>")
            for name in urls:
                html.write("<th>%s</th>" % _format_url(name))
            html.write("</tr>\n")

            html.write("<tr>")
            html.write("<td>Unknown</td>" )

            logging.info("Processing unknowns")

            for url in urls:
                if url not in unknowns:
                    html.write("<td></td>")
                    continue

                html.write("<td>")
                for region in unknowns[url]:

                    sample_frame = region.start_frame + 0.5 * (region.end_frame - region.start_frame)

                    img_file = img_path + "%s_%d.%s" % (path.splitext(path.basename(url))[0], sample_frame, args.imageext)
                    thumb_file = img_path + "%s_%d_thumbnail.%s" % (path.splitext(path.basename(url))[0], sample_frame, args.imageext)

                    if args.force or not path.exists( img_file ) or not path.exists( thumb_file ):
                        logging.info("Fetching frame %d from %s for contact sheet" % (sample_frame, path.basename(url)))
                        img = qt.get_frame(url, sample_frame, format='jpg',
                                        width=IMAGE_RESOLUTION[0], height=IMAGE_RESOLUTION[1])
                        img.save( img_file )
                        img.thumbnail( img_size )  # PIL.thumbnail preserves aspect ratio

                        img.save( thumb_file )

                    relapath = path.relpath( img_file, path.dirname(html_file) )
                    relathumb = path.relpath( thumb_file, path.dirname(html_file) )

                    caption = "%d -- %d" % (region.start_frame, region.end_frame)
                    caption = "%s (%s | %s)" % (caption, _format_url(url).split('|')[1].strip(), "unknown")
                    html.write("<a href=\"%s\"><img src=\"%s\"/></a><br>%s<br>" % (relapath, relathumb, caption))
                html.write("</td>")


            html.write("</tr>")

            html.write("</table>")
            html.write("</body></html>")
