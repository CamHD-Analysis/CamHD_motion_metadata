

import json
from os import path


class Region:
    def __init__(self, json):
        self.json = json

        self.type = json["type"] if "type" in json else None
        self.scene_tag = json["sceneTag"] if "sceneTag" in json else None

    @property
    def static(self):
        return self.type == "static"


class RegionFile:

    def __init__(self, json):
        self.json = json

        self.mov = self.json['movie']['URL']
        self.basename = path.splitext(path.basename(self.mov))[0]

        self.regions = [Region(j) for j in self.json["regions"]]

    def save_json(self, outfile):
        with open(outfile, 'w') as out:
            json.dump(self.json, out, indent=4)

        def is_classified(self):
            for r in self.static_regions:
                if r.sceneTag is None:
                    return False

            return True

    @classmethod
    def load(cls, filename):

        with open(filename) as f:
            j = json.load(f)

        if "regions" not in j:
            raise Exception("%s doesn't appear to be "
                            "a regions file" % filename)

        return RegionFile(j)

    @classmethod
    def from_optical_flow(cls, oflow, regions):
        return RegionFile({'movie': oflow.json['movie'],
                           'contents': {'regions': '1.1'},
                           'versions': {},
                           'regions': regions,
                           'depends': {'opticalFlow': {oflow.path(): oflow.git_rev()}}
                           })

    @property
    def static_regions(self):
        return [r for r in self.regions if r.static]
