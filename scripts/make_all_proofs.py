#
#
# Thin wrapper around make_regions_proof_sheet which makes multiple,
# slightly more manageable proof sheets, and a top-level index.html
# file.
#

import subprocess
import json


# years = {2015: [11,12],
#          2016: [1, 2, 3, 4, 5, 6, 7],
#          2017: [9, 10] }

years = { 2017: [9, 10] }

subsets = {'0?': 0,
           '1?': 1,
           '[23]?': 2}

with open("_html/index.html", 'w') as f:

    f.write("<html><body>\n")

    f.write("<ul><li><a href='ground_truth.html'>Ground Truth</a>"
            "</ul><br/><br/>")

    for year, months in years.items():

        for month in months:

            f.write("<br/><h2>%d %d</h2>" % (year, month))
            f.write("<ul>\n")

            for regex, s in subsets.items():

                html_file = "%04d_%02d_%d.html" % (year, month, s)

                subprocess.run(['python',
                                'scripts/make_regions_proof_sheet.py',
                                "--lazycache-url", "http://ursine:8080//v1/org/oceanobservatories/rawdata/files/",
                                "--output", "_html/%s" % html_file,
                                "RS03ASHS/PN03B/06-CAMHDA301/%04d/%02d/%s/*_regions.json" % (year, month, regex)])

#                                "--with-groundtruth",


                f.write("<li><a href=\"%s\">%s</a>" % (html_file, html_file))

            f.write("</ul>\n")

    f.write("</html></body>\n")


# Ugly but fast
# Overwrite the file you just made

subprocess.run(['python',
                'scripts/make_regions_proof_sheet.py',
                "--lazycache-url", "http://ursine:8080//v1/org/oceanobservatories/rawdata/files/",
                "--with-groundtruth",
                "--output", "_html/2016_07_2.html",
                "RS03ASHS/PN03B/06-CAMHDA301/2016/07/2[0-5]/*_regions.json"])

## Make a ground truth proof file
gt_file = "classification/ground_truth.json"

with open(gt_file) as f:
    gt = json.load(f)

subprocess.run(['python', 'scripts/make_regions_proof_sheet.py',
                "--lazycache-url", "http://ursine:8080//v1/org/oceanobservatories/rawdata/files/",
                "--output", "_html/ground_truth.html"] + gt )
