To just look at the [data](https://github.com/davidedelvento/Mybrid/tree/main/data) you can use the `./plot_midi.py` command.

At minimum, you need `Python 3` (tested with `3.7.12`) and `mido`(a python library for MIDI, tested with `1.2.10`). Mido itself
needs a backend, and the simplest one you can use is `python-rtmidi` (tested with 1.4.9). If you want to make plots,
instead of just dumping a text of the data, you need also `matplotlib`

The `./plot_midi.py` command is very simple. You specify the `filename` of a bzip2-ed MIDI file containing the expected SYSEX
and by default it creates a matplotlib interactive plot. If you rather use something else, you specify the `--dump` option
and it prints on the `stdout` the data (you can redirect it into a text file). Optionally, you can use the `-i` argument
to ignore the MIDI time data (if present).
