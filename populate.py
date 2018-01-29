import os

for i in range(15,31):
	if(i < 10):
		s="0"
	else:
		s=""
	s=s+str(i)
	os.system("python scripts/make_regions_files.py RS03ASHS/PN03B/06-CAMHDA301/2016/08/"+s+"/CAMHDA301-201608"+s+"T000000Z_optical_flow.json --force --lazycache-url http://localhost:8080/v1/org/oceanobservatories/rawdata/files/ --ground-truth classification/ground_truth_d3.json --force")
	f = open("logs.txt", "a")
	f.write(str(i)+"\n")
