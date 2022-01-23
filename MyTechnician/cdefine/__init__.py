
# Typical use
#from cdefine import CDefine
#
#defined = CDefine('bla.h')
#defined.MIDI_VENDOR


class CDefine:
    def __init__(self, include_file):
        with open(include_file) as f:
            for line in f:
                self.parse(line.strip())

    def parse(self, line):
        if line.startswith('#define'):
            define, name, value, *rest = line.split()
            setattr(self, name, int(value, 16))
