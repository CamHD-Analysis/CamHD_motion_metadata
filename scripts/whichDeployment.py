
import glob
import logging
import argparse
import os.path as path
import os
import json
import time
import subprocess
from datetime import datetime 

parser = argparse.ArgumentParser(description='Generate deployment details from _optical_flow.json files')

parser.add_argument('input', metavar='N', nargs='*', help='Files or paths to process')

args = parser.parse_args()

sample = args.input[0]
year = sample.split("-")[1][:4]
month =  sample.split("-")[1][4:6]
day =  sample.split("-")[1][6:8]
print(year, month, day)

if(datetime(int(year), int(month), int(day)) >= datetime(2015,11,18) and datetime(int(year), int(month), int(day)) <= datetime(2016,7,25) ):
	print("d2")

elif(datetime(int(year), int(month), int(day)) >= datetime(2016,7,29) and datetime(int(year), int(month), int(day)) <= datetime(2017,6,14) ):
	print("d3")

elif(datetime(int(year), int(month), int(day)) >= datetime(2017,8,14)):
	print("d3")

else:
	print("INVALID")