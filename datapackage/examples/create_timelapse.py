import subprocess
import os
import datetime

scene = 'd2_p8_z1'


# prepare paths
videos = "output/" + scene + '/videos/'
frames = "output/" + scene + '/frames/'


# create output directory
if not os.path.exists(videos):
	os.makedirs(videos)



# get list of files to parse for time stamps as subtitles
f = []
for dirpath, dirnames, filenames in os.walk(frames):
    f.extend(filenames)
f = [i[19:35] for i in f]


# create initial timelapse
create_vid = "ffmpeg -framerate 10 -pattern_type glob -i '" + frames + \
	"*.png' -c:v libx264 -pix_fmt yuv420p " + videos + scene + "-time_lapse.mp4"
process = subprocess.Popen(create_vid,shell=True)
process.wait()


# stabilize timelapse
detect_vid = "ffmpeg -i " + videos + scene + "-time_lapse.mp4 -vf vidstabdetect -f null -"
process = subprocess.Popen(detect_vid,shell=True)
process.wait()
stab_vid = "ffmpeg -i "+ videos + scene + "-time_lapse.mp4 -vf vidstabtransform " + videos + scene + "-time_lapse_stabilized.mp4"
process = subprocess.Popen(stab_vid,shell=True)
process.wait()



# create subtitle srt file
images_per_sec = 10.0
dt = datetime.timedelta(seconds=(1.0/images_per_sec))

with open(videos + scene + '.srt', 'w') as srt:
    count = 1
    this_time = datetime.datetime(1,1,1)

    for i in f[1:]:
        srt.write("%d\n" % count)

        next_time = this_time + dt
        srt.write("%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n" %
                  (this_time.hour, this_time.minute, this_time.second, this_time.microsecond/1000,
                   next_time.hour, next_time.minute, next_time.second, next_time.microsecond/1000))

        # Write the actual subtitle
        srt.write(i + '\n\n')

        this_time = next_time
        count = count + 1

# convert srt to ass
convert_sub = "ffmpeg -i " + videos + scene + ".srt " + videos + scene +".ass"
process = subprocess.Popen(convert_sub ,shell=True)
process.wait()


# position the timestamp in the video and change font size
with open(videos + scene + ".ass") as ass_file:
	lines = ass_file.readlines()
	new_lines = []
	for line in lines:
		if line.startswith('Dialogue'):
			line = line[:43] + line[43:44].replace('0', '300') + line[44:] 
			line = line[:49] + line[49:50].replace('0', '260') + line[50:]
			new_lines.extend(line)
		elif line.startswith('Style'):
			line = line[:21] + line[21:23].replace('16', '12') + line[23:]
			new_lines.extend(line)
		else:
			new_lines.extend(line)
	

with open(videos + scene + ".ass", "w") as ass_file:
	ass_file.writelines(new_lines)



# add subtitles to stabilized video
add_sub = "ffmpeg -i "+ videos + scene + "-time_lapse_stabilized.mp4 -vf ass=" + videos + scene +".ass " + videos + scene + "-time_lapse_stabilized_subs.mp4"
process = subprocess.Popen(add_sub ,shell=True)
process.wait()


os.remove('transforms.trf')
os.remove(videos + scene + '.srt')
