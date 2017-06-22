

import logging
import skimage.data as skd
import skimage.feature as skf
import skimage.transform as skt
import skimage.color
import imreg_dft as ird
import random


def classify_regions( regionsj, classification, lazycache ):

    mov = regionsj["movie"]["URL"]

    for r in regionsj["regions"][:1]:
        logging.info(r["type"] )
        if r["type"] != "static":
            continue

        logging.info("Attempting to classify region from %d to %d" %(r["startFrame"], r["endFrame"]) )


        # Identify sample image within region
        sample = round(r["startFrame"] + r["endFrame"] / 2)

        ref_img = lazycache.get_frame( mov, sample )
        ref_img = skimage.color.rgb2gray(skt.rescale(ref_img, 0.25, mode='constant' ))

        rms = {}

        for c in sorted(classification.keys()):
            ## Choose an arbitrary image for now
            logging.info("Checking class %s" % c)
            test_img_path = random.choice( classification[c] )
            test_img = skd.load( test_img_path )
            test_img = skimage.color.rgb2gray(skt.rescale(test_img, 0.25, mode='constant' ))

            logging.info("Comparing to class %s test image %s" % (c, test_img_path) )


            #shifts,error,phasediff = skf.register_translation( test_img, ref_img )
            # logging.info("Relative to class %s, RMS error = %f, shifts = %f,%f" % (c, error, shifts[0], shifts[1]))
            #
            # ## Heuristic test to invalidate large shifts
            # if abs(shifts[0]) > 30 or abs(shifts[1]) > 30:
            #     logging.info("Large shift, discarding")
            #     continue

            # Odds = 0 : never consider image rotated by 180
            result = ird.translation(test_img, ref_img, odds=0)

            print(result)


            #ms[c] = 0.0

        print(rms)

    return regionsj
