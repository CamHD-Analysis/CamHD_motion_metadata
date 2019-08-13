This is a set of scripts for image alignment, built for https://github.com/CamHD-Analysis/CamHD_motion_metadata but can work for general videos.

Licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.
(C) Axel Li, 2019 (github: "inferee")

Apologies in advance if the code is difficult to read or bucks conventions. 
Asides from manual.py and warp.py, the code should be at least decently readable.

Introduction:
The code here serves to align frames of timelapse videos to each other with 2d homographies.

There were a couple of challenges with dealing the images:
1. The images are often severely misaligned across deployments.
2. The environment is constantly changing both in short and long timeframes. 
3. The images taken vary in color.
4. The images taken vary in lighting.
5. The images are blurry or distorted from time to time due to the water.

The alignment uses OpenCV's findTransformECC function. 
An edge filter approach would not work due to the function being area based, and the dynamic textures of the environment.
Feature based approaches would have truble with distortions and the environment constantly changing.
As a result, the end product automatically aligns within each deployment (assuming each video is a timelapse of a deployment) and has the user manually align between deployments.

The programs work in three steps:

auto.py - iterates through the input videos and creates initial alignments, storing that and other general metadata in a .json file
manual.py - allows users to manually align frames within and across videos when necessary, and updates the metadata as changes are made
apply.py - applies the transformations specified in the metadata and creates the actual aligned videos

Other Files:

helper.py - miscellaneous functions created for reuse
warp.py - program that actually calculates the transformations between two images
display.py - class created for use in manuual.py that displays images with various functionalities
reference.py - class created to determine what frame a specific frame in a video should align to

Program Quirks:
Python's glob module is used, meaning that it is possible to enter multiple files with pattern expansion. 
That being said, it is also possible to just list out all the videos.
The argument parsers for each of auto.py, manual.py, and apply.py are designed so users only need to change the script name to the next one without changing anything else.

The metadata for each video is relatively self explanatory if you peek in auto.py or look in one of the generated files.
However in manual.py video and frame "packs" are used quite extensively and may be confusing to understand.
Each video pack contains an index, OpenCV readers for the video itself, and the metadata for the video, all stored in a dict.
Each frame pack contains an index (the frame number), the image itself, and the metadata for the frame, also all in a dict.

For auto.py, a similarity threshold by comparing the Structural Similarity Index between the aligned and reference frame is used prevent misalignments.
In addition, auto.py uses a treated grayscale version of each image for the findTransformECC function.

The program also uses reference.py to determine which previous frame any particular frame should reference.
AbsoluteReference can create jittery alignments, and RelativeReference can slowly distort over time.
BinaryReference was created to deal with the issues of the previous approaches.

Due to the way the reference class is programmed, auto.py will always give a warning for the first frame. 
Always labeling the first frame as a success was considered but not implemented since frame references may change such that frame 0 is no longer a "root".

Two different types of alignments are possible with manual.py. 
If two frames from the same video are selected, they will be aligned and all references to the aligned frame will update.
If two frames from different videos are selected, then the videos will be aligned via the global matrix value. 
No individual frame matrices will be impacted when aligning two videos.

There is no reference protection for cross video alignment in manual.py.
This means it is possible to repeatedly align two videos against each other to get a extremely distorted output.

Tips:

Debug mode or testing on smaller sample videos beforehand recommended, as the program may still have unexpected bugs.

It is recommended to align frames and videos to the earliest frame/video that it can be matched against to prevent accumulation of errors with manual alignment.
It is possible to run auto.py, then apply.py, skipping any manual alignment. 

When running manual.py, sliding through the frames and videos in one display window while keeping the frame in the other constant can give a quick peek of what the end result looks like.

Future room for improvement:
Have draggable points at each corner of a semi-transparent frame and another frame underneath it for easier alignment.
Program in video references similar to frame references.
Get logging to file to work.
Better GUI and user controls.