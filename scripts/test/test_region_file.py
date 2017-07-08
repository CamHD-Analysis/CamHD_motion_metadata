

import region_analysis as ra

TEST_REGION_FILE = "../RS03ASHS/PN03B/06-CAMHDA301/2016/03/01/CAMHDA301-20160301T000000Z_optical_flow_regions.json"


def test_constructor():
    regions = ra.RegionFile(TEST_REGION_FILE)

    assert regions.basename == "CAMHDA301-20160301T000000Z"
    assert regions.mov == "/RS03ASHS/PN03B/06-CAMHDA301/2016/03/01/CAMHDA301-20160301T000000Z.mov"

    # These are known apriori and may change
    assert len(regions.regions) == 87
    assert len(regions.static_regions) == 44
