

import json
import os.path as path

infile = "CAMHDA301-20160301T000000Z.json"
outfile = "CAMHDA301-20160301T000000Z_munged.json"

with open(infile) as x:
    j = json.load(x)


jout = {}

for key,val in j.items():
    filename = path.basename(key)
    filename = filename.replace("frame_",'')
    filename = filename.replace(".png",'')

    jout[ int(filename) ] = val


jout = { "/RS03ASHS/PN03B/06-CAMHDA301/2016/03/01/CAMHDA301-20160301T000000Z/": jout }

with open(outfile,'w') as x:
    json.dump( jout, x, indent=2 )
