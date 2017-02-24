

class atomic(object):
    """Something"""



class Atomic(object):
    def __enter__(self):
        print("Atomic enter")
        return self._baseobject
    def __exit__(self, exc_type, exc_value, traceback):
        print("Atomic exit")
    def __init__(self, baseobject):
        print("Atomic init")
        self._baseobject = baseobject