# Status

To capture data at the highest temporal resolution possible and avoid the problem mentioned in the "Less relevant, older information" section below,
I am using an SD card with the code I posted [here](https://github.com/davidedelvento/no-OS-FatFS-SD-SPI-RPi-Pico/blob/master/example/tests/big_file_test.c#L66-L81)

That data is in the `hires` and in the `battery` directories and it is bzip2'ed RAW binary format. The `parse.py` script
can extract that and dump it in text format, plot it or pretend to be a Pico and print information
about what MIDI velocities would that setting create

Given the high level of noise showed in the `hires` data and following some discussion at the link below about what might be causing
that noise, I speculated the noise being caused but the SMPS of the Pico. Following guidance from the data sheet, I tried a
number of things, including providing a `ADC_VREF` via a CR2032 battery and forcing the PWM mode on the power supply (simply with
`gpio_pull_up(23)`).  That helped a bit, but not substantially. So I decided
to power the Pico via two [C-cell batteries](https://en.wikipedia.org/wiki/C_battery) in series, applied to the `3V3`
(pin 36 of the Pico board) and to `ADC_VREF`. Yes, that's
supposed to be an "out" voltage, and I hickajed it to injected the power after the switching supply.
To avoid the (minimal?) risk of voltage flowing backwards through the regulator I also grounded out 3V3_EN pin 37 of the Pico board).

The series measured 3.2V before the test.
The internal resistance of the battery was a bit of a problem: voltage dropped to 3.05V during the test, and I was not sure that was sufficent
to power the Pico correctly (remember, this is bypassing the power regulator and forcing the board to run on exactly this voltage). The
battery series returned to 3.2V when I removed the load. 
My code was able to complete the ADC capture without attaching a computer. Look how clean it is compared to the PWM! Note the difference in
the vertical scale. 

![PWM power](https://github.com/davidedelvento/Mybrid/blob/main/data/RPiPico%2BEAITRCA6/battery/detail_pwm.png)

![Battery power](https://github.com/davidedelvento/Mybrid/blob/main/data/RPiPico%2BEAITRCA6/battery/detail_battery.png)

I am not sure about what may be causing that residual 160Hz modulation, it might be the Pico itself or it may be some external signal.
The signal here is from an IR phototransistor, and there was background artificial light, so the 60Hz power supply might
be playing a role (the test was performed in the USA).

More tests with a very accurate power supply and a signal generator are due.

See also https://pianoclack.com/forum/d/289-scanning-speed-and-velocity-mapping-of-cybrid/121 and 
https://pianoclack.com/forum/d/347-how-to-deal-with-hyperlocality-in-savitzky-golay-filtering/23



# Less relevant, older information

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
