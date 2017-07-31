


import subprocess
import logging


years = [2016]

months = [1,2,3,4,5,6,7]

subsets = { '0?': 0,
            '1?': 1,
            '[2-3]?': 2}


f = open("_html/index.html", 'w')

f.write("<html><body>\n")
f.write("<ul>\n")

for year in years:
    for month in months:
        for reg, s in subsets.items():

            html_file = "%04d_%02d_%d.html" % (year, month, s)

            subprocess.run(['python', 'scripts/make_regions_proof_sheet.py',
			                "--lazycache-url", "http://ursine:8080//v1/org/oceanobservatories/rawdata/files/",
					"--with-groundtruth",
                            "--output", "_html/%s" % html_file,
                            "RS03ASHS/PN03B/06-CAMHDA301/%04d/%02d/%s/*_regions.json" % (year, month, reg)])

            f.write("<li><a href=\"%s\">%s</a>" % (html_file, html_file))

f.write("</ul>\n")
f.write("</html></body>\n")

f.close()
