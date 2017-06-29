

import json
from os import path


class Region:
    def __init__(self, json):
        self.json = json

        self.type = json["type"] if "type" in json else None
        self.sceneTag = json["sceneTag"] if "sceneTag" in json else None

    @property
    def static(self):
        return self.type == "static"

class RegionFile:

    def __init__(self, filename):
        self.filename = filename

        with open(filename) as f:
            self.json = json.load(f)

        if "regions" not in self.json:
            raise Exception("%s doesn't appear to be a regions file" % filename)

        self.mov = self.json['movie']['URL']
        self.basename = path.splitext(path.basename(self.mov))[0]

        self.regions = [Region(j) for j in self.json["regions"]]

    @property
    def static_regions(self):
        return [r for r in self.regions if r.static]
