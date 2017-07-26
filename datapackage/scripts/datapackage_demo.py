import datapackage

url = "https://raw.githubusercontent.com/CamHD-Analysis/CamHD_motion_metadata/master/datapackage/datapackage.json"

dp = datapackage.DataPackage(url)

print(dp.descriptor['title'])
