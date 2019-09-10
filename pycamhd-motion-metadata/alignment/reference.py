"""
Classes used to determine which previous frame a certain frame should align against.
Should of created a parent class for good practice, though this is only used in one place.

counter refers to the frame number being processed
ref refers to the frame number of the data returned with get(); returns counter if get() returned None

get() retrieves data for a reference frame; further calls will return backup references, with None indicating no more frames
save() saves the information for a particular frame, and updates everything accordingly
reset() resets the get() function; unused
"""

"""
Always directs to the previous frame.
"""
class RelativeReference:
    def __init__(self):
        self.store = None
        self.counter = 0
        self.ref = 0
        self.tried = False

    def get(self):
        if self.tried:
            return None
        else:
            self.tried = True
            return self.store

    def save(self, data):
        self.store = data
        self.counter+=1
        self.ref = self.counter-1
        self.reset()

    def reset(self):
        self.tried = False
        self.ref = self.counter-1

"""
Always directs to the first frame.
"""
class AbsoluteReference:
    def __init__(self):
        self.store = None
        self.tried = False
        self.counter = 0
        self.ref = 0

    def get(self):
        if self.tried:
            return None
        else:
            self.tried = True
            return self.store

    def save(self, data):
        if self.store is None:
            self.store = data
        self.counter += 1
        self.reset()

    def reset(self):
        self.tried = False
"""
Points according to the following algorithm:

For each frame, a subtraction value is set to equal the frame's least significant set bit.
The frame then uses the image [subtraction value] frames before it.
If the alignment fails, then the subtraction value is halved. If the subtraction value reaches 0, then the current frame will not be aligned.
"""
class BinaryReference:
    def __init__(self):
        self.counter = 0
        self.storage = []
        self.sub = 0
        self.ref = 0

    def get(self):
        self.ref = self.counter - self.sub
        if self.sub == 0:
            return None
        
        index = self.bl(self.lsb(self.ref))

        self.sub = int(self.sub/2)
        return self.storage[index]

    def reset(self):
        self.sub = self.lsb(self.counter)
        self.ref = self.counter - self.sub

    def save(self, data):
        index = self.bl(self.lsb(self.counter))
        if len(self.storage)<=index:
            self.storage.append(data)
        else:
            self.storage[index] = data
        self.counter += 1
        self.reset()
    
    def lsb(self,x):
        assert(type(x) is int)
        return (1 + (x ^ (x-1))) >> 1

    def bl(self,x):
        return x.bit_length()

if __name__=="__main__":
    br = BinaryReference()
    for i in range(0,100):
        ref = 0
        while(ref!=None):
            ref = br.get()
            print(i, ref)
        br.save(i)