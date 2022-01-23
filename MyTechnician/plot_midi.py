#!/usr/bin/env python3

import argparse
import mido
from mido import Message, MidiFile, MidiTrack
from cdefine import CDefine

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--save", help="Save data in a file named <SAVE> for later plotting")
parser.add_argument("-l", "--load", help="Load data in a file named <LOAD> for immediate plotting")
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()

if ((args.save is     None and args.load is     None) or
    (args.save is not None and args.load is not None)):
    parser.error("Must select either --save or --load")

defined = CDefine('../RaspberryPiPico/My_MIDI_constants.h')

if args.load:
    import matplotlib.pyplot as plt      # importing here to allow saving without GTK
    x = []
    y = []
    i = 0

    for msg in MidiFile(args.load).play():
        if msg.type == 'sysex':
            if (msg.data[0] == defined.MIDI_VENDOR and
                msg.data[1] <= defined.MIDI_MAX_ADC_VALUE):

                x.append(i)
                i = i + 1
                y.append(msg.data[2] + msg.data[1] * 128)

    fig, ax = plt.subplots()
    ax.plot(x,y)
    ax.set_ylim(0, 4096);
    plt.show()

if args.save:
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    pico=mido.get_input_names()[1]
    if args.verbose:
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
