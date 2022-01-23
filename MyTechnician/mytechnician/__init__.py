#!/usr/bin/env python3

import mido
from mido import Message, MidiFile, MidiTrack
from cdefine import CDefine

defined = CDefine('../RaspberryPiPico/My_MIDI_constants.h')
pico_in  = mido.get_input_names()[1]
pico_out = mido.get_output_names()[1]

inport = mido.open_input(pico_in)
outport = mido.open_output(pico_out)

print("Opened", pico_in, "for input")
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


