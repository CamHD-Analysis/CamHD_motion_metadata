

import region_analysis as ra

TEST_REGION_FILE = "../RS03ASHS/PN03B/06-CAMHDA301/2016/03/01/CAMHDA301-20160301T030000Z_optical_flow_regions.json"


def test_constructor():
    regions = ra.RegionFile.load(TEST_REGION_FILE)

    assert regions.basename == "CAMHDA301-20160301T030000Z"
    assert regions.mov == "/RS03ASHS/PN03B/06-CAMHDA301/2016/03/01/CAMHDA301-20160301T030000Z.mov"

    # These are known apriori and may change
    assert len(regions.regions()) == 77
    assert len(regions.static_regions()) == 39


def test_datetime():

    regions = ra.RegionFile.load(TEST_REGION_FILE)

    date = regions.datetime()

    assert date
    assert date.year == 2016
    assert date.month == 3
    assert date.day == 1
    assert date.hour == 3
    assert date.minute == 0
    assert date.second == 0
