The data in this directory is (bzip2 compressed) capture of hammer strikes. The capture has been performed with
[MyTechnician](https://github.com/davidedelvento/Mybrid/tree/main/MyTechnician/mytechnician).

The `1000us` and the `pp-to-ff` files have been generated with a requested ADC dumping delay of `1ms` between samples. The `100us` file has been
generated with a `0.1ms` delay. As it can be seen from the data, in the higher-temporal-resolution case, packets have been dropped. This is due
to various issues, most notably [this one](https://github.com/SpotlightKid/python-rtmidi/issues/79). Even dumping the data in other ways, I would
still unable to capture the full temporal resolution of the RPiPico's ADC, as described
[here](https://raspberrypi.stackexchange.com/questions/135890/full-speed-of-pico-adc-faster-than-usb-how-to-capture-spi-compression)

To analyze these files this [tool](https://github.com/davidedelvento/Mybrid/blob/main/MyTechnician/) can be used.

![Plot](http://i.imgur.com/njksiwA.png)
