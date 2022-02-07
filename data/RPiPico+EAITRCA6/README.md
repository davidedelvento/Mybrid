# Status

To capture data at the highest temporal resolution possible and avoid the problem mentioned below,
I am using an SD card with the code I posted [here](https://github.com/davidedelvento/no-OS-FatFS-SD-SPI-RPi-Pico/blob/master/example/tests/big_file_test.c#L66-L81)

That information is in the `hires` directory and it is bzip2'ed RAW binary format. The `parse.py` script
can extract that and dump it in text format, plot it or pretend to be a Pico and print information
about what MIDI velocities would that setting create

See https://pianoclack.com/forum/d/289-scanning-speed-and-velocity-mapping-of-cybrid/121 for some 
plots and download the data in `txt` format



# Less relevant information

The data in this directory is (bzip2 compressed) capture of hammer strikes. The capture has been performed with
[MyTechnician](https://github.com/davidedelvento/Mybrid/tree/main/MyTechnician/mytechnician).

Why capture in MIDI format instead of plain text? Because so I have lots of other housekeeping information which the Picos produce
and that may turn useful to understand what is going on (for example packet loss as described in the next paragraph). A simple
plain text dump of measured numbers require something (comments?) to specify this information and a format definition. The MIDI
files already have this format definition inside.

The `1000us` and the `pp-to-ff` files have been generated with a requested ADC dumping delay of `1ms` between samples. The `100us` file has been
generated with a `0.1ms` delay. As it can be seen from the data, in the higher-temporal-resolution case, packets have been dropped. This is due
to various issues, most notably [this one](https://github.com/SpotlightKid/python-rtmidi/issues/79). Even dumping the data in other ways, I would
still unable to capture the full temporal resolution of the RPiPico's ADC, as described
[here](https://raspberrypi.stackexchange.com/questions/135890/full-speed-of-pico-adc-faster-than-usb-how-to-capture-spi-compression)

To analyze these files this [tool](https://github.com/davidedelvento/Mybrid/blob/main/MyTechnician/) can be used.

![Plot](http://i.imgur.com/njksiwA.png)
