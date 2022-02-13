#!/usr/bin/env python3

import argparse
import math
import bz2
import statistics

parser = argparse.ArgumentParser(description="Parser of High Resolution binary (not MIDI) files")
parser.add_argument("filename", help="Load <FILENAME> for plotting, analysis or dumping in a text file")

action = parser.add_mutually_exclusive_group(required=True)
action.add_argument("-d", "--dump", help="Dump the content of FILENAME on the terminal", action="store_true")
action.add_argument("-p", "--plot", help="Plot the content of FILENAME with matplotlib", action="store_true")
action.add_argument("-m", "--midi-plot", help="Pretend to a RPi Pico: plot MIDI velocities", action="store_true")

file_format = parser.add_mutually_exclusive_group(required=True)
file_format.add_argument("-12", help="Force two 12-bit samples, 1-ADC channel per timestamp",
                         dest="bits_12", action="store_true")
file_format.add_argument("-8", help="Force three 8-bit samples, 3-ADC channels per timestamp",
                         dest="bits_8", action="store_true")
args = parser.parse_args()

IDLE = 0
FLY = 1
SOUND = 2


class regulation():
    def __init__(self, range='medium', bits=12):
        # see https://pianoclack.com/forum/d/289-scanning-speed-and-velocity-mapping-of-cybrid/3
        if range == 'large':
            self.LET_OFF = 3950
            self.VEL_SLOPE = 70
            self.VEL_CONST = 70 + self.VEL_SLOPE * math.log10(2000)      # about 506
        elif range == 'medium':
            self.LET_OFF = 3000
            self.VEL_SLOPE = 40
            self.VEL_CONST = 40 + self.VEL_SLOPE * math.log10(1000)      # about 155
        elif range == 'small':
            self.LET_OFF = 2700
            self.VEL_SLOPE = 40
            self.VEL_CONST = 40 + self.VEL_SLOPE * math.log10(1000)
        else:
            raise ValueError("The range argument must be 'large', 'medium' or 'small'")

        self.STRIKE = 2600
        self.DROP = 4080
        self.sg = False

        if bits == 8:
            self.LET_OFF = self.LET_OFF / 16 - 1       # 12 to 8 bit ratio
            self.STRIKE = self.STRIKE / 16 - 1
            self.DROP = self.DROP / 16 - 1

    def set_sav_gol(self, window_len, position):
        self.sg = True
        self.coeffs = savgol_coeffs(window_len, 2, deriv=1, use='dot', delta=0.01, pos=position)
        self.start_index = int((window_len + 1) / 2)
        if position is not None:
            self.start_index = int((window_len + position + 1) / 2)

    def savgol_midi(self, value, index):
        velocity = 0
        for (i, c) in enumerate(self.coeffs):
            velocity += c * value[index - self.start_index + i]
        return 80


def midi_vel(delta_time, r):
    return int(r.VEL_CONST - r.VEL_SLOPE * math.log10(delta_time))


def parse_2_12(b0, b1, b2):
    d2 = b0 + ((b1 & 0x0F) << 8)
    d1 = (b2 << 4) + ((b1 & 0xF0) >> 4)
    return d1, d2


def interpolate_time(time):
    time_interp = []
    previous_t = time[0]
    for t in time:
        time_interp.append((t + previous_t) / 2)
        time_interp.append(t)
        previous_t = t
    return time_interp


def print_stats(time):
    delta_t = [t1 - t2 for (t2, t1) in zip(time[1:], time[2:])]
    avg = statistics.mean(delta_t)
    std = statistics.stdev(delta_t)
    print("DELTA t statistics")
    print("avg =", avg, "std_dev =", std, "max =", max(delta_t), "min =", min(delta_t))
    print("median =", statistics.median(delta_t))
    try:
        print("deciles =", statistics.quantiles(delta_t, n=10))
        print("percentiles =", statistics.quantiles(delta_t, n=100))
        print("multimode =", statistics.multimode(delta_t))
    except AttributeError:
        print("mode =", statistics.mode(delta_t))


def plot_midi_all_regulations(data, time, bits, label="", options=['small', 'medium', 'large']):
    prefix = ""
    if label != "":
        prefix = label + " "
    for (gg, range) in enumerate(options):
        lw = gg + 1
        ls = ['-', '--', '-.', ':'][gg % 4]
        r = regulation(range=range, bits=bits)
        midi_data, time_data = parse_ADC_data(data, time, r)
        ax.plot(time_data, midi_data, label=prefix+"comparator: " + range, linestyle=ls, linewidth=lw)
    r = regulation(bits=bits)
    for window_len in [13, 23]:
        for position in ['center', 'end']:
            suffix = "sg (" + str(window_len) + ", " + position + ")"
            if position == 'center':
                position = None
            else:
                position = window_len - 1
            r.set_sav_gol(window_len, position)
            midi_data, time_data = parse_ADC_data(data, time, r)
            ax.plot(time_data, midi_data, label=prefix+ suffix, linestyle=ls, linewidth=lw)


def finish_adc_plot(bits):
    ax.set_xlabel('time (us)')
    ax.set_ylabel('Raw ADC value')
    for range in ['large', 'medium', 'small']:
        r = regulation(range=range, bits=bits)
        plt.axhline(y=r.LET_OFF, linestyle='-', color="green", label="let off - " + range)

    r = regulation()
    plt.axhline(y=r.STRIKE, linestyle='-', color="yellow", label="strike")
    plt.axhline(y=r.DROP, linestyle='-', color="red", label="drop")

    ax.legend()
    plt.show()


def parse_ADC_data(d, t, r):
    status = IDLE
    start_time = 0
    midi_data = []
    time_data = []
    for (i, dist) in enumerate(d):
        if status == IDLE:
            if dist < r.LET_OFF:
                status = FLY
                start_time = t[i]
        elif status == FLY:
            if dist < r.STRIKE:
                status = SOUND
                if not r.sg:
                    m = midi_vel(t[i] - start_time, r)
                else:
                    m = r.savgol_midi(d, i)
                if m == 0:
                    print("warning, apparent note-off data")
                midi_data.append(0)                      # making the plot
                time_data.append(t[i-1] / 1000000)       # easier to read
                midi_data.append(m)
                time_data.append(t[i] / 1000000)         # us
            elif dist > r.DROP:
                status = IDLE
        elif status == SOUND:
            if dist > r.DROP:
                status = IDLE
                midi_data.append(0)
                time_data.append(t[i] / 1000000)
    return midi_data, time_data


if args.plot or args.midi_plot:
    import matplotlib.pyplot as plt      # importing here to allow saving without GTK
    from scipy.signal import savgol_coeffs

if args.bits_12:
    data = []
    time = []

    with bz2.open(args.filename, mode='rb') as file:
        b = file.read()
        old_time = b[3]
        increment = 256
        for i in range(0, len(b), 4):
            d1, d2 = parse_2_12(b[i], b[i+1], b[i+2])
            data.append(d1)
            data.append(d2)
            curr_time = b[i+3]
            if (curr_time < old_time):
                curr_time += increment
                if (curr_time < old_time):
                    increment += 256
                    curr_time += 256
            time.append(curr_time)
            old_time = curr_time

    if args.dump:
        print("Time\tadc_at_time\tadc_at_time_plus")
        for i in range(len(time)):
            print(time[i], data[2*i], "", data[2*i+1], sep="\t")
    elif args.plot:
        time_interp = interpolate_time(time)
        fig, ax = plt.subplots()
        ax.plot(time_interp, data, label="ADC")
        ax.set_ylim(0, 4096)
        finish_adc_plot(bits=12)
    elif args.midi_plot:
        time_interp = interpolate_time(time)
        print_stats(time_interp)
        fig, ax = plt.subplots()
        plot_midi_all_regulations(data, time_interp, bits=12)

        ax.set_ylim(-10, 140)
        ax.set_xlabel('time (s)')
        ax.set_ylabel('MIDI value')
        ax.legend()
        plt.show()

elif args.bits_8:
    data1 = []
    data2 = []
    data3 = []
    time = []

    with bz2.open(args.filename, mode='rb') as file:
        b = file.read()
        old_time = b[3]
        increment = 256
        for i in range(0, len(b), 4):
            data1.append(b[i])
            data2.append(b[i+1])
            data3.append(b[i+2])
            curr_time = b[i+3]
            if (curr_time < old_time):
                curr_time += increment
                if (curr_time < old_time):
                    increment += 256
                    curr_time += 256
            time.append(curr_time)
            old_time = curr_time

    if args.dump:
        print("Time\tadc1\tadc2\tadc3")
        for i in range(len(time)):
            print(time[i], data1[i], data2[i], data3[i], sep="\t")
    elif args.plot:
        fig, ax = plt.subplots()
        ax.plot(time, data1, label="ADC1")
        ax.plot(time, data2, label="ADC2")
        ax.plot(time, data3, label="ADC3")
        ax.set_ylim(0, 256)
        finish_adc_plot(bits=8)
    elif args.midi_plot:
        fig, ax = plt.subplots()
        print_stats(time)
        plot_midi_all_regulations(data1, time, bits=8, label="note 1")
        plot_midi_all_regulations(data2, time, bits=8, label="note 2")
        plot_midi_all_regulations(data3, time, bits=8, label="note 3")
        ax.set_ylim(-10, 140)
        ax.set_xlabel('time (s)')
        ax.set_ylabel('MIDI value')
        ax.legend()
        plt.show()
