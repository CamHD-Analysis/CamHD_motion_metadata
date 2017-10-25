#
# This is a very simple script showing timelapse generation using the
# lazycache and the regions.csv datapackage.   It has limited features.
# For full featured version, see scripts/timelapse.py
#

import os
import datapackage

import pycamhd.lazycache as camhd

DATAPACKAGE = "https://raw.githubusercontent.com/CamHD-Analysis/CamHD_motion_metadata/master/datapackage/datapackage.json"

scene_tag = 'd2_p1_z0'
outdir = "_timelapse"


## Use package-default Lazycache instance
qt = camhd.lazycache()

os.makedirs(outdir, exist_ok=True)

dp = datapackage.DataPackage(DATAPACKAGE)
regions = dp.resources[0]

mov = {}

for r in regions.iter():
    if r['scene_tag'] == scene_tag:
        # Just take the last relevant region in each movie
        mov[r['mov_basename']] = r

for basename in sorted(mov.keys()):
    region = mov[basename]

    print("In movie %s, using region from frames %d to %d " %
          (basename, region['start_frame'], region['end_frame']))

    frame = int((region['end_frame'] + region['start_frame'])/2)
    filename = "%s/%s_%06d.png" % (outdir, basename, frame)

    print("       Retrieving frame %d, saving to %s" % (frame, filename))
    img = qt.get_frame(camhd.convert_basename(basename), frame, format='png',
                       timeout=30)
    img.save(filename)
