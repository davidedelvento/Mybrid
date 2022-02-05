#!/usr/bin/env python3

import argparse
import mytechnician

parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Load <FILENAME> for plotting, analysis or dumping in a text file")
action = parser.add_mutually_exclusive_group(required=True)
action.add_argument("-d", "--dump", help="Dump the content of FILENAME on the terminal", action="store_true")
action.add_argument("-p", "--plot", help="Plot the content of FILENAME with matplotlib", action="store_true")
action.add_argument("-s", "--stat", help="Print summary statistics about FILENAME", action="store_true")
action.add_argument("-a", "--analysis", help="Plot analysis for MIDI velocity from ADC dump", action="store_true")
parser.add_argument("--ignore-midi-time", help="Use the ADC values sequentially, disregarding MIDI time", action="store_true")
parser.add_argument("-q", "--quiet", help="Do not report housekeeping messages", action="store_true")
args = parser.parse_args()

mt = mytechnician.mt()


def x_and_firstnote(old_x, yi):
    first_note = False
    for note_n in yi:
        if not first_note:
            first_note = note_n

    new_x = old_x

    if args.ignore_midi_time:
        xi = []
        for i, adc_v in enumerate(yi[first_note]):
            xi.append(i)
        new_x = xi

    return new_x, first_note


def plot():
    import matplotlib.pyplot as plt      # importing here to allow saving without GTK
    import numpy as np
    xi, yi = mt.parse_stats(args.filename, quiet=args.quiet)
    x, first_note = x_and_firstnote(xi, yi)
    x = [item if item != "N/A" else np.nan for item in x]

    fig, ax = plt.subplots()
    for note in yi:
        yi[note] = [item if item != "N/A" else np.nan for item in yi[note]]
        ax.plot(        x,          # NOQA -- I like this indentation better
                 yi[note],          # NOQA
                label="MIDI note " + str(note))

    ax.set_ylim(0, 4096)
    ax.set_xlabel('time (s)')
    ax.set_ylabel('Raw ADC value')
    ax.legend()
    plt.show()


def dump():
    xi, yi = mt.parse_stats(args.filename, quiet=args.quiet)

    if args.ignore_midi_time:
        print("Time_(packet_cnt)", end="\t")
    else:
        print("Time_(s)", end="\t")

    for note_n in yi:
        print("ADC_value_for_MIDI_note_", note_n, sep="", end="\t")
    print()

    xi, first_note = x_and_firstnote(xi, yi)

    for (i, x) in enumerate(xi):
        print(x, end="\t")
        for note_n in yi:
            try:
                print(yi[note_n][i], end="\t")
            except IndexError:
                print("N/A", end="\t")          # TODO piling them up at the end, but they can be lost anywhere

        print()


if args.stat:
    mt.parse_stats(args.filename)
elif args.plot:
    plot()
elif args.dump:
    dump()
else:
    print("Nothing to do yet")
