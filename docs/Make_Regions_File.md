# Dependencies

The script takes a whole raft of Python dependencies.   I believe the conda-format
file `scripts/requirements.yml` is correct.  With [conda](https://conda.io/docs/) installed, the command

    conda env create -f scripts/requirements.yml

If the env already exists, then `conda env update` should be used

    conda env update -f scripts/requirements.yml

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


  * `--use-cnn` Flag to use the trained CNN model for region classification. If this flag is set, then the --ground-truth argument is ignored.
  If this flag is not set, the 'matchByGroundTruth' algorithm will be used for region classification. <br>
  _NOTE:_ The default trained CNN - [scene_classifier_cnn_d5A-v0.6.hdf5](https://drive.google.com/file/d/1nB-Fiod11_gsLy1FY14H3uMHegxd2IaF/view?usp=sharing) (_download from the link_) needs to be present in the 'pycamhd-motion-metadata/pycamhd/region_analysis/trained_classification_models/' directory.

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
The runner script to automate the process of creating region files for new set of videos.
Note: Ensure to run this on a new branch taken from updated master.

# TODO: Add documentation about the script and the sample config.
