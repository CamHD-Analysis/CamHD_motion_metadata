

import json
import random
from os import path


class Region:
    def __init__(self, json):
        self.json = json

    @property
    def static(self):
        return self.type == "static"

    def draw(self, range=(0.1, 0.9)):
        ''' Should be better parameterized '''
        return frame_at( random(range[0], range[1]))

    def frame_at(self, pct):
        return round(self.start_frame + pct * (self.end_frame-self.start_frame))

    @property
    def scene_tag(self):
        return self.json["sceneTag"] if "sceneTag" in self.json else None

    @property
    def unknown(self):
        return self.scene_tag() == 'unknown'

    @property
    def type(self):
        return self.json["type"] if "type" in self.json else None

    @property
    def start_frame(self):
        return self.json['startFrame']

    @property
    def end_frame(self):
        return self.json['endFrame']

    def set_scene_tag(self, scene_tag, inferred_by=None):
        self.json['sceneTag'] = scene_tag
        if 'sceneTagMeta' not in self.json:
            self.json['sceneTagMeta'] = {}
        if inferred_by:
            self.json['sceneTagMeta']['inferredBy'] = inferred_by


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
            for r in self.static_regions():
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

    def static_regions(self, scene_tag=None):
        if scene_tag is None:
            return [r for r in self.regions if r.static]
        else:
            return [r for r in self.regions if r.static and r.scene_tag == scene_tag]

    def static_at( self, i ):
        return self.static_regions()[i]
