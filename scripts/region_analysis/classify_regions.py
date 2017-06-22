

import logging
import skimage.data as skd
import skimage.feature as skf
import skimage.transform as skt
import skimage.color
import skimage.io
import imreg_dft as ird
import random

from dask import compute, delayed
import dask.threaded

from operator import attrgetter

class CompareResult:

    def __init__(self, tag, score ):
        self.tag = tag
        self.score = score



def compare_images( ref_img, classification, tag ):
    ## Choose an arbitrary image for now
    logging.info("Checking class %s" % tag)
    test_img_path = random.choice( classification[tag] )
    test_img = skd.load( test_img_path )
    test_img = skimage.color.rgb2gray(skt.rescale(test_img, 0.25, mode='constant' ))

    skimage.io.imsave( "/tmp/region_analysis/%s.png" % tag, test_img )

    logging.info("Comparing to class %s test image %s" % (tag, test_img_path) )

    #shifts,error,phasediff = skf.register_translation( test_img, ref_img )
    # logging.info("Relative to class %s, RMS error = %f, shifts = %f,%f" % (c, error, shifts[0], shifts[1]))
    #
    # ## Heuristic test to invalidate large shifts
    # if abs(shifts[0]) > 30 or abs(shifts[1]) > 30:
    #     logging.info("Large shift, discarding")
    #     continue

    # Odds = 0 : never consider image rotated by 180
    result = ird.translation(test_img, ref_img, odds=0)

    #logging.info(result)

    return CompareResult( tag, result['success'] )


def classify_regions( regionsj, classification, lazycache, first_n = None ):

    mov = regionsj["movie"]["URL"]

    regions = regionsj["regions"]
    if first_n:
        regions = regions[:first_n]

    for rj in regions:
        logging.info(rj["type"] )
        if rj["type"] != "static":
            continue

        # Identify sample image within region
        sample = round( (rj["startFrame"] + rj["endFrame"]) * 0.5 )

        logging.info("Attempting to classify region from %d to %d" %(rj["startFrame"], rj["endFrame"]) )
        logging.info("Using test frame %d" % sample)

        ref_img = lazycache.get_frame( mov, sample )
        ref_img = skimage.color.rgb2gray(skt.rescale(ref_img, 0.25, mode='constant' ))

        skimage.io.imsave( "/tmp/region_analysis/ref.png", ref_img )

        ## Parallelize in dask
        values = [delayed( compare_images )(ref_img, classification, tag) for tag in classification.keys() ]
        results = compute( *values, get=dask.threaded.get )

        def sort_key( result ):
            return float()

        results = sorted( results, key=attrgetter('score') )

        for r in results:
            logging.info("%s : %f" % (r.tag, r.score))

        ## Heuristic tests?
        test_ratio = 2

        scene_tag = 'unknown'
        scene_tag_guesses = {}

        ## Keep top n
        for r in results:
            if r.score > 0.1:
                scene_tag_guesses[ r.tag ] = r.score

        first = results[-1]
        second = results[-2]

        ## Use simple ratio test
        ratio = first.score / second.score
        logging.info("1st/2nd best scores: %f, %f    : ratio = %f" % (first.score, second.score, ratio))
        if ratio > test_ratio:
            scene_tag = first.tag

        rj['sceneTag'] = [scene_tag]
        rj['sceneTagScore'] = scene_tag_guesses

        # for c in sorted( rms, key=rms.get ):
        #     logging.info( " %s    : %f" % (c, rms[c]) )

    return regionsj
