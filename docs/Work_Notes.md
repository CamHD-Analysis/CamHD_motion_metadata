# Work Notes

This file covers changes, suggestions, and observations while going over the region classification code.

## Changes

### pycamhd-motion-metadata/pycamhd/region_analysis/classify_regions.py

* Added a skip threshold that causes the classification to tag the region immediately without retrieving more samples.
* Samples are now selected from regions at points 0.5, 0.2, and 0.8 (in that order) as opposed to 0.4, 0.5, and 0.6.
* Set default skip threshold to 0.75 and changed default probability threshold from 0.2 to 0.5.
* Added code to log time taken for files and individual regions.

### pycamhd-motion-metadata/pycamhd/region_analysis/find_regions.py

* Trivial code documentation and cleanup

### pycamhd-motion-metadata/pycamhd/region_analysis/scene_tag_classifiers_meta.json

* Created a v0.95 configuration copied from v0.9, but with a skip threshold of 0.65 and probability threshold of 0.4.
* Updated latest model to be the 0.95 configuration. 

### pycamhd-motion-metadata/scripts/make_regions_files.py

* Trivial code documentation

### pycamhd-motion-metadata/scripts/make_regions_proof_sheet.py

* If a ground truth file is not specified, a hard coded sequence of scene tags will now be used.
* The program will no longer insert a scene tag into the sequence if it does not detect a match with the sequence.
* Made the program more robust by searching forwards to the end, then backwards for a scene tag match as opposed to searching forward a preset number of steps and giving up.
* The time in `_format_url()` now returns hours and minutes as opposed to hours only.
* Added an extra overflow tag for if the program goes wrong unexpectedly.
* The program now shows thumbnails from all regions, not just the first region if there are duplicate regions of the same tag. 
* Multiple html proof sheets are now created in the event there are duplicate regions.
* Adjusted proof sheet to handle files from different deployments.

### pycamhd-motion-metadata/scripts/make_regions_csv_sheet.py

* Wrote a script to output summarized information for comparison of region classification over time.

### trained_classification_models/links.txt

* Added links to the pretrained CNN models and training sets.

### docs/Make_Regions_File.md

* Changed listed lazycache url from http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files to https://cache.camhd.science/v1/org/oceanobservatories/rawdata/files, as the former would shed its query string when redirecting to the latter.

### docs/Basic_Classification.md

* Wrote a series of instructions on how to classify regions and verify them.

### docs/Work_Notes.md

* Wrote this document. :P

### RS03ASHS/PN03B/06-CAMHDA301/2019/0[456]/*/*_regions.json

* Created _region.json files for April, May and June of 2019.
* Excluded days 1, 2, 3, 10, 20, and the T000000 for following days.
* Excluded files after 6/16 (new deployment).

## Recommendatons

### CNN

* Ideally the CNN probability threshold should probably be higher around 0.6-0.8 as opposed to 0.5, and definitely should not have been 0.2. However, as the confidence degrades over time, it would probably not be a good idea to set it too high.
* The CNN should have an "unknown" tag, as opposed to labeling regions that don't have high probabilities for any tags as "unknown"
* The CNN training and testing script in `pycamhd-motion-metadata/pycamhd/region_analysis` appears to be broken.

### Region Classification

* To decrease time wasted from duplicate regions of the same scene, it may be possible to write an algorithm that skips around and only goes back if an unclassified region is sandwiched between regions of different scenes.
* Threading would likely speed up the region classification, as most of the time is spent retrieving images from online.
* _region.json files currently should record the thresholds used when the regions were being classified.

## Notes

* The CNN confidence decreases noticably from January to June.
* There is a new deployment on 6/16 with what appears to be manual tests of the camera at unusual times.
* p5 and p6 scenes tend to be misclassified the most; however a significant portion of the scenes are blurry and of less interest in the first place.






