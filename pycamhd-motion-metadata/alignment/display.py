"""
Displays frames from multiple images in a window.
Designed for use by manual.py
"""

import time, argparse, logging
import glob, os, traceback
import cv2, numpy as np

"""
Displays frames from multiple videos in a window.
Has a video and frame trackbar for navigation.
"""
class Display:
    def __init__(self, packs, name, func, readsource = 'original'):
        self.packs = packs
        self.window_name = name
        self.readsource = readsource
        self.func = func # Used to update the test image in manual.py to .
        self.start()
    
    """
    Manipulates the feature points.
    The more feature points, the more accurate manual alignment will be. 
    """
    def click(self, event, x, y, flags, param): 
        if event == cv2.EVENT_LBUTTONDBLCLK:
            pt = (x,y)
            logging.info("Click number {} at {} in window {}.".format(len(self.points), pt, self.window_name))
            self.points.append(pt)
        elif event == cv2.EVENT_MBUTTONDBLCLK:
            logging.info("Cleared all points in window {}.".format(self.window_name))
            self.points.clear()
        elif event == cv2.EVENT_MBUTTONDOWN:
            try:
                assert len(self.points)>0, "No selected points."
                logging.info("Undid click number {} in window {}.".format(len(self.points)-1, self.window_name))
                self.points.pop()
            except AssertionError as e:
                logging.info("No selected points.")
                logging.debug(e)
                logging.debug(traceback.format_exc())
            except Exception as e:
                logging.warning("Unable to delete previous point.")
                logging.debug(e)
                logging.debug(traceback.format_exc())

    """
    Used to initialize the window.
    """
    def start(self):
        self.points = []
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.click)
        self.video_count = len(self.packs)
        cv2.createTrackbar('video', self.window_name, 0, self.video_count-1, self.update_video)
        self.frame_count = max(self.packs[i]['metadata']['frame_count'] for i in range(len(self.packs)))
        cv2.createTrackbar('frame', self.window_name, 0, self.frame_count-1, self.update_frame)
        self.update_video(0)

    """
    Updates the video that is selected.
    """
    def update_video(self, video_num, frame_num = 0):
        self.vid_pack = self.packs[video_num]
        logging.info("Selected video {}, index {}, with {} frames, in window {}.".format(
            self.vid_pack['metadata']['filepath'], video_num, self.vid_pack['metadata']['frame_count'], self.window_name))
        self.update_frame(frame_num)
        cv2.setTrackbarPos('video', self.window_name, video_num)
        cv2.setTrackbarPos('frame', self.window_name, frame_num)

    """
    Updates the frame that is selected.
    """
    def update_frame(self, frame_num):
        try:
            reader = self.vid_pack[self.readsource]
            assert reader.isOpened()
            reader.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            grabbed, frame = reader.read()
            assert grabbed
            self.frame_pack = {'index':frame_num, 'frame': frame, 'metadata': self.vid_pack['metadata']['frames'][frame_num]}
            self.points = []
            self.func()
            self.display()
            logging.debug("Selected frame {} of video {} in window {}".format(frame_num, self.vid_pack['index'], self.window_name))
        except Exception as e:
            logging.warning("Unable to retrieve frame {} from video {}.".format(
                frame_num, self.vid_pack['metadata']['filepath']))
            logging.debug(e)
            logging.debug(traceback.format_exc())
            self.frame_pack = None

    """
    Displays the frame currently selected, with marks at selected feature points.
    """
    def display(self):
        try:
            assert self.frame_pack is not None
            self.copy = self.frame_pack['frame'].copy()
            for pt in self.points:
                cv2.circle(self.copy,pt,3,(0,0,255),-1)
            cv2.imshow(self.window_name, self.copy)
        except Exception as e:
            logging.warning("Unable to display frame from video {}.".format(self.vid_pack['metadata']['filepath']))
            logging.debug(e)
            logging.debug(traceback.format_exc())

    """
    Selects a specific frame from a specific video.
    """
    def goto(self, indices):
        self.update_video(indices[0],indices[1])
