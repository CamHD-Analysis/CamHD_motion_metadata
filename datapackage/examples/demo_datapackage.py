import datapackage

url = "https://raw.githubusercontent.com/CamHD-Analysis/CamHD_motion_metadata/master/datapackage/datapackage.json"

dp = datapackage.DataPackage(url)

print(dp.descriptor['title'])

#regions = next(r for r in dp.resources if r.name == 'regions')
regions = dp.resources[0]                  # This shouldn't hard coded, should look for resource with name 'regions'

d2_p2_z0 = [r for r in regions.iter() if r['scene_tag'] == 'd2_p2_z0']

print("Data package contains %d regions with scene tag 'd2_p2_z0'" % len(d2_p2_z0))
