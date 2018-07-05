# Technical Overview

At present, CamHD is installed for a 1-year operational cycle, with the CamHD instances swapped during the Operations and Maintenance (O&M) cruise which occurs every summer.


# Designations

There are two instances of CamHD, designated `P1` and `P2` (corresponding to serial numbers 1 and 2).    Spares exist for the electronics and pressure vessels -- but not the physical structure including the triangular frame and floatation -- to construct a third example.

While there has only been one CamHD design, it has evolved over its life, resulting in multiple revisions:

* `rev0` -- Original design.   Impulse rubber-molded connectors throughout.
* `rev1` -- Replacement of Impulse rubber-molded connectors with Subconn.   Non-rubber molded connectors not changed:    Impulse micro-connector on IMU end of IMU cabling, hybrid coax+power connector to camera, all ODI cabling.
* `rev2` -- Modification of power boards to isolate CamHD DC ground from cabled array system -187.5V

# History

<table>
  <tr>
    <th>Deployment</th>
    <th>Instance</th>
    <th>Deployed</th>
    <th>Recovered</th>
    <th>Notes</th>
  </tr>
  <tr>
    <td>`d1` and `d2`</td>
    <td>P2 _rev0_</td>
    <td>Summer 2014</td>
    <td>July 25, 2016</td>
    <td>This is one continuous deployment.   `d1`  designates _ad hoc_ data taken before the OOI CI was fully functional.   `d2` designates regularly scheduled data taken after the CI data distribution system was up.</td>
  </tr>
  <tr>
    <td>`d3`</td>
    <td>P1 _rev1_</td>
    <td>July 29, 2016</td>
    <td>August xx, 2017</td>
    <td>Unit started to show ground faults in ~May and was finally powered off on June 14 </td>
  </tr>
  <tr>
    <td>`d4`</td>
    <td>P2 _rev1_</td>
    <td>August 14 2017</td>
    <td>July 4, 2018</td>
    <td>Unit suffered from ground faults within first few weeks of deployment.  Was able to limp along by turning off one light.   Unit powered down 13 Nov 2017.</td>
  </tr>
  <tr>
    <td>`d5`</td>
    <td>P1 _rev2_</td>
    <td>July 4, 2018</td>
    <td>ongoing</td>
    <td>First deployment of _rev2_ configuration.</td>
  </tr>
</table>

Unit P2 was installed in the summer of 2014, before the formal commissioning of the Cabled Array, and was in place for two years, starting with approx. 16 months of quiescence (July 2014 – November 2015).   Upon the formal commissioning of the CA in November/December 2015, CamHD started its regular sampling routine.

The deployment of P2 coincided with the switch from Impulse to Subconn cabling across much of the OOI system.   Replacement cabling was procured from Subconn in the spring of 2015.    P1 was recabled immediately.  P2 was recabled during the 2016-2017 season.

Unit P2 was recovered and replaced by P1 during the Summer 2016 O&M cruise.
Unit P1 was deployed for from summer 2016-summer 2017.   In ~May-June of 2017 (~10-11 months in operation), it exhibited a steadily worsening ground fault which resulted in the instrument being turned off on June 14 2017 to prevent catastrophic failure.

P1 was recovered during the 2017 O&M cruise and replaced with a refurbished P2.  P2 started to exhibit a ground fault almost immediately.   It ran for a period with a single light, then was turned off completely in October 2017.   The CamHD system was off-line from Oct 2017 – July 2018.

During the 2017-2018 refurbishment, P1 was installed in the OSB test tank where it developed a ground fault within a matter of days.  A full refurbishment report can be found [here](docs/2018 CamHD Refurbishment Report rev1.pdf)
