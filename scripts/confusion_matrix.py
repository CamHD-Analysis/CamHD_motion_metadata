import json
import numpy as np
import pandas as pd
import random
import seaborn as sn
import matplotlib.pyplot as plt

sampleGeneratedFile = "RS03ASHS/PN03B/06-CAMHDA301/2016/08/01/CAMHDA301-20160801T000000Z_optical_flow_regions.json"
manualTagsPath = "RS03ASHS/PN03B/06-CAMHDA301/2016_manual/08/"
generatedTagsPath = "RS03ASHS/PN03B/06-CAMHDA301/2016/08/"

def getTags(file):
	
	data = json.load(open(file))
	tags = []
	for tag in range(0, len(data['regions']), 2):
		if tag not in tags:
			tags.append(data['regions'][tag]['sceneTag'])

	return tags 

def addDummyData(path):

	tags = []
	f = open("order.txt")
	lines = f.readlines()
	for line in lines:
		tags.append(line.strip("\n"))
		tags.append("d3_p2_z2")
	tags = list(set(tags))
	for i in range(1,31):
		s=""
		if(i < 10):
			s="0"+str(i)
		else:
			s=str(i)
		
		s = s + "/CAMHDA301-201608"+s+"T000000Z_optical_flow_regions.json"
		random.shuffle(tags)
		with open(path+s, "w") as f:
			for tag in tags:
				f.write(tag+"\n")
		f.close()
	
	return tags

def confusionMatrix(tags, manualPath, generatedPath):
	#confusion matrix with each tag
	A = np.zeros(shape = (len(tags), len(tags)))
	
	#creating the matrix
	df = pd.DataFrame(A, index=tags, columns=tags)	
	for i in range(2, 14):
		s=""
		if(i < 10):
			s="0"+str(i)
		else:
			s=str(i)

		s = s + "/CAMHDA301-201608"+s+"T000000Z_optical_flow_regions.json"	
		#manual tags
		mFile = open(manualPath+s, "r")
		mTags = []
		for m in mFile.readlines():
			mTags.append(m.replace(" ", "").strip("\n"))

		#generated tags 
		data = json.load(open(generatedPath+s))
		

		gTags = []

		for i in range(0, len(data['regions']), 2):
				gTags.append(data['regions'][i]['sceneTag'])


		for i in range(len(mTags)):
			
			if mTags[i] in tags and gTags[i] in tags:
				df[mTags[i]][gTags[i]] = df[mTags[i]][gTags[i]] + 1
				

	sn.set(font_scale=1) #for label size
	sn.heatmap(df, annot=True,annot_kws={"size": 16})# font size
	plt.show()

#tags = getTags(file = sampleGeneratedFile)
tags = addDummyData(path = manualTagsPath)
confusionMatrix(tags = tags, manualPath=manualTagsPath, generatedPath=generatedTagsPath)




