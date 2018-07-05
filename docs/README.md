Documentation
=============

For a high-level overview of the processing of CamHD video, see [Twenty_Thousand_Foot_View.md](Twenty_Thousand_Foot_View.md) -- which is a work in progress!

 * [CamHD_Biography.md](CamHD_Biography.md) is a history of the CamHD program.

 * [Regions.md](Regions.md) describes the region labelling system ('d2_p2_z0' etc.) and provides
    sample images from each static region.

 * [Make_Regions_File.md](Make_Regions_File.md) provides the main documentation for the [`scripts/make_regions_files.py`](https://github.com/CamHD-Analysis/CamHD_motion_metadata/blob/master/scripts/make_regions_files.py) script which makes regions files from optical flow files.

 * [Making_Region_Proof_Sheets.md](Making_Region_Proof_Sheets.md) describes the [`scripts/make_regions_proof_sheet.py`](https://github.com/CamHD-Analysis/CamHD_motion_metadata/blob/master/scripts/make_regions_proof_sheet.py) script, which makes an HTML "proof sheet" for comparing sets of regions files.

 * [Json_Optical_Flow_File_Format.md](Json_Optical_Flow_File_Format.md) and [Json_Regions_File_Format.md](Json_Regions_File_Format.md) describes the format of the optical flow and regions JSON files.   Both files share some common fields described in [Json_Common_Headers.md](Json_Common_Headers.md).

  [Json_Format_Change_Log.md](Json_Format_Change_Log.md) describes the evolution of these two files.
