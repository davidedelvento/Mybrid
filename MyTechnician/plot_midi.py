#!/usr/bin/env python3

import argparse
from mido import MidiFile
import matplotlib.pyplot as plt
from cdefine import CDefine

parser = argparse.ArgumentParser()
parser.add_argument("file")
args = parser.parse_args()

defined = CDefine('../RaspberryPiPico/My_MIDI_constants.h')

x = []
y = []
i = 0

for msg in MidiFile(args.file).play():
    if msg.type is 'sysex':
        if (msg.data[0] == defined.MIDI_VENDOR and
            msg.data[1] <= defined.MIDI_MAX_ADC_VALUE):

            x.append(i)
            i = i + 1
            y.append(msg.data[2] + msg.data[1] * 128)

fig, ax = plt.subplots()
ax.plot(x,y)
ax.set_ylim(0, 4096);
plt.show()
