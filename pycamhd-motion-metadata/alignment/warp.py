"""
Contains code for actually aligning two images.
"""

import cv2
import time
import numpy as np
import helper

"""
Calculates a transformation from one image to another. 
Supports transformations other than homographies.
"""
def calculate(reference, align, warp_matrix, warp_mode = cv2.MOTION_HOMOGRAPHY, iterations = 50, termination_eps = 1e-4):
    append = []
    if warp_mode != cv2.MOTION_HOMOGRAPHY:
        append = warp_matrix[2:3]
        warp_matrix = warp_matrix[:2]
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, iterations,  termination_eps)
    (cc, warp_matrix) = cv2.findTransformECC(reference, align, warp_matrix, warp_mode, criteria, None)
    if warp_mode != cv2.MOTION_HOMOGRAPHY:
        warp_matrix = np.concatenate((warp_matrix,append))
    return warp_matrix

"""
Applies a transformation matrix to an image and returns the warped image.
"""
def apply_warp(img, warp_matrix, warp_mode = cv2.MOTION_HOMOGRAPHY):
    sz = img.shape
    if warp_mode == cv2.MOTION_HOMOGRAPHY:
        warped = cv2.warpPerspective(img, warp_matrix, (sz[1],sz[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
    else:
        warp_matrix = warp_matrix.copy()[:2]
        warped = cv2.warpAffine(img, warp_matrix, (sz[1],sz[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
    return warped

"""
Aligns two images with a pyramid approach with the specified settings
"""
def pyramid(ref, align, settings, est_warp = np.eye(3,3,dtype = np.float32)):
    assert ref is not None and align is not None, "Reference and align images must not be None."
    assert est_warp.shape == (3,3), "Estimated warp matrix must be 3x3."

    matrix = est_warp

    for setting in settings:
        mode = setting[0]
        func = setting[1]
        power = setting[2]
        iterations = setting[3]

        scale = 0.5**power

        rsz1 = func(helper.resize_scale(ref, scale))
        rsz2 = func(helper.resize_scale(align, scale))

        matrix = helper.scale_matrix(matrix, scale)
        matrix = calculate(rsz1, rsz2, matrix, mode, iterations)
        matrix = helper.scale_matrix(matrix, 1/scale)
        matrix = helper.one(matrix)
    
    aligned = apply_warp(align, matrix, cv2.MOTION_HOMOGRAPHY)
    similarity = helper.similar(ref, aligned, multichannel = True)
    return matrix, similarity

"""
Finds the transformation between two images.
Originally designed to include multiple pyramid calls.
"""
def find_matrix(ref, align):
    assert ref is not None and align is not None, "Reference and align images must not be None."

    matrix_rel, similarity = pyramid(ref, align, settings = settings)

    return matrix_rel, similarity

def gray(img):
    img = helper.gray(img)
    return img

def silhouette(img):
    img = helper.gray(img)
    img = helper.GaussBlur(img)
    img = helper.binary(img)
    return img

def clahe_mod(img):
    img = helper.gray(img)
    factor = np.sqrt(img/255.0)
    clahe = helper.CLAHE(img)
    img = np.multiply(factor, clahe)
    img = img.astype(np.uint8)
    return img

# translation, euclidean, affine, homography
# Settings:
settings = [ # Feel free to change as necessary.
        (cv2.MOTION_TRANSLATION, clahe_mod, 3, 100),
        (cv2.MOTION_HOMOGRAPHY, clahe_mod, 1, 50),
        (cv2.MOTION_HOMOGRAPHY, clahe_mod, 0, 50),
        ]

# if __name__ == '__main__':
#     a = cv2.imread("input/d3_p4_z0.jpg")
#     helper.display(a, scale=0.5)
#     helper.display(gray(a), scale=0.5)
#     helper.display(clahe_mod(a), scale=0.5)
#     helper.pause()