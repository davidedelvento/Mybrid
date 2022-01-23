#!/usr/bin/env python3

import mido, argparse
from mido import Message, MidiFile, MidiTrack

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--save", help="Save data in a file named SAVE for later plotting", required=True)
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()

mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)

pico=mido.get_input_names()[1]
print("Trying to open", pico)

with mido.open_input(pico) as inport:
    print(pico, "opened, waiting for messages, CTRL-C to stop and save")
    try:
      for msg in inport:
          track.append(msg)
          if args.verbose:
              print(msg)
    except KeyboardInterrupt:
      pass
        
mid.save(args.save)
print(args.save, "saved")
