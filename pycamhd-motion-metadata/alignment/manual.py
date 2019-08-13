"""
Part 2 of 3 of auto.py, manual.py, and apply.py
Allows the user to make manual changes to alignment metadata.
"""

import time, argparse, logging
import glob, os, traceback
import cv2, numpy as np, queue
import warp, helper, reference, display

"""
Applies a manual transformation between two frames. 
Has different actions depending on if the frames are in the same video.
"""
def warp_update(ref_pack, align_pack, rel_matrix):
    ref_vid_pack = ref_pack[0]
    align_vid_pack = align_pack[0]

    if ref_vid_pack == align_vid_pack:
        warp_frames(ref_pack, align_pack, rel_matrix)
    else:
        warp_videos(ref_pack, align_pack, rel_matrix)

"""
Aligns a frame to another within a particular video, and recursively updates affected frames.
"""
def warp_frames(ref_pack, align_pack, rel_matrix):
    assert ref_pack[0] == align_pack[0], "Videos {} and {} are not the same.".format(ref_pack[0], align_pack[0])
    vid_pack = ref_pack[0]
    ref_frame_pack = ref_pack[1]
    align_frame_pack = align_pack[1]

    logging.info("Warping frame {} to frame {} in video {}.".format(align_frame_pack['index'],ref_frame_pack['index'], vid_pack['index']))

    frames = vid_pack['metadata']['frames']
    ref_num = ref_frame_pack['index']
    align_num = align_frame_pack['index']

    helper.rereference(frames, ref_num, align_num)

    frames[align_num]['rel_matrix'] = rel_matrix
    helper.set_success(vid_pack, align_frame_pack, True)

    next_num = frames[ref_num]['refer_to']
    chained = {align_num, ref_num}
    sever_ties = True
    while next_num not in chained: # Checks if a loop of references would be created.
        if next_num == frames[next_num]['refer_to']:
            sever_ties = False
            break
        next_num = frames[next_num]['refer_to']

    if sever_ties: # If a loop is found, severs it.
        frames[ref_num]['rel_matrix'] = np.eye(3,3,dtype = np.float32)
        helper.rereference(frames, ref_num, ref_num)

    todo = queue.LifoQueue()
    visited = set()

    todo.put(align_num)
    visited.add(ref_num)

    while not todo.empty(): # Recursively updates the relevant frames
        num = todo.get()
        print(num)
        if not num in visited:
            visited.add(num)
            pointer = frames[num]['refer_to']
            frames[num]['abs_matrix'] = np.matmul(frames[pointer]['abs_matrix'], frames[num]['rel_matrix'])
            for x in frames[num]['refer_by']:
                todo.put(x)
        else:
            logging.warning("Chain detected with frame num {}.".format(num))
    helper.update_average(align_pack[0])
    helper.save(ref_pack[0])

"""
Aligns video to another via specific frames in each. 
Only changes the global matrix for the aligned video.
"""
def warp_videos(ref_pack, align_pack, rel_matrix):
    logging.info("Warping video {} to video {}.".format(align_pack[0]['index'], ref_pack[0]['index']))
    ref_vid_meta = ref_pack[0]['metadata']
    align_vid_meta = align_pack[0]['metadata']
    ref_frame_meta = ref_pack[1]['metadata']
    align_frame_meta = align_pack[1]['metadata']

    align_vid_meta['global_matrix'] = np.matmul(np.matmul(ref_vid_meta['global_matrix'], ref_frame_meta['abs_matrix']), 
                                            np.matmul(rel_matrix, np.linalg.inv(align_frame_meta['abs_matrix'])))##TODO
    helper.update_average(align_pack[0])
    helper.save(align_pack[0])

align_display = None
ref_display = None
matrix = np.eye(3,3,dtype = np.float32)
test_image = None

"""
Finds the relative transformation between two given frames. 
"""
def find_rel_matrix():
    global matrix
    if align_display is not None and ref_display is not None:
        matrix = np.matmul(np.matmul(np.linalg.inv(ref_display.frame_pack['metadata']['abs_matrix']), 
            np.linalg.inv(ref_display.vid_pack['metadata']['global_matrix'])),
            np.matmul(align_display.vid_pack['metadata']['global_matrix'], 
            align_display.frame_pack['metadata']['abs_matrix']))
        logging.debug("Found relative matrix.")
        reset_test_image()
    else:
        logging.warning("Displays may not have been initialized yet.")

"""
Sets the test image to the current frame in the align display and applies a transformation.
"""
def reset_test_image():
    global test_image
    global matrix
    test_image = warp.apply_warp(align_display.frame_pack['frame'], matrix)
    logging.debug("Applied warp to test image.")
    cv2.imshow("test",test_image)

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", nargs="+", required = True, help ="input files, glob matching supported")
ap.add_argument("-l", "--log", default = "DEBUG", help ="logging level")

args = ap.parse_args()
logging.basicConfig(format = "%(asctime)s\t%(levelname)s\t%(message)s", level = args.log.upper(), datefmt = "%H:%M:%S")

video_names = helper.glob_unpack(args.input)
packs = helper.vid_unpack(video_names)

align_display = display.Display(packs, 'align', find_rel_matrix)
ref_display = display.Display(packs, 'ref', find_rel_matrix)

test_image = align_display.frame_pack['frame']
cv2.imshow("test",test_image)

todo_gen = helper.todo(packs) # Finds the next frame labeled as unsuccessful in the metadata.

while True:
    ref_display.display()
    align_display.display()

    k = cv2.waitKey(100) & 0xFF

    if k == 255 or k == 233: # Ignores the Alt key and no keypress scenarios.
        continue

    if k == 27: # Escape key.
        cv2.destroyAllWindows()
        break

    if k == ord('h'): # The test image will display what the aligned frame will look like relative to the reference frame.
        try:
            logging.info("Finding and applying transformation.")
            assert align_display.frame_pack is not None and ref_display.frame_pack is not None, "Using invalid frames."
            matrix, mask = cv2.findHomography(np.array(ref_display.points), np.array(align_display.points))
            logging.info("Calculated matrix:\n"+str(matrix))
            reset_test_image() 
        except AssertionError as e: # May happen if videos are not the same length.
            logging.warning("Invalid video/frame selected.")
            logging.debug(e)
            logging.debug(traceback.format_exc())
        except Exception as e:
            logging.error("An error occured calculating and displaying manual alignment.")
            logging.error(e)
            logging.error(traceback.format_exc())
    elif k == ord('g'):
        try:
            logging.info("Atempting to apply transformations to metadata.")
            warp_update((ref_display.vid_pack, ref_display.frame_pack), \
                (align_display.vid_pack, align_display.frame_pack), matrix)
        except Exception as e:
            logging.error("An error occured saving transformations.")
            logging.error(e)
            logging.error(traceback.format_exc())
    elif k == ord('j'):
        try:
            find_rel_matrix()
            logging.info("Matrix reset.")
        except Exception as e:
            logging.error("An error occured calculating and displaying relative alignment.")
            logging.error(e)
            logging.error(traceback.format_exc())

    if k == ord('p'):
        try:
            logging.info("Resetting global matrix for video.")
            helper.reset_global_matrix(align_display.vid_pack) 
        except Exception as e:
            logging.error("An error occured resetting global matrix.")
            logging.error(e)
            logging.error(traceback.format_exc())
    elif k == ord('o'):
        try:
            logging.info("Resetting frame to default.")
            helper.reset_frame_matrix(align_display.vid_pack, align_display.frame_pack)
        except Exception as e:
            logging.error("An error occured resetting frame to default.")
            logging.error(e)
            logging.error(traceback.format_exc())
    elif k == ord('i'):
        try:
            logging.info("Clearing frame references.")
            helper.clear_frame_reference(align_display.vid_pack, align_display.frame_pack)
        except Exception as e:
            logging.error("An error occured clearing frame references.")
            logging.error(e)
            logging.error(traceback.format_exc())

    if k == ord('t'):
        try:
            logging.info("Cycling to next failed frame.")
            align_display.goto(next(todo_gen))
        except StopIteration as e:
            logging.warning("No more frames in generator, press r to reset.")
            logging.debug(e)
            logging.debug(traceback.format_exc())
        except Exception as e:
            logging.error("An error occured cycling through failed frames.")
            logging.error(e)
            logging.error(traceback.format_exc())
    elif k == ord('r'):
        try:
            logging.info("Resetting the generator cycling through failed frames.")
            todo_gen = helper.todo(packs)
        except Exception as e:
            logging.error("An error occured resetting the generator.")
            logging.error(e)
            logging.error(traceback.format_exc())

    if k == ord('d'): # Displays relevant referencing and success metadata.
        try:
            assert align_display.frame_pack is not None
            logging.info("Frame success is {}.".format(align_display.frame_pack['metadata']['success']))
            logging.info("Refers to {}.".format(align_display.frame_pack['metadata']['refer_to']))
            logging.info("Referred by {}.".format(str(align_display.frame_pack['metadata']['refer_by'])))
        except Exception as e:
            logging.error("An error occured logging frame success metadata.")
            logging.error(e)
            logging.error(traceback.format_exc())
    elif k == ord('s'):
        try:
            logging.info("Attempting to label frame as successful.")
            helper.set_success(align_display.vid_pack, align_display.frame_pack, True)
            helper.save(align_display.vid_pack)
        except Exception as e:
            logging.error("An error occured labeling frame as successful.")
            logging.error(e)
            logging.error(traceback.format_exc())
    elif k == ord('f'):
        try:
            logging.info("Attempting to label frame as failed.")
            helper.set_success(align_display.vid_pack, align_display.frame_pack, False)
            helper.save(align_display.vid_pack)
        except Exception as e:
            logging.error("An error occured labeling frame as failed.")
            logging.error(e)
            logging.error(traceback.format_exc())

    if k == ord('x'): 
        try:
            logging.info("Global matrix for video: \n"+str(align_display.vid_pack['metadata']['global_matrix']))##TODO
        except Exception as e:
            logging.error("An error logging global matrix.")
            logging.error(e)
            logging.error(traceback.format_exc())
    elif k == ord('c'):
        try:
            logging.info("Relative matrix for frame: \n" +str(align_display.frame_pack['metadata']['rel_matrix']))
            logging.info("Absolute matrix for frame: \n" +str(align_display.frame_pack['metadata']['abs_matrix']))
        except Exception as e:
            logging.error("An error occured logging frame matrices.")
            logging.error(e)
            logging.error(traceback.format_exc())