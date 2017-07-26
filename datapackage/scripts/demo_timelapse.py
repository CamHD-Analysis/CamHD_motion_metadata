
import argparse
import logging
import os
import datapackage
import math

import pycamhd.lazycache as camhd

parser = argparse.ArgumentParser(description='Generate HTML proofs')

parser.add_argument('--scene-tag', metavar='scene_tag', nargs='?',
                    help='Scene tag to extract')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--output', dest='outdir', nargs='?', default='_timelapse/', help='Directory for timelapse images')

parser.add_argument('--image-size', dest='imgsize', nargs='?', default=None)

parser.add_argument('--lazycache-url', dest='lazycache', default=os.environ.get("LAZYCACHE_URL", "http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files"),
                    help='URL to Lazycache repo server (only needed if classifying)')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )

if not args.scene_tag:
    logging.fatal("Scene tag must be specified with --scene-tag")
    exit(-1)

qt = camhd.lazycache( args.lazycache )

img_size = None
if args.imgsize:
    img_size = args.imgsize.split('x')
    img_size = (int(img_size[0]), int(img_size[1]))


url = "https://raw.githubusercontent.com/CamHD-Analysis/CamHD_motion_metadata/master/datapackage/datapackage.json"

dp = datapackage.DataPackage(url)

regions = dp.resources[0]

mov = {}
count = 0

for r in regions.iter():
    if r['scene_tag'] == args.scene_tag:
        basename = r['mov_basename']

        if basename not in mov:
            mov[basename] = []

        mov[basename].append(r)

keys = sorted( mov.keys() )

for basename in keys:
    print(basename)

    r = mov[basename]

    # Select which region
    region = r[math.floor(len(r)/2)] if len(r) > 1 else r[0]

    logging.info("Using regions from frames %d to %d" % (region['start_frame'], region['end_frame']))

    # Select the precise frame to retrieve
    frame = math.floor( region['end_frame'] - region['start_frame']/2.0 )

    logging.info("Retrieving frame %d" % frame)
    img = qt.get_frame( camhd.convert_basename(basename), frame, format='png', timeout=30 )

    if img_size:
        img.thumbnail( img_size )

    # Make filename
    filename = "%s/%08d_%s_%06d.png" % (args.outdir, count, basename, frame)

    logging.info("Saving to %s" % filename)
    img.save( filename )

    count += 1




logging.info("Run \"ffmpeg -framerate 10 -pattern_type glob -i '%s/*.png' -c:v libx264 -pix_fmt yuv420p out.mp4\"" % args.outdir)
