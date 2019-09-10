"""
Miscellaneous functions.
"""

import time, argparse, logging
import cv2, numpy as np
import glob, os, traceback
from skimage.measure import compare_ssim
import json_tricks

num = 0

def display(img, name = None, scale = 1):
    global num
    if name is None:
        name = str(num)
        num+=1
    img = resize_scale(img,scale)
    cv2.imshow(name,img)

def pause():
    k = cv2.waitKey(0)
    if k == 27: 
        cv2.destroyAllWindows()

def resize_dim(img, dim):
    resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    return resized

def resize_scale(img, scale = 1):
    width = int(img.shape[1] * scale)
    height = int(img.shape[0] * scale)
    dim = (width, height)
    resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    return resized

def gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
def eqHist(img):
    return cv2.equalizeHist(img)

def CLAHE(img, clipLimit = 40, tileGridSize = (8,8)):
    clahe = cv2.createCLAHE(clipLimit, tileGridSize)
    return clahe.apply(img)

def GaussBlur(img):
    return cv2.GaussianBlur(img,(5,5),0)
    
def medBlur(img):
    return cv2.medianBlur(img, 5)

def lap(img):
    return cv2.Laplacian(img, ddepth=cv2.CV_32F,ksize=5)

def Canny(img):
    return cv2.Canny(img, 500, 1000, apertureSize=5)

def binary(img):
    return cv2.threshold(img,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]

def tozero(img):
    return cv2.threshold(img,0,255,cv2.THRESH_TOZERO+cv2.THRESH_OTSU)[1]

def scale_matrix(matrix, scale):# Displays 
    matrix[0][2]*=scale
    matrix[1][2]*=scale
    matrix[2][0]/=scale
    matrix[2][1]/=scale
    return matrix

def one(matrix):
    return matrix/matrix[2][2]

def similar(img1, img2, multichannel = True):
    ma1 = np.ma.masked_equal(img1,0)
    ma2 = np.ma.masked_equal(img2,0)

    score = compare_ssim(ma1, ma2, gaussian_weights = True, multichannel = multichannel)

    return np.mean(score)

def read_data(filename):
    with open(filename) as readfile:
        data = json_tricks.load(readfile)
    return data

def write_data(filename, data, method = 'w'):
    with open(filename, method) as writefile:
        json_tricks.dump(data, writefile, indent = 4, sort_keys = True)

def data_file(video):
    root, ext = os.path.splitext(video)
    data_file = root + matrix_suffix + json_extension
    return data_file

def output_file(video):
    root, ext = os.path.splitext(video)
    output_video = root + aligned_suffix + ext
    return output_video

matrix_suffix = "_matrix"
aligned_suffix = "_aligned"
json_extension = ".json"

def glob_unpack(input_paths):
    files = []
    for path in input_paths:
        for filename in glob.iglob(path):
            if os.path.isfile(filename):
                root, ext = os.path.splitext(filename)
                if root.endswith(aligned_suffix):
                    continue

                files.append(filename)
                logging.info("Found file {0}.".format(filename))
    return files

def vid_unpack(videos):
    info = []
    for vid_num, video_name in enumerate(videos):
        data_filename = data_file(video_name)
        metadata = read_data(data_filename)
        original = cv2.VideoCapture(video_name)
        aligned = cv2.VideoCapture(output_file(video_name))
        info.append({'index':vid_num, 'original':original, 'aligned':aligned, 'metadata':metadata})
    return info

def update_average(vid_pack):
    average = sum(vid_pack['metadata']['frames'][i]['abs_matrix'] for i in range(vid_pack['metadata']['frame_count']))/vid_pack['metadata']['frame_count']
    return average

def save(vid_pack):
    vid_path = vid_pack['metadata']['filepath']
    data_filename = data_file(vid_path)
    write_data(data_filename, vid_pack['metadata'])
    logging.info("Saved metadata for video {}".format(vid_path))

def todo(packs):
    for vid_pack in packs:
        for num in vid_pack['metadata']['failed'].copy():
            yield(vid_pack['index'], num)

def set_success(vid_pack, frame_pack, success):
    frame_pack['metadata']['success'] = success
    if success:
        try:
            assert frame_pack['index'] in vid_pack['metadata']['failed'], "Frame not included in 'failed' set."
            vid_pack['metadata']['failed'].remove(frame_pack['index'])
        except AssertionError as e:
            logging.info("Frame not previously listed as failed.")
            logging.debug(e)
            logging.debug(traceback.format_exc())
    else:
        vid_pack['metadata']['failed'].add(frame_pack['index'])

def rereference(frames, ref_num, align_num):
    frames[frames[align_num]['refer_to']]['refer_by'].remove(align_num)
    frames[align_num]['refer_to'] = ref_num
    frames[ref_num]['refer_by'].add(align_num)

def reset_global_matrix(vid_pack):
    vid_pack['metadata']['global_matrix'] = np.eye(3,3,dtype = np.float32)
    save(vid_pack)

def reset_frame_matrix(vid_pack, frame_pack):
    frame_pack['metadata']['abs_matrix'] = np.eye(3,3,dtype = np.float32)
    clear_frame_reference(vid_pack, frame_pack)
    save(vid_pack)

def clear_frame_reference(vid_pack, frame_pack):
    rereference(vid_pack['metadata']['frames'], 
        frame_pack['index'], frame_pack['index'])
    frame_pack['metadata']['rel_matrix'] = np.eye(3,3,dtype = np.float32)
    save(vid_pack)