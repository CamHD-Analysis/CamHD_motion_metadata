

# June 16 2017

## OpticalFlow v1.0 -> v1.1

v1.0 `optical_flow.json` files can be converted to v1.1 using the script [20170616_optical_flow_v1_0_to_v1_1.py](../scripts/migrations/20170616_optical_flow_v1_0_to_v1_1.py).

Migration scripts are written to be safe when run on post-migration files.

 * In the top-level "contents" sections:
  * Rename "frame_stats" as "frameStats"
  * Remove the intermediate "contents" layer within "frameStats".
  * Rename the "frameStats" content type "optical_flow as "opticalFlow"
  * Updates "opticalFlow" content type to "v1.1"

* Rename the top-level section "frame_stats" to "frameStats"
* Within each element of the "frameStats" array:
 * Rename "similarity" to "opticalFlow"
 * Delete the "performance" section _if_ element was named "similarity".  Versions of frame_stats which generate v1.0 optical_flow information do not generate valid performance information.

* If top-level "timing" section exists, delete it.  This version of frame_stats generates incorrect timing information when run in a multithreaded manner.    Version which implement a correct timing algorithm use a top-level "performance" object
which includes a "timing"


## OpticalFlowRegions v1.0 -> v1.1

v1.0 `optical_flow_regions.json` files can be converted by reprocessing (with the --force option) using [make_regions_files.py](../scripts/make_regions.files.py).

 * In the top-level "contents" sections:
  * Updates "regions" content type to "v1.1"

* In each region:
 * Replaces the 2-tuple "bounds" with separate "startFrame" and "endFrame" fields
 * In the "stats" object:
   * Replace "scale_mean" with "scaleMean"; "tx_mean" with "txMean"; and "ty_mean" with "tyMean"
