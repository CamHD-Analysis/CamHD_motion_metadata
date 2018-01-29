import os
import errno

rootPath = "RS03ASHS/PN03B/06-CAMHDA301/2016_manual/08/"

for i in range(1,31):
	s=""
	if(i < 10):
		s="0"+str(i)
	else:
		s=str(i)
	
	s = s + "/CAMHDA301-201608"+s+"T000000Z_optical_flow_regions.json"
	if not os.path.exists(os.path.dirname(rootPath+s)):
	    try:
	        os.makedirs(os.path.dirname(rootPath+s))
	    except OSError as exc: # Guard against race condition
	        if exc.errno != errno.EEXIST:
	            raise

	with open(rootPath+s, "w") as f:
	    f.write("yup")