#!/usr/bin/env python3

import mido
from mido import Message, MidiFile, MidiTrack
from cdefine import CDefine

import threading, time, blessed, sys

pico_in  = mido.get_input_names()[1]
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
    def pretty_print(self, data, exclude=[]):
        my_midi_strings = list(midi_strings.keys())
        for e in exclude:
            my_midi_strings.remove(e)

        if data[1] in midi_values:
            if midi_values[data[1]] in my_midi_strings:
                print(midi_values[data[1]], data[2], data[3])
        else:
            print(data[1], data[2], data[3])

    def _print_info(self):
        print("Run `mt.save_captured(file)` to stop capturing and save.")
        print("Run `mt.abort_capture()` to stop capturing.")

    def __init__(self):
        self.th = None
        self.t = blessed.Terminal()
        self.outport = mido.open_output(pico_out)
        print("Opened", pico_out, "for output", file=sys.stderr)
        self.must_stop = True
        self.mid = None
        self.track = None

    def _print_above(self, stuff):
        with self.t.location(self.t.width - len(stuff) - 1, 0):
            print(stuff, end=None)

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
        self.th = threading.Thread(target = mt._capture, args = (self, pico) )
        self.th.start()
        time.sleep(1) # let the _print_above win the race condition agains the prompt


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
        self.outport.send(mido.Message('sysex', data=(
            defined.MIDI_VENDOR,
            defined.MIDI_DUMP_NOTE_ADC,
            note,
            0,0,0)))

    def stop_adc_dump(self):
        self.outport.send(mido.Message('sysex', data=(
            defined.MIDI_VENDOR,
            defined.MIDI_STOP_DUMP_ADC,
            0,0,0,0)))
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
        self.outport.send(mido.Message('sysex', data=(
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
        second = int( (a - int(a)) * 100 )
        self.outport.send(mido.Message('sysex', data=(
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

        self.outport.send(mido.Message('sysex', data=(
            defined.MIDI_VENDOR,
            defined.MIDI_REGULATE,
            note,
            0,0,0)))
        self._int_regulation_with(let_off, verbose)
        self._int_regulation_with(strike, verbose)
        self._int_regulation_with(drop, verbose)
        self._float_regulation_with(vel_const, verbose)
        self._float_regulation_with(vel_slope, verbose)
        self._int_regulation_with(let_off, verbose)             # dummy to close the regulation

