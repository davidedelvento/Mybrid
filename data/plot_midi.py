#!/bin/env python3

import argparse
from mido import MidiFile

parser = argparse.ArgumentParser()
parser.add_argument("file")
args = parser.parse_args()

print('content of file', args.file, '(no plot yet)')

for msg in MidiFile(args.file).play():
        print(msg)
