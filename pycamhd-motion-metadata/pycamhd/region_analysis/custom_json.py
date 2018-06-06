

import collections

def autodict():
    return collections.defaultdict(autodict)
