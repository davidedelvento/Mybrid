#!/usr/bin/env python3

import mido
from mido import Message, MidiFile, MidiTrack
from cdefine import CDefine

import threading
import time
import sys
import bz2
import statistics
from collections import defaultdict

pico_in  = mido.get_input_names()[1]           # NOQA -- I like this indentation better
pico_out = mido.get_output_names()[1]
defined = CDefine('../RaspberryPiPico/My_MIDI_constants.h')

midi_strings = defined.__dict__
midi_values = {}
for k in defined.__dict__.keys():
    value = defined.__dict__[k]
    if value in midi_values:
        print("Warning, duplicated value", value, "for", midi_values[value], "and", k, file=sys.stderr)
    midi_values[defined.__dict__[k]] = k


class mt:
    def _previous_not_NA(self, mylist):
        previous = "N/A"
        i = 0
        while (previous == "N/A"):
            i = i + 1
            previous = mylist[-i] if (len(mylist) > i - 1) else 0
        return previous

    def _count_missing(self, all_packets):
        n_missing_packets = all_packets.count("N/A")
        n_present_packets = len(all_packets) - n_missing_packets
        return n_missing_packets, n_present_packets

    def parse_stats(self, filename, quiet=False):
        adc_packets = defaultdict(lambda: list())
        rtc_packets = []
        n_junk_packets = 0
        iter_per_ms = defaultdict(lambda: list())
        n_overflow_iter_per_ms = defaultdict(lambda: 0)
        roundtrip_time = []
        notes_on = defaultdict(lambda: 0)
        velocities_on = defaultdict(lambda: 0)
        notes_off = defaultdict(lambda: 0)
        velocities_off = defaultdict(lambda: 0)
        if not quiet: print()                    # NOQA -- simple and clear enough

        previous_packet = None  # Check if ADC and RTC packets alternate
        for msg in MidiFile(file=bz2.open(filename, 'rb')).play():
            if msg.type == 'note_on':
                notes_on[msg.note] += 1
                velocities_on[msg.note] += msg.velocity
                continue
            if msg.type == 'note_off':
                notes_off[msg.note] += 1
                velocities_off[msg.note] += msg.velocity
                continue
            if msg.type != 'sysex':
                print("Warning, not dealing with", msg.type, file=sys.stderr)
                continue
            try:
                if msg.data[0] != defined.MIDI_VENDOR:
                    print("Warning, probable message corruption", msg, file=sys.stderr)
                    continue
                if msg.data[1] > defined.MIDI_MAX_ADC_VALUE:
                    if msg.data[1] == defined.MIDI_RTC:
                        curr_time = (msg.data[2] * 128 + msg.data[3]) / 1000000   # us
                        old_time = self._previous_not_NA(rtc_packets)
                        while (curr_time < old_time):
                            curr_time += 16384 / 1000000                          # us
                        rtc_packets.append(curr_time)
                        if previous_packet == defined.MIDI_RTC:
                            # TODO make sure N_ADC packets not just one
                            for key in adc_packets:
                                adc_packets[key].append("N/A")
                        previous_packet = defined.MIDI_RTC
                    elif msg.data[1] == defined.MIDI_ITER_PER_MS:
                        if msg.data[2] == msg.data[3] and msg.data[2] == 127:
                            n_junk_packets += 1
                            continue
                        if msg.data[3] == 127:
                            n_overflow_iter_per_ms[msg.data[2]] += 1
                            continue
                        iter_per_ms[msg.data[2]].append(msg.data[3])
                    elif msg.data[1] == defined.MIDI_ROUNDTRIP_TIME_uS:
                        roundtrip_time.append(msg.data[2] * 128 + msg.data[3])
# MIDI_REGULATE
# MIDI_CONTINUE_REGULATION
# MIDI_DUMP_REGULATION
# INIT_PICO
# MIDI_NO_SUCH_NOTE
# MIDI_ERROR
#   TOO_MANY_PICOS
#   EXPECTING_INIT
#   TOO_MANY_PACKETS
                    else:
                        print("Warning, not counting ", end="", file=sys.stderr)
                        self.pretty_print(msg.data, target=sys.stderr)
                else:
                    if previous_packet == defined.MIDI_MAX_ADC_VALUE:
                        # TODO count up to N_ADC packets to save b/w
                        rtc_packets.append("N/A")
                    adc_packets[msg.data[3]].append(msg.data[1] * 128 + msg.data[2])
                    previous_packet = defined.MIDI_MAX_ADC_VALUE
            except IndexError:
                print("Warning, corrupted packet ", end="", file=sys.stderr)
                self.pretty_print(msg.data, target=sys.stderr)

        if not quiet:
            n_adc_missing_packets = 0
            n_adc_present_packets = 0
            for i in adc_packets:
                miss, pres = self._count_missing(adc_packets[i])
                n_adc_missing_packets += miss
                n_adc_present_packets += pres

            n_rtc_missing_packets, n_rtc_present_packets = self._count_missing(rtc_packets)

            print()
            print("Number of       ADC      dump    packets", n_adc_present_packets)
            print("Number of known ADC      missing packets", n_adc_missing_packets)
            print("Number of       MIDI_RTC         packets", n_rtc_present_packets)
            print("Number of known MIDI_RTC missing packets", n_rtc_missing_packets)
            print("Number of startup  packets", n_junk_packets)
            for pico in iter_per_ms:
                if len(iter_per_ms[pico]) > 0:
                    avg = statistics.mean(iter_per_ms[pico])
                    std = statistics.stdev(iter_per_ms[pico])
                else:
                    avg = "N/A"
                    std = "N/A"
                print("ITER_PER_MS for pico #", pico, " avg:", avg, "stdev:", std, "(over", len(iter_per_ms[pico]), "messages)")
            if len(iter_per_ms) == 0:
                print("No ITER_PER_MS packets")
            for pico in n_overflow_iter_per_ms:
                print("Number of overflow ITER_PER_MS packets for pico #", pico, "is", n_overflow_iter_per_ms[pico])
            if len(roundtrip_time) > 0:
                avg = statistics.mean(roundtrip_time)
                std = statistics.stdev(roundtrip_time)
            else:
                avg = "N/A"
                std = "N/A"
            print("MIDI_ROUNDTRIP_TIME_uS. avg:", avg, "stdev:", std, "(over", len(roundtrip_time), "messages)")
            print("NOTE_ON", dict(notes_on))
            for v in velocities_on:
                velocities_on[v] /= notes_on[v]
            print("VELOCITY_ON", dict(velocities_on))
            print("NOTE_OFF", dict(notes_off))
            for v in velocities_off:
                velocities_off[v] /= notes_off[v]
            print("VELOCITY_OFF", dict(velocities_off))
        return rtc_packets, adc_packets

    def pretty_print(self, data, exclude=[], target=sys.stdout):
        my_midi_strings = list(midi_strings.keys())
        for e in exclude:
            my_midi_strings.remove(e)

        if data[1] in midi_values:
            if midi_values[data[1]] in my_midi_strings:
                print(midi_values[data[1]], data[2], data[3], file=target)
        else:
            print(data[1], data[2], data[3], file=target)

    def _print_info(self):
        print("Run `mt.save_captured(file)` to stop capturing and save.")
        print("Run `mt.abort_capture()` to stop capturing.")

    def __init__(self):
        self.th = None
        self.term = None
        self.outport = mido.open_output(pico_out)
        print("Opened", pico_out, "for output", file=sys.stderr)
        self.must_stop = True
        self.mid = None
        self.track = None

    def _print_above(self, stuff):
        try:
            if self.term is None:
                import blessed
                self.term = blessed.Terminal()
            with self.term.location(self.term.width - len(stuff) - 1, 0):
                print(stuff, end=None)
        except ModuleNotFoundError:
            pass

    def _capture(self, pico):
        with mido.open_input(pico) as inport:
            print(pico, "opened, collecting messages.", file=sys.stderr)
            self._print_info()
            last_time = 0
            options = ["|", "/", "-", "\\"]
            i = 0
            self._print_above(options[i])
            for msg in inport:
                self.track.append(msg)
                curr_time = time.time()
                if (curr_time - last_time > .25):
                    i = (i+1) % len(options)
                    self._print_above(options[i])    # TODO print MIDI housekeeping
                    curr_time = last_time
                if self.must_stop:
                    break
        print("Capture stopped")

    def abort_capture(self):
        self.must_stop = True
        print("Waiting for last packet to quit")
        self.th.join()

    def capture(self, pico=pico_in):
        self.mid = MidiFile()
        self.must_stop = False

        self.track = MidiTrack()
        self.mid.tracks.append(self.track)
        self.th = threading.Thread(target=mt._capture, args=(self, pico) )  # NOQA space makes it clearer
        self.th.start()
        time.sleep(1)  # let the _print_above win the race condition agains the prompt

    def save_captured(self, filename):
        if type(filename) != str:
            raise ValueError("first argument must be a string")

        self.must_stop = True
        self.mid.save(filename)
        print("File saved, waiting for last packet")
        self.th.join()

    def adc_dump(self, note):
        if (self.must_stop):
            print("Dumping but not capturing")
            print("Run `mt.capture()` to capture.")
        self.outport.send(Message('sysex', data=(
            defined.MIDI_VENDOR,
            defined.MIDI_DUMP_NOTE_ADC,
            note,
            0, 0, 0)))

    def stop_adc_dump(self):
        self.outport.send(Message('sysex', data=(
            defined.MIDI_VENDOR,
            defined.MIDI_STOP_DUMP_ADC,
            0, 0, 0, 0)))
        if (not self.must_stop):
            print("Stopped dumpting but still capturing")
            self._print_info()

    def _validate_integer(self, a):
        if a < 0 or a > 4095:
            raise ValueError("Let off, Strike and Drop must be 0-4095")
        if a != int(a):
            raise ValueError("Let off, Strike and Drop must be integers")

    def _validate_float(self, a):
        if a < 0 or a > 255:
            raise ValueError("Velocities must be 0-255")

    def _int_regulation_with(self, a, verbose):
        first = int(a / 127)
        second = a % 127
        self.outport.send(Message('sysex', data=(
            defined.MIDI_VENDOR,
            defined.MIDI_CONTINUE_REGULATION,
            first,
            second,
            0, 0)))
        if verbose:
            print("Regulating with",
                  "0x{:02x}".format(first),
                  "0x{:02x}".format(second),
                  "==", first, second)

    def _float_regulation_with(self, a, verbose):
        first = int(a)
        second = int( (a - int(a)) * 100 )          # NOQA spaces make it clearer
        self.outport.send(Message('sysex', data=(
            defined.MIDI_VENDOR,
            defined.MIDI_CONTINUE_REGULATION,
            first,
            second,
            0, 0)))
        if verbose:
            print("Regulating with",
                  "0x{:02x}".format(first),
                  "0x{:02x}".format(second),
                  "==", first, second)

    def regulate(self, note, let_off=0, strike=0, drop=0,
                 vel_const=0, vel_slope=0, verbose=True):
        self._validate_integer(let_off)
        self._validate_integer(strike)
        self._validate_integer(drop)
        self._validate_float(vel_const)
        self._validate_float(vel_slope)

        self.outport.send(Message('sysex', data=(
            defined.MIDI_VENDOR,
            defined.MIDI_REGULATE,
            note,
            0, 0, 0)))
        self._int_regulation_with(let_off, verbose)
        self._int_regulation_with(strike, verbose)
        self._int_regulation_with(drop, verbose)
        self._float_regulation_with(vel_const, verbose)
        self._float_regulation_with(vel_slope, verbose)
        self._int_regulation_with(let_off, verbose)             # dummy to close the regulation
