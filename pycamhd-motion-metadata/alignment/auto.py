"""
Part 1 of 3 of auto.py, manual.py, and apply.py
Generates all metadata and initial alignments.
"""

import time, argparse, logging
import glob, os, traceback
import cv2, numpy as np
import warp, helper, reference

"""
Takes a filepath for a video and calculates homography matricies.
Stores all metadata in a .json file.
The global matrix for each video is set to the identity matrix, as users are expected to manually align between images.
"""
def calculate_matrix(input_video):
    logging.info("Calculating transformation matrices for video {}.".format(input_video))
    start = time.time()

    reader = cv2.VideoCapture(input_video)
    assert reader.isOpened(), "Reader could not be opened."
    
    logging.info("Opened video {}.".format(input_video))
    fps = reader.get(cv2.CAP_PROP_FPS)
    width = int(reader.get(3))
    height = int(reader.get(4))

    frame_num = 0
    average = np.zeros((3,3), np.float32)
    refer = reference.BinaryReference()

    metadata = {}
    metadata['filepath'] = input_video
    metadata['fps'] = fps
    metadata['width'] = width
    metadata['height'] = height
    metadata['similarity_threshold'] = args.threshold
    metadata['global_matrix'] = np.eye(3,3,dtype = np.float32)
    metadata['failed'] = set()

    video_length = int(reader.get(cv2.CAP_PROP_FRAME_COUNT))
    metadata['frame_count'] = video_length

    logging.info("{} frames detected.".format(video_length))

    metadata['frames'] = []

    while True:
        grabbed, frame = reader.read()
        if not grabbed:
            break

        success = False

        while True: # Keeps attempting alignments until successful or until it runs out
            data = refer.get()
            if data is None:
                break
            
            logging.debug("Attempting to align frame {}, refer counter {}, with refer to {}.".format(
                frame_num, refer.counter, refer.ref))
            ref, ref_matrix = data
            similarity = 0.0

            try: 
                rel_matrix, similarity = warp.find_matrix(ref, frame)
                assert similarity>args.threshold, "Similarity must meet specified threshold."
            except Exception as e: # May happen if two images are so dissimilar the algorithm fails to converge.
                logging.debug(e)
                logging.debug(traceback.format_exc())
                logging.debug("Alignment failed with similarity {}.".format(similarity))
                continue
            else:
                success = True
                break
        
        if success:
            logging.debug("Aligned with similarity {}.".format(similarity))
        else: # Frames that fail to align with themselves are listed as referencing themselves in the metadata.
            rel_matrix = np.eye(3,3,dtype = np.float32)
            ref_matrix = np.eye(3,3,dtype = np.float32)
            similarity = 0
            metadata['failed'].add(frame_num)
            logging.warning("Could not align frame {} of video {} to reference image.".format(frame_num, input_video))
        
        abs_matrix = np.matmul(ref_matrix, rel_matrix)
        results = {'frame_num' : frame_num, 'success' : success, "similarity" : similarity, 'refer_to' : refer.ref,  
            'rel_matrix' : rel_matrix, 'abs_matrix': abs_matrix, 'refer_by': set()}
            
        metadata['frames'].append(results)
        metadata['frames'][refer.ref]['refer_by'].add(frame_num)

        refer.save((frame, abs_matrix))
        
        logging.debug("Relative matrix: \n"+str(rel_matrix))
        logging.debug("Absolute matrix: \n"+str(abs_matrix))
        logging.info("Finished frame {}.".format(frame_num))
        frame_num += 1
        average += abs_matrix 

    reader.release()

    logging.info("Finished finding transformations for video file {}.".format(input_video))

    average /= frame_num
    logging.info("Average transformation matrix:\n"+str(average))
    
    metadata['average_matrix'] = average
    
    data_file = helper.data_file(input_video)

    helper.write_data(data_file, metadata)
    logging.info("Successfully wrote metadata to {}.".format(data_file))

    # assert frame_count == frame_num, 'Number of frames expected ({}) does not equal number of frames processed ({}).'.format(frame_count, frame_num)

    end = time.time()
    logging.info("Time taken: {}.".format(end-start))

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", nargs="+", required = True, help ="input files, glob matching supported")
ap.add_argument("-t", "--threshold", type = float, default = 0.5, help = "structural similarity index threshold dropping frames")
ap.add_argument("-l", "--log", default = "DEBUG", help ="logging level")

args = ap.parse_args()
logging.basicConfig(format = "%(asctime)s\t%(levelname)s\t%(message)s", level = args.log.upper(), datefmt = "%H:%M:%S")

video_names = helper.glob_unpack(args.input)
            
logging.info("Similarity threshold: {}.".format(args.threshold))

for input_video in video_names:
    try:
        calculate_matrix(input_video)
    except Exception as e:
        logging.error("An error occured on video {}.".format(input_video))
        logging.error(e)
        logging.error(traceback.format_exc())