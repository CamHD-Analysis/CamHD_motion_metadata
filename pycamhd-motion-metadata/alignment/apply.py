"""
Part 3 of 3 of auto.py, manual.py, and apply.py
Applies transformations specified in the metadata and creates corresponding aligned videos.
"""

import time, argparse, logging
import glob, os, traceback
import cv2, numpy as np
import warp, helper, reference

"""
Takes the filepath of the original video and creates an aligned one.
"""
def align_frames(input_video):
    start = time.time()

    logging.info("Applying transformations for video {}.".format(input_video))

    data_file = helper.data_file(input_video)
    output_video = helper.output_file(input_video)

    metadata = helper.read_data(data_file)
    assert metadata['filepath'] == input_video, "Video filepath ({}) does not match that noted in metadata ({}).".format(input_video, metadata['filepath'])
    reader = cv2.VideoCapture(input_video)
    assert reader.isOpened(), "Reader could not be opened."
    
    logging.info("Opened video {}.".format(input_video))
    fps = reader.get(cv2.CAP_PROP_FPS)
    width = int(reader.get(3))
    height = int(reader.get(4))

    # assert metadata['fps'] == fps, "Video fps ({}) does not match that noted in metadata ({}).".format(fps, metadata['fps'])
    # assert metadata['width'] == width, "Video width ({}) does not match that noted in metadata ({}).".format(width, metadata['width'])
    # assert metadata['height'] == height, "Video height ({}) does not match that noted in metadata ({}).".format(height, metadata['height'])
    # assert metadata['frame_count'] == length, 'Number of frames ({}) does not match that noted in metadata ({}).'.format(length, metadata['frame_count'])

    writer = cv2.VideoWriter(output_video,cv2.VideoWriter_fourcc(*args.fourcc), fps, (width, height), True)
    assert writer.isOpened(), "Writer could not be opened."

    logging.info("Opened writer to {}.".format(output_video))

    for frame_data in metadata['frames']:
        if not frame_data['success']:
            logging.warning("Frame {} of video {} was not successfully aligned.".format(frame_data['frame_num'], input_video))
        
        abs_matrix = np.matmul(metadata['global']['abs_matrix'], frame_data['abs_matrix'])
        
        grabbed, frame = reader.read()
        assert grabbed, "Length of video is shorter than length of video metadata."

        aligned = warp.apply_warp(frame, abs_matrix)
        writer.write(aligned)

    
    grabbed, frame = reader.read()
    assert not grabbed, "Length of video is longer than length of video metadata."

    reader.release()
    writer.release()

    logging.info("Finished with video file {}.".format(input_video))

    end = time.time()
    # assert frame_count == frame_num, 'Number of frames expected ({}) does not equal number of frames processed ({}).'.format(frame_count, frame_num)

    logging.info("Time taken: {}.".format(end-start))

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", nargs="+", required = True, help ="input files, glob matching supported")
ap.add_argument("-f", "--fourcc", default = 'MJPG', help = "fourcc code")
ap.add_argument("-l", "--log", default = "DEBUG", help ="logging level, debug recommended")

args = ap.parse_args()
logging.basicConfig(format = "%(asctime)s\t%(levelname)s\t%(message)s", level = args.log.upper(), datefmt = "%H:%M:%S")

video_names = helper.glob_unpack(args.input)

logging.info("Fourcc code: {}.".format(args.fourcc))

for input_video in video_names:
    try:
        align_frames(input_video)
    except Exception as e:
        logging.error("An error occured on video {}.".format(input_video))
        logging.error(e)
        logging.error(traceback.format_exc())