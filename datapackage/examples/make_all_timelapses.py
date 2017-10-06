#!/usr/bin/env python3

import subprocess

#scenes = ['d2_p0_z0']

scenes = [ 'd2_p0_z0',
            'd2_p1_z0',
            'd2_p2_z0',
            'd2_p3_z0',
            'd2_p4_z0',
            'd2_p5_z0',
            'd2_p6_z0',
            'd2_p7_z0',
            'd2_p8_z0' ]

def execute(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break

        if output:
            print(output.strip())

    rc = process.poll()
    return rc

    # lines_iterator = iter(popen.stdout.readline, b"")
    # while popen.poll() is None:
    #     for line in lines_iterator:
    #         nline = line.rstrip()
    #         print(nline.decode("latin"), end = "\r\n",flush =True) # yield line


for scene in scenes:
    print("Downloading images for %s" % scene)

    execute(['./retrieve_frames.py', '--scene-tag', scene,
             '--log', 'INFO',
             '--lazycache-url', "http://localhost:8080/v1/org/oceanobservatories/rawdata/files/"])

    execute(['./create_timelapse.py', '--scene-tag', scene,
             '--log', 'INFO',
             '--prores'])
