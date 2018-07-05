Each time CamHD is serviced or replaced, we call that a different "deployment".   While the camera is nominally put in the same place every time, there are minor differences in
the camera position, camera lighting, and even the camera behavior (one of them zooms faster than the other) which can confound matching.   When the camera is cycled, the biofouling is
cleared, which also introduces a step change in the appearance.

We also use the deployment number to track changes in collection routine.  For example, `d2` is the "standard" pre-programmed routine during the 2015-2016 deployment.   `d1` is the pre-history before the pre-programmed routine was codified, while `d3` is the "standard" preprogrammed routine during the 2016-2017 deployment.    The photometric difference between the two routines can be seen in this sample:

<table>
  <tr>
    <td><img src="images/CAMHDA301-20160725T210000Z_5000.jpg"><br>
      CAMHDA301-20160725T210000Z, frame 5000</td>
    <td><img src="images/CAMHDA301-20160729T000000Z_6000.jpg"><br>
      CAMHDA301-20160729T000000Z, frame 6000</td>
  </tr>
</table>

(note, these are not exactly the same scene (yet)....)


Since the pre-programmed routine is nominally the same between instances,
the `p` positions should be equivalent between deployments.

More details on the evolution of CamHD can be found in the [CamHD Biography](CamHD_Biography.md)

<table>
  <tr><th>Deployment</th>
      <th>Starts at</th>
      <th>Ends at</th>
  </tr>
  <tr><td>`d2`</td><td>2015/11/18/CAMHDA301-20151118T000020Z (approx)</td><td>2016/07/25/CAMHDA301-20160725T210000Z</td></tr>
  <tr><td>`d3`</td><td>2016/07/29/CAMHDA301-20160729T000000Z</td><td>2017/06/14/CAMHDA301-20170614T231900^</td></tr>
  <tr><td>`d4`</td><td>2017/08/14/CAMHDA301-20170814T211500</td><td>2017/11/13/CAMHDA301-20171113T211500^^</td></tr>
  <tr><td>[`d5`](Deployment_d5.md)</td><td>2018/07/04/CAMHDA301-20180704T.....</td><td>_Ongoing_</td></tr>
</table>

^ Deployment `d3` was cut short by a growing ground fault in June of 2016.

^^ Deployment `d4` suffered from ground faults almost immediately.  The camera was run in a degraded condition with one light through 13 November 2017, then was powered off.  See the [CamHD Biography](CamHD_Biography.md)

In both cases, the _camera_ was stopped but the _recording_ was not.   This resulted in  sequence of videos containing ~12 minutes of black.   These videos are readily identifiable as the black frame compress relatively well, with the Quicktime files at ~550MB in sie (versus 14GB).

# Regions

<table>
  <tr>
  <th>Name</th>
  <th>Action before</th>
  <th>Deployment `d2`</th>
  <th>Deployment `d3`</th>
  <th>Deployment `d4`</th>
  </tr>

  <tr>
    <td>d?_p1_z0</td>
    <td/>
    <td> <img src="region_thumbs/d2_00000981.jpg"></td>
    <td> <img src="region_thumbs/d3_1656.jpg"></td>
    <td> <img src="region_thumbs/d4_1026.jpg"></td>
  </tr>

  <tr>
    <td>d?_p1_z1</td>
    <td>Zoom In</td>
    <td> <img src="region_thumbs/d2_00001297.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z0</td>
    <td>Zoom Out / Pan up (no break?)</td>
    <td> <img src="region_thumbs/d2_00002013.jpg"></td>
    <td> <img src="region_thumbs/d3_3131.jpg"></td>
    <td> <img src="region_thumbs/d4_2501.jpg"></td>
  </tr>

  <tr>
    <td>d?_p2_z0</td>
    <td>Pan Up/left</td>
    <td> <img src="region_thumbs/d2_00002522.jpg"></td>
    <td> <img src="region_thumbs/d3_3931.jpg"></td>
    <td> <img src="region_thumbs/d4_3311.jpg"></td>
  </tr>

  <tr>
    <td>d?_p2_z1</td>
    <td>Zoom in</td>
    <td> <img src="region_thumbs/d2_00003352.jpg"></td>
  </tr>

  <tr>
    <td>d?_p2_z2 (?)</td>
    <td>Zoom in</td>
    <td></td>
    <td> <img src="region_thumbs/d3_4526.jpg"></td>
  </tr>

  <tr>
    <td>d?_p2_z0</td>
    <td>Zoom out</td>
    <td> <img src="region_thumbs/d2_00004045.jpg"></td>
    <td> <img src="region_thumbs/d3_5386.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z0</td>
    <td>Pan down/right</td>
    <td> <img src="region_thumbs/d2_00004675.jpg"></td>
    <td> <img src="region_thumbs/d3_5911.jpg"></td>
    <td> <img src="region_thumbs/d4_5401.jpg"></td>
  </tr>

  <tr>
    <td>d?_p3_z0</td>
    <td>Pan up</td>
    <td> <img src="region_thumbs/d2_00005215.jpg"></td>
    <td> <img src="region_thumbs/d3_6411.jpg"></td>
    <td> <img src="region_thumbs/d4_5891.jpg"></td>
  </tr>

  <tr>
    <td>d?_p3_z1</td>
    <td>Zoom in</td>
    <td> <img src="region_thumbs/d2_00005670.jpg"></td>
    <td></td>
    <td> <img src="region_thumbs/d4_6351.jpg"></td>
  </tr>

  <tr>
    <td>d?_p3_z2</td>
    <td>Zoom in (further)</td>
    <td> <img src="region_thumbs/d2_00006191.jpg"></td>
    <td> <img src="region_thumbs/d3_7541.jpg"></td>
    <td> <img src="region_thumbs/d4_7036.jpg"></td>
  </tr>

  <tr>
    <td>d?_p3_z0</td>
    <td>Zoom out</td>
    <td> <img src="region_thumbs/d2_00007111.jpg"></td>
    <td> <img src="region_thumbs/d3_8691.jpg"></td>
    <td> <img src="region_thumbs/d4_7986.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z0</td>
    <td>Pan down</td>
    <td> <img src="region_thumbs/d2_00007515.jpg"></td>
    <td> <img src="region_thumbs/d3_9226.jpg"></td>
    <td> <img src="region_thumbs/d4_8521.jpg"></td>
  </tr>

  <tr>
    <td>d?_p4_z0</td>
    <td>Pan up/right</td>
    <td> <img src="region_thumbs/d2_00008115.jpg"></td>
    <td> <img src="region_thumbs/d3_9811.jpg"></td>
    <td> <img src="region_thumbs/d4_9096.jpg"></td>
  </tr>

  <tr>
    <td>d?_p4_z1</td>
    <td>Zoom in</td>
    <td> <img src="region_thumbs/d2_00008550.jpg"></td>
    <td> <img src="region_thumbs/d3_10296.jpg"></td>
    <td> <img src="region_thumbs/d4_9556.jpg"></td>
  </tr>

  <tr>
    <td>d?_p4_z2</td>
    <td>Zoom in (further)</td>
    <td> <img src="region_thumbs/d2_00009071.jpg"></td>
    <td> <img src="region_thumbs/d3_10971.jpg"></td>
    <td> <img src="region_thumbs/d4_10256.jpg"></td>
  </tr>

  <tr>
    <td>d?_p4_z0</td>
    <td>Zoom out</td>
    <td> <img src="region_thumbs/d2_00010005.jpg"></td>
    <td> <img src="region_thumbs/d3_11926.jpg"></td>
    <td> <img src="region_thumbs/d4_11221.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z0</td>
    <td>Pan down/left</td>
    <td> <img src="region_thumbs/d2_00010460.jpg"></td>
    <td> <img src="region_thumbs/d3_12456.jpg"></td>
    <td> <img src="region_thumbs/d4_11756.jpg"></td>
  </tr>

  <tr>
    <td>d?_p5_z0</td>
    <td>Pan right</td>
    <td> <img src="region_thumbs/d2_00010845.jpg"></td>
    <td> <img src="region_thumbs/d3_12961.jpg"></td>
    <td> <img src="region_thumbs/d4_12276.jpg"></td>
  </tr>



  <tr>
    <td>d?_p5_z1</td>
    <td>Zoom in</td>
    <td> <img src="region_thumbs/d2_00011335.jpg"></td>
    <td> <img src="region_thumbs/d3_13416.jpg"></td>
    <td> <img src="region_thumbs/d4_12756.jpg"></td>
  </tr>

  <tr>
    <td>d?_p5_z2</td>
    <td>Zoom in (further)</td>
    <td> <img src="region_thumbs/d2_00011881.jpg"></td>
    <td> <img src="region_thumbs/d3_14111.jpg"></td>
    <td> <img src="region_thumbs/d4_13416.jpg"></td>
  </tr>

  <tr>
    <td>d?_p5_z0</td>
    <td>Zoom out</td>
    <td> <img src="region_thumbs/d2_00012801.jpg"></td>
    <td> <img src="region_thumbs/d3_15041.jpg"></td>
    <td> <img src="region_thumbs/d4_14341.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z0</td>
    <td>Pan left</td>
    <td> <img src="region_thumbs/d2_00013137.jpg"></td>
    <td> <img src="region_thumbs/d3_15541.jpg"></td>
    <td> <img src="region_thumbs/d4_14831.jpg"></td>
  </tr>

  <tr>
    <td>d?_p6_z0</td>
    <td>Pan left</td>
    <td> <img src="region_thumbs/d2_00013601.jpg"></td>
    <td> <img src="region_thumbs/d3_15976.jpg"></td>
    <td> <img src="region_thumbs/d4_15296.jpg"></td>
  </tr>

  <tr>
    <td>d?_p6_z1</td>
    <td>Zoom in</td>
    <td> <img src="region_thumbs/d2_00014050.jpg"></td>
    <td> <img src="region_thumbs/d3_16426.jpg"></td>
    <td> <img src="region_thumbs/d4_15766.jpg"></td>
  </tr>

  <tr>
    <td>d?_p6_z2</td>
    <td>Zoom in (further)</td>
    <td> <img src="region_thumbs/d2_00014571.jpg"></td>
    <td> <img src="region_thumbs/d3_17096.jpg"></td>
    <td> <img src="region_thumbs/d4_16416.jpg"></td>
  </tr>

  <tr>
    <td>d?_p6_z0</td>
    <td>Zoom out</td>
    <td> <img src="region_thumbs/d2_00015491.jpg"></td>
    <td> <img src="region_thumbs/d3_18041.jpg"></td>
    <td> <img src="region_thumbs/d4_17336.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z0</td>
    <td>Pan right</td>
    <td> <img src="region_thumbs/d2_00015841.jpg"></td>
    <td> <img src="region_thumbs/d3_18536.jpg"></td>
    <td> <img src="region_thumbs/d4_17866.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z1</td>
    <td>Zoom in</td>
    <td> <img src="region_thumbs/d2_00016415.jpg"></td>
    <td> <img src="region_thumbs/d3_19096.jpg"></td>
    <td> <img src="region_thumbs/d4_18396.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z2</td>
    <td>Zoom in (further)</td>
    <td> <img src="region_thumbs/d2_00016961.jpg"></td>
    <td> <img src="region_thumbs/d3_19826.jpg"></td>
    <td> <img src="region_thumbs/d4_19126.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z0</td>
    <td>Zoom out</td>
    <td> <img src="region_thumbs/d2_00018001.jpg"></td>
    <td> <img src="region_thumbs/d3_20916.jpg"></td>
    <td> <img src="region_thumbs/d4_20216.jpg"></td>
  </tr>

  <tr>
    <td>d?_p7_z0</td>
    <td>Pan down</td>
    <td> <img src="region_thumbs/d2_00018725.jpg"></td>
    <td> <img src="region_thumbs/d3_21601.jpg"></td>
    <td> <img src="region_thumbs/d4_21031.jpg"></td>
  </tr>

  <tr>
    <td>d?_p7_z1</td>
    <td>Zoom in</td>
    <td> <img src="region_thumbs/d2_00019625.jpg"></td>
    <td> <img src="region_thumbs/d3_22446.jpg"></td>
    <td> <img src="region_thumbs/d4_21871.jpg"></td>
  </tr>

  <tr>
    <td>d?_p7_z0</td>
    <td>Zoom out</td>
    <td> <img src="region_thumbs/d2_00020475.jpg"></td>
    <td> <img src="region_thumbs/d3_23166.jpg"></td>
    <td> <img src="region_thumbs/d4_22466.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z0</td>
    <td>Pan up</td>
    <td> <img src="region_thumbs/d2_00021080.jpg"></td>
    <td> <img src="region_thumbs/d3_23671.jpg"></td>
    <td> <img src="region_thumbs/d4_22971.jpg"></td>
  </tr>

  <tr>
    <td>d?_p8_z0</td>
    <td>Pan right/down</td>
    <td> <img src="region_thumbs/d2_00021605.jpg"></td>
    <td> <img src="region_thumbs/d3_24156.jpg"></td>
    <td> <img src="region_thumbs/d4_23506.jpg"></td>
  </tr>

  <tr>
    <td>d?_p8_z1</td>
    <td>Zoom in</td>
    <td> <img src="region_thumbs/d2_00022205.jpg"></td>
    <td> <img src="region_thumbs/d3_24966.jpg"></td>
    <td> <img src="region_thumbs/d4_24266.jpg"></td>
  </tr>

  <tr>
    <td>d?_p8_z0</td>
    <td>Zoom out</td>
    <td> <img src="region_thumbs/d2_00023051.jpg"></td>
    <td> <img src="region_thumbs/d3_25791.jpg"></td>
    <td> <img src="region_thumbs/d4_25091.jpg"></td>
  </tr>

  <tr>
    <td>d?_p0_z0</td>
    <td>Pan up/left</td>
    <td> <img src="region_thumbs/d2_00023615.jpg"></td>
    <td> <img src="region_thumbs/d3_26336.jpg"></td>
    <td> <img src="region_thumbs/d4_25636.jpg"></td>
  </tr>

  <tr>
    <td>d?_p1_z0</td>
    <td>Pan down</td>
    <td> <img src="region_thumbs/d2_00024151.jpg"></td>
    <td> <img src="region_thumbs/d3_26851.jpg"></td>
    <td> <img src="region_thumbs/d4_26186.jpg"></td>
  </tr>

</table>
