#!/usr/bin/env python3

import mido
from mido import Message, MidiFile, MidiTrack
from cdefine import CDefine

defined = CDefine('../RaspberryPiPico/My_MIDI_constants.h')
pico_in  = mido.get_input_names()[1]
pico_out = mido.get_output_names()[1]

#inport = mido.open_input(pico_in)
outport = mido.open_output(pico_out)

#print("Opened", pico_in, "for input")
print("Opened", pico_out, "for output")

def adc_dump(note):
    outport.send(mido.Message('sysex', data=(
        defined.MIDI_VENDOR,
        defined.MIDI_DUMP_NOTE_ADC,
        note,
        0,0,0)))

def stop_adc_dump():
    outport.send(mido.Message('sysex', data=(
        defined.MIDI_VENDOR,
        defined.MIDI_STOP_DUMP_ADC,
        0,0,0,0)))

def _validate_integer(a):
    if a < 0 or a > 4095:
        raise ValueError("Let off, Strike and Drop must be 0-4095")
    if a != int(a):
        raise ValueError("Let off, Strike and Drop must be integers")

def _validate_float(a):
    if a < 0 or a > 255:
        raise ValueError("Velocities must be 0-255")

def _int_regulation_with(a, verbose):
    first = int(a / 127)
    second = a % 127
    outport.send(mido.Message('sysex', data=(
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

def _float_regulation_with(a, verbose):
    first = int(a)
    second = int( (a - int(a)) * 100 )
    outport.send(mido.Message('sysex', data=(
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

def regulate(note, let_off=0, strike=0, drop=0,
        vel_const=0, vel_slope=0, verbose=True):
    _validate_integer(let_off)
    _validate_integer(strike)
    _validate_integer(drop)
    _validate_float(vel_const)
    _validate_float(vel_slope)

    outport.send(mido.Message('sysex', data=(
        defined.MIDI_VENDOR,
        defined.MIDI_REGULATE,
        note,
        0,0,0)))
    _int_regulation_with(let_off, verbose)
    _int_regulation_with(strike, verbose)
    _int_regulation_with(drop, verbose)
    _float_regulation_with(vel_const, verbose)
    _float_regulation_with(vel_slope, verbose)
    _int_regulation_with(let_off, verbose)             # dummy to close the regulation

