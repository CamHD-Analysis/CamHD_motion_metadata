# Dependencies

The script takes a whole raft of Python dependencies.   I believe the conda-format
file `scripts/requirements.yml` is correct.  With [conda](https://conda.io/docs/) installed, the command

    conda env create -f scripts/requirements.yml

If the env already exists, then `conda env update` should be used

    conda env update -f scripts/requirements.yml

# Set following environments variables:
* `CAMHD_MOTION_METADATA_DIR`: The path to the local clone of the repository. This is required if `--use-cnn` flag is set.
* `CAMHD_SCENETAG_DATA_DIR`: The data directory to store train data and trained models. This is required if `--cnn-model-config` argument is provided. Previous train data (need to extracted) and the trained models (keras) can be downloaded from this [google drive folder](https://drive.google.com/drive/folders/1fbsL4FfJTWV4Vp2h17oS7gQi58Hz7meQ?usp=sharing).

_NOTE_: If `process_regions_files.py` is being used, then both the above environment variables need to be set.

# make_regions_file.py

The [make_regions_file.py](../scripts/make_regions_file.py) script is the
command-line interface into the Python modules which convert [optical flow](OpticalFlowJson.md)
metadata files into [regions](OpticalFlowRegionsJson).   It runs in two stages:

  1. Break the video into time frames with consistent camera behavior (camera static, zooming in, panning left, etc.).
  1. Use a set of hand-labelled ground truth files to attempt to label each static section with its corresponding [region](Regions.md).

To run the script, from the top level of the repo

     python script/make_regions_file.py [path to optical flow files]

the script takes wildcards, and if given a directory, it will assume `*_optical_flow.json` e.g.,

     python script/make_regions_file.py RS03ASHS/PN03B/06-CAMHDA301/2016/01/*/*_optical_flow.json

and

    python script/make_regions_file.py RS03ASHS/PN03B/06-CAMHDA301/2016/01/*/

Are equivalent.   It will automatically determine the region filename and place it
in the same directory as the optical flow file unless otherwise configured.
It __will not__ overwrite existing files, unless given the `--force` flag.

## Flags

  * `--dry-run` will cause the script to perform all processing but does not write to the output file.

  * If given the `--force` option, the script will overwrite any existing `_optical_flow_regions.json` files.

  * If given the `--force-unclassified` option, the script will recreate any
  existing files _only_ if any static regions in the file are unclassified.
  This option is for handling any existing regions files which contain only the
  segment analysis but predate the static region labelling functionality -- or were processed
  with the `--no-classify` option (below).

  * The `--no-classify` causes the script to stop processing after extracting regions (which is cheap),
  but to skip region labelling (which is expensive).  These files can be
  processed later using the `--force-unclassified` option.

  * This script uses the [Python3 Logging](https://docs.python.org/3/library/logging.html)
  function.   The `--log` option allows specification of the [logging level](https://docs.python.org/3/library/logging.html#levels) shown on the console.

  * The `--first [N]` option causes the script to label only the first N static regions
  in a file.  Good for validating the labelling algorithms.

  * `--ground-truth` specifies the location of the `ground_truth.json` file used
  to specify the set of ground truthfiles.   This defaults to [`classification/ground_truth.json`](../classification/ground_truth.json).


  * `--use-cnn` Flag to use the trained CNN model for region classification. If this flag is set, then the --ground-truth argument is ignored. If this flag is not set, the 'matchByGroundTruth' algorithm will be used for region classification.
  
  * `--cnn-model-config` The path to the scene tag classifier CNN model config json file. Default: The config corresponding to the latest model in the classifiers_meta_file (scene_tag_classifiers_meta.json).<br>
  _NOTE:_ The trained models referred by the cnn-model-config must be present in the `$CAMHD_SCENETAG_DATA_DIR/trained_classification_models` directory. The trained classification models can be downloaded from this [google drive folder] (https://drive.google.com/drive/folders/1MVaCIZ7XQfVPdjlsr0bspuiNS4PBRPdE?usp=sharing).

  * The `--git-add` argument causes the script to `git add` any new regions files
  it may create (including when overwriting an existing file).

  * The script will download image frames as needed for region labelling.
  Ground truth images are cached in the `classification/images/` directory,
  while images from test files are not cached.

  These images are retrieved using [pycamhd-lazycache](https://github.com/CamHD-Analysis/pycamhd-lazycache).   It will default to the
  public lazycache hosted on Google App Engine.   An alternative URL can be
  specified with the `--lazycache-url` flag.   The URL should include the whole path to the root of the Rutgers CI
  mirror.   For example, the default is:

    http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files

# Algorithms

The two phases of region extraction are relatively independent.

## Finding regions

The first step is dividing the time sequence for a movie into contiguous
`regions` or segments which correspond to one step or stage in the camera's
motion sequence.  It does this by examining the output from the
optical-flow-based [motion
analysis](https://github.com/CamHD-Analysis/camhd_motion_analysis).   This step
requires no additional input other than the [optical flow
JSON](OpticalFlowJson.md) file --- it doesn't require any frames from the
original video and is relatively quick.

The output is a complete [regions](OpticalFlowRegionsJson.md) file, with the
static sections unlabelled (the `sceneTag` entry will not exist in each region).
The script will write this output to disk as an intermediate checkpoint before
initiating region classification.

(more here)

## Classifying regions

The static regions in a file are labelled by comparison to the labelled regions
in a  set of hand-annotated (or at least, hand-validated) ground truth files.
Doing this requires retrieving representative images for both the ground truth
files and files under test, which  is done using
[Lazycache](https://github.com/CamHD-Analysis/pycamhd-lazycache).    The script
will aggressively cache and reuse images extracted from ground truth files but
does not retain images extracted from test videos.

A list of validated ground truth files is kept in [classification/ground_truth.json](../classification/ground_truth.json).
This file contains a JSON list of regions files which are taken as ground truth.
The `GroundTruthLibrary` Python class loads the contents of this file, and from there
stores the static region information for those files.

When presented with a new file to classify, the GroundTruthLibrary selects a subset of ground truth files which are temporally closest to the test file (right now, there's only one ground truth file, so it always draws that files, but in the long run it may draw more than one).   It
then checks the current contents of the classification image cache (`classification/images`)
and catalogs the number of representative images available for each label from the ground truth image.
If a minimum number of images are not available for every label, it downloads
additional images, randomly selected from the relevant regions in the ground truth
files.

For each static region in the test file, it draws _N_ representative images using
Lazycache.  At present, these frames are drawn deterministically by taking the, e.g.,
images at the 40%, 50% and 60% point in the region.  Each of these test frames is compared
against _M_ ground truth images randomly drawn from each class in the ground truth set.  That is, if
there at _C_ static region labels (there are currently _C=23_ labels), classifying
a region requires

  N x M x C

image comparisons.

The current image comparison algorithm performs a DFT-based correlation (using
[imreg-dft](http://imreg-dft.readthedocs.io/en/latest/) on a subsampled,
greyscale version of each image. Each comparison gives an estimated translation
(shift) between the two images and an RMS error at the translation of best
match.  Any translations indicating a shift of more than 10\% of subsampled
image dimensions are immediately discarded.

For each class, the highest and lowest RMS values are discarded and the mean of
the remaining RMS values is used as an aggregate score for the match between the
test region and that class.  Those scores are ranked, and the highest-ranked
match is accepted if the ratio between the first- and second-best match exceeds
a given ratio.

Any regions which do not have a definitive label are left unlabelled.   After
attempting photometric processing for the all static regions, two further
processing steps are used to attempt to classify these regions.

Any unclassified regions are photometrically compared (using the same DFT-based
algorithm) to the nearest preceding and following regions which _have_ been
successfully labelled.   If this photometric comparison has a low RMS (below a
preset threshold), the unlabelled region adopts the label of its matching
neighbor.   This catches cases where a longer continuous section is incorrectly
subdivided into multiple regions.

Finally, a reference sequence of camera motions is known a priori.   Due to
variability in the camera motion and the region extraction algorithm, the
sequence of regions extracted from a given video might vary from this reference
sequence.   In cases where an unknown section is preceded and followed by
labelled section, this three-region sequences (known-unknown-known) will be
compared to the reference sequence.   If matched to a portion of the reference
sequence, the intervening unlabelled region adopts the middle label.

If a region is successfully labeled, the tag `sceneTag` is added to the region file.   If a region cannot be labelled, a region is labelled `unknown`.  The `sceneTagMeta` tag is used to store meta information about the matching process.

# process_regions_files.py
The runner script to automate the process of creating region files for new set of videos.<br>
_Note:_ This uses the latest data and creates new files. Therefore, run this on a new branch taken from updated master.

##### Usage:
Please use the `--help` argument to check all the arguments for the script.

```
python process_regions_files.py --config <path to regions_file_process_config.json> --logfile <path_to_logfile>
```

##### The STEPS involved in the script.
* *STEP 1*: Sample data from new validated region files.
* *STEP 2*: Merge the train datasets.
* *STEP 3*: Train the CNN on the new train data.
* *STEP 4*: Make region files for input_optical_flow_files.
* *STEP 5*: Create Validation Report.
* *STEP 6*: Create Proofsheet.

##### MANUAL Steps After running this script *(these steps also appear as warnings in the logs)*:
1. Add newly trained model to GoogleDrive and classifiers meta to Git, and clear the train and validation splits.
   * The classifier_meta_file (scene_tag_classifiers_meta.json) would be updated and need be pushed to Git Repository.
   * The new trained model need be shared by uploading to the Google Drive.
   * The train and validation split of the current train data can be deleted.
2. The validation report would be created, and need to be pushed to Git Repository.
3. Validation regions files and generate performance evaluation report.
   * The proofsheets can be used to manually validate and correct the region files scene_tags.
   * The corrected and validated regions files need to be pushed to the Git Repository.
   * The Performance Evaluation Report need to be generated and pushed to the Git Repository. Refer the logs for the command to generate the Performance Evaluation Report.

##### Region Files Process Config (JSON file) documentation:

```python
{
    "version": 0.1,       # The version id for the process workflow.
    "deployment": "d5A",  # The deployment tag.
    "name": "201901",     # The name as an identifier for this config file.

    # A bash wildcard referring to the regions files which have been recently validated, but not included in training.
    "new_validated_reg_files": "$CAMHD_MOTION_METADATA_DIR/RS03ASHS/PN03B/06-CAMHDA301/2018/12/*",

    # Name of the directory for train data sampled from 'new_validated_reg_files'.
    # It will be stored in $CAMHD_SCENETAG_DATA_DIR/scene_classification_data.
    "new_reg_train_data_dirname": "set_201812",

    # Probability to be used while sampling frames from 'new_validated_reg_files'.
    "new_reg_sampling_prob": 0.5,

    # Name of the directory containing the train data to which the data from 'new_reg_train_data_dirname'
    # needs to be appended. It could be the train data from the previous model training.
    # It will be taken from (prefixed with) $CAMHD_SCENETAG_DATA_DIR/scene_classification_data.
    "base_train_data_dirname": "set_201811_train_data",

    # Probability to be used while sampling train data from 'base_train_data_dirname'.
    "base_train_data_prob": 0.5,

    # Name of the directory for merged train data including train data
    # from 'base_train_data_dirname' and 'new_reg_train_data_dirname'.
    # It will be stored in $CAMHD_SCENETAG_DATA_DIR/scene_classification_data.
    "merged_train_data_dirname": "set_201812_train_data",

    "val_split": 0.25,    # Optional. The proportion of train data from 'merged_train_data_dirname' to be used as validation data. Defaulted to 100.
    "epochs": 100,        # Optional. The number of epochs. Defaulted to 100.
    "batch_size": 8,      # Optional. The batch-size for training. Defaulted to 8.
    "restrict_gpu": "0",  # Optional. The GPU core id to be used. Defaulted to system's $CUDA_VISIBLE_DEVICES value. If not set, all GPU cores will be utilized.

    # The new trained model will be stored at $CAMHD_SCENETAG_DATA_DIR/trained_classification_models.
    # Corresponding model_config will be updated in the classifier_meta_file (scene_tag_classifiers_meta.json).
    # The model version will be inferred by taking the next model version from the current 'latest_model' version.

    # A bash wildcard referring to the optical flow files for which the regions files need to be generated.
    "input_optical_flow_files": "$CAMHD_MOTION_METADATA_DIR/RS03ASHS/PN03B/06-CAMHDA301/2019/01/0[456789] $CAMHD_MOTION_METADATA_DIR/RS03ASHS/PN03B/06-CAMHDA301/2019/01/1[123456789] $CAMHD_MOTION_METADATA_DIR/RS03ASHS/PN03B/06-CAMHDA301/2019/01/2[123456789] $CAMHD_MOTION_METADATA_DIR/RS03ASHS/PN03B/06-CAMHDA301/2019/01/3[01]",

    # Optional. If 'monthly' key is provided, the 'input_optical_flow_files' will be automatically inferred
    # with respect to the $CAMHD_MOTION_METADATA_DIR. The above example contains inferred value from 'monthly': '2019-01'.
    "monthly": "2019-01",

    # The output path for the validation report of the regions files.
    "validation_report_path": "$CAMHD_MOTION_METADATA_DIR/regions_files_validation_reports/201901.txt",

    # The output path for the proofsheets required for manual verification of the regions files.
    "proofsheet_path": "$CAMHD_SCENETAG_DATA_DIR/proofsheets/201901/raw.html"
}
```

##### The sample Region Files Process Config is available at:
```
<Repositry_Root>/pycamhd-motion-metadata/examples/sample_region_files_process_config.json
```
