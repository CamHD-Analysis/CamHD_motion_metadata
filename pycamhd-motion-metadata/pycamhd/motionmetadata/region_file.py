

import json
import random
import logging
from os import path

import re
import datetime

class Region:
    def __init__(self, json):
        self.json = json

    @property
    def static(self):
        return self.type == "static"

    def draw(self, range=(0.1, 0.9)):
        ''' Should be better parameterized '''
        return self.frame_at(random.uniform(range[0], range[1]))

    def frame_at(self, pct):
        return round(self.start_frame + pct * (self.end_frame-self.start_frame))

    @property
    def scene_tag(self):
        return self.json["sceneTag"] if "sceneTag" in self.json else None

    @property
    def unknown(self):
        return self.scene_tag == 'unknown'

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

    def datetime(self):

        prog = re.compile("CAMHDA301-(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})")
        match = re.match(prog, self.basename)

        if match:
            dt = datetime.datetime(int(match.group(1)), int(match.group(2)),
                                     int(match.group(3)), int(match.group(4)),
                                     int(match.group(5)), int(match.group(6)))
            return dt

        return None


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

    def regions(self):
        return [Region(j) for j in self.json["regions"]]

    def region_at(self, i):
        return self.regions()[i]

    def static_regions(self, scene_tag=None):
        if scene_tag is None:
            return [r for r in self.regions() if r.static]
        else:
            return [r for r in self.regions() if r.static and r.scene_tag == scene_tag]

    def static_at( self, i ):
        return self.static_regions()[i]


    def merge_regions(self, i, j):
        self.json["regions"][j]["startFrame"] = self.json["regions"][i]["startFrame"]
        del self.json["regions"][i:j]


    def squash_gaps( self, delta = 20 ):

        i = 1
        while i < len(self.regions())-1:
            dt = self.region_at(i).end_frame - self.region_at(i).start_frame

            if dt <= delta:
                logging.info("Region %d from %d to %d is only %d long, squashing" % (i, self.region_at(i).start_frame, self.region_at(i).end_frame, dt))
                self.merge_regions( i-1, i+1 )
            else:
                i += 1


    def squash_scene_tag_sandwiches( self, delta = 20):

        i = 0
        while i < len(self.regions())-1:
            if self.region_at(i).scene_tag == None:
                i += 1
                continue

            for j in range(i+1, len(self.regions())):
                if self.region_at(i).scene_tag == self.region_at(j).scene_tag:
                    break;

            if j < len(self.regions()):
                dt = self.region_at(j).start_frame - self.region_at(i).end_frame

                logging.info("Examining gap of %d between %d and %d of type %s"
                             % (dt, self.region_at(i).end_frame,
                                self.region_at(j).start_frame,
                                self.region_at(j).scene_tag))
                if dt <= delta:
                    logging.info("Merging regions %d and %d" % (i, j))
                    self.merge_regions(i,j)
            else:
                i += 1
