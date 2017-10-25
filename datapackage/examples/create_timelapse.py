#!/usr/bin/env python3

# For video stabilization documentation, see:
#     https://github.com/georgmartius/vid.stab

import subprocess
import os
from os import path
import datetime
import argparse
import logging

parser = argparse.ArgumentParser(description='Use ffmpeg to convert sets of images to timelapse movies')

parser.add_argument('--scene-tag', metavar='scene_tag', nargs='?',
                    help='Scene tag to work with')

parser.add_argument('--log', metavar='log', nargs='?', default='DEBUG',
                    help='Logging level')

parser.add_argument('--prores', action='store_true',
                    help='Also make a ProRes (high resolution) movie')

parser.add_argument('--hevc', action='store_true',
                    help='Make MP4 in HEVC (H.265) format')

parser.add_argument('--nvidia', action='store_true',
                    help='Use GPU for encoding videos')

parser.add_argument('--force', action='store_true',
                    help='Download images even if a file with the same name already exists')

parser.add_argument('--output', dest='outdir', nargs='?', default=None,
                    help='Directory for timelapse images')

args = parser.parse_args()

logging.basicConfig(level=args.log.upper())

if not args.scene_tag:
    logging.fatal("Scene tag must be specified with --scene-tag")
    exit(-1)

scene = args.scene_tag

# prepare paths
videos_path = "output/" + args.scene_tag + '/videos/'
frames_path = "output/" + args.scene_tag + '/frames/'


# create output directory
if not os.path.exists(videos_path):
    os.makedirs(videos_path)

# get list of files to parse for time stamps as subtitles
f = []
for dirpath, dirnames, filenames in os.walk(frames_path):
    f.extend(filenames)
f = [path.basename(i) for i in f]

# Frames per second
framerate = 10

# Make subtitle .srt file
dt = datetime.timedelta(seconds=(1.0/framerate))
this_time = datetime.datetime(1, 1, 1)

subtitles_file = videos_path + scene + '.srt'
with open(subtitles_file, 'w') as srt:
    count = 1

    for filename in f:
        srt.write("%d\n" % count)

        next_time = this_time + dt
        srt.write("%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n" %
                  (this_time.hour, this_time.minute, this_time.second, this_time.microsecond/1000,
                   next_time.hour, next_time.minute, next_time.second, next_time.microsecond/1000))

        # Write the actual subtitle
        srt.write("%s\n" % filename )

        # Blank line between entries
        srt.write("\n")

        this_time = next_time
        count = count + 1


ffmpeg_global_opts = "-hide_banner -thread_queue_size 4096 -y"

if args.hevc:
    if args.nvidia:
        # Haven't tuned any options here
        mp4_vid_opts = "-c:v hevc_nvenc  -pix_fmt yuv420p"
    else:
        # Haven't tuned any options here
        mp4_vid_opts = "-c:v libx265 -crf 17 -pix_fmt yuv420p"
else:
    if args.nvidia:
        # From "ffmpeg -h encoder=h264_nvenc"
        # -cq = Set target quality level (0 to 51, 0 means automatic) for constant quality mode in VBR rate control (from 0 to 51) (default 0)
        # -bf = Set max number of B frames between non-B-frames.
        # -g  = set the group of picture (GOP) size
        #
        # ** Was unable to get acceptable video with nvenc
        mp4_vid_opts = "-c:v h264_nvenc -preset:v slow -profile:v high -rc:v vbr -cq:v 51 -bf 2 -g 150 -pix_fmt yuv420p"
    else:
        mp4_vid_opts = "-c:v libx264 -profile:v high -crf 17 -pix_fmt yuv420p"


mp4_extension = 'mp4'
subtitle_opts = "-i %s -scodec mov_text -metadata:s:s:0 language=eng" % subtitles_file

# create initial timelapse
movie_file            = videos_path + scene + "-time_lapse.%s" % mp4_extension
unsharp_movie_file    = videos_path + scene + "-unsharp.mp4"
vidstab_file          = videos_path + scene + "-vidstab.trf"
vidstab_visualization = videos_path + scene + "-vidstab.mp4"
stabilized_movie_file = videos_path + scene + "-time_lapse_stabilized.%s" % mp4_extension

if not os.path.isfile(movie_file) or args.force:
    create_vid = ("ffmpeg %s -framerate %d -pattern_type glob -i '%s*.png' %s %s %s"
                  % (ffmpeg_global_opts, framerate, frames_path, subtitle_opts, mp4_vid_opts, movie_file))
    logging.debug("==> "  + create_vid )
    process = subprocess.run(create_vid,shell=True,check=True)

    if os.path.isfile(unsharp_movie_file):
        os.remove(unsharp_movie_file)

movie_to_stabilize = movie_file

# Create a blurred version of video to remove HF transients in video
# stabilization routine.
# if not os.path.isfile(unsharp_movie_file) or args.force:
#     detect_vid = "ffmpeg %s -i %s -vf unsharp=13:13:-1.0:13:13:-1.0 %s %s" % (ffmpeg_global_opts, movie_file,  mp4_vid_opts, unsharp_movie_file)
#     logging.debug("==> "  + detect_vid )
#     process = subprocess.run(detect_vid,shell=True,check=True)
#     movie_to_stabilize = unsharp_movie_file

#stab_opts = "shakiness=1:show=2:mincontrast=0.2:tripod=1:result=%s" % vidstab_file
stab_opts = "result=%s" % vidstab_file

# stabilize timelapse
detect_vid = "ffmpeg %s -i %s -vf vidstabdetect=%s %s"  \
              % (ffmpeg_global_opts, movie_to_stabilize, stab_opts, vidstab_visualization)
logging.debug("==> "  + detect_vid )
process = subprocess.run(detect_vid,shell=True,check=True)
#
# stab_opts = "optzoom=0:tripod=1:crop=black:maxangle=0:input=%s" % vidstab_file
stab_opts = "input=%s:debug=1" % vidstab_file

# unsharp=5:5:0.8:3:3:0.4,
stab_vid = "ffmpeg %s -i %s %s -vf vidstabtransform=%s %s" \
            % (ffmpeg_global_opts, movie_file, subtitle_opts, stab_opts, stabilized_movie_file)
logging.debug("==> "  + stab_vid )
process = subprocess.run(stab_vid,shell=True,check=True)


## Make Prores codec files
if args.prores:
    logging.info("Producing Prores files")

#-qscale:v 10

    prores_vid_opts = "-c:v prores -profile:v 3 -pix_fmt yuv422p10le"
    prores_extension = 'mov'

    # create initial timelapse
    movie_file            = videos_path + scene + "-time_lapse.%s" % prores_extension
    stabilized_movie_file = videos_path + scene + "-time_lapse_stabilized.%s" % prores_extension

    # Video stabilization from images to Prores works (prores -> prores doesn't)
    create_vid = ("ffmpeg %s -framerate %d -pattern_type glob -i '%s*.png' %s -vf format=pix_fmts=yuv420p,vidstabtransform=%s %s %s"
                  % (ffmpeg_global_opts, framerate, frames_path, subtitle_opts, stab_opts, prores_vid_opts, stabilized_movie_file))
    logging.debug("==> "  + create_vid )
    process = subprocess.run(create_vid,shell=True,check=True)
