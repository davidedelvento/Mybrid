### About

This directory contains code to run an electronic musical instrument, based on ADCs, with a number of Raspberry Pi Pico, which should work identically on the microcontroller 
which powers it, the RP2040. This microcontroller (or the Raspberry Pi Pico, if you prefer a turnkey solution) is very attractive for a number of reasons
(listed below) and hence this subproject.

### Goals
The main goals of the whole platform apply, namely foster a collaborative exploration of options, seeking for the possible best
electronic musical instrument, at a much less expensive price than commercial; be totally in charge of it and be able
to change things as one prefer, a big plus for digital piano players. Specific to this subproject are the following:
* The cheapest turnkey solution to tests and characterize various distance sensors. Initially this was my only goal, but since it turned out to be a very viable
platform, I wrote some quite decent code for it and added the following
* Test and characterize the RP2040 *itself*, both as
  * a possible external ADC chip, as discussed by Jay [here](https://github.com/jkominek/piano-conversion/issues/46#issuecomment-1011710810)
  * a viable standalone platform, which on paper seems a bit too wimpy
* Provide an option for a complete solution, with industrial quality parts, no custom PCB design and ordering, and almost no soldering

### Current Status
As stated above, I purchased the Raspberry Pi Pico as test platform for sensors. In fact, it its current form, this software almost makes it
to the point of the latter. For example, the code not only supports daisy-chaining up to 60 boards: it automatically discovers the number
of connected boards and correctly operates all of them! You need to connect only the main Pico to a computer, and it presents itself as
a single MIDI instrument. Via MIDI, it sends SYS_EX messages regarding its internal performance and status. You
can control a number of internal settings via MIDI too: just send SYS_EX commands: no need to recompile. By no means it's a complete
project, but it is taking shape as such and it *could* become a complete project with a small amount of work.

### Wiring diagram
See pictures. You can wire it differently, just make sure to change the relevant PINs in the code.

### Benefits of this approach
* The RP2040 (and the Raspberry Pi Pico) is not experiencing any chip shortage as many other competing boards
* This platform is extremely inexpensive. A Raspberry Pi Pico costs $4.00 and a  RP2040 ranging in price from $0.70 to $1.00 
each, depending on volume.
* The RP2040 has a competent ADC, with 12 nominal bits and almost 9 ENOB. It can operate at 0.5MHz and it includes a very easy to program 5-to-1
multiplexer (of course using the multiplexer the frequency of each channel is divided by the number in use, so if one uses all 5 of them
a less attractive, but still decent, 100kHz sampling is possible in each channel). One multiplexer line is hard-wired internally, so only
4 lines can be used for the external sensors. Moreover, the Raspberry Pi Pico hard-wires another channel, so only 3 channels are available with
it. Assuming one does not uses the hard-wired channels, a Raspberry Pi Pico can sample 3 sensors each at 167kHz, whereas a naked RP2040 can sample
4 sensors at 125kHz. If higher frequency sampling turns out to be indispensable, as discussed at the link below, one can use fewer channels, possibly
down to even a single channel per board. This is supported in the code with a simple recompile. 
* The RP2040 has a number of buses to communicate with the outside world, but see caveats below.
* Building a complete solution with Raspberry Pi Picos and pre-soldered sensors such as [these](https://www.sparkfun.com/products/9453) will cost
about $50 per octave, with most of the price coming from the sensor boards. Making your own sensor board will easily halve that cost to around $25
per octave. Using the RP2040s alone and the sensors both in your custom made PCB, will halve that price again to about $12 per octave. Making it in
volume will further reduce the costs substantially, and since many identical parts are needed for a single keyboard, just making 10 of them
would further reduce the price by about 20%
* The prices above are for a single sensor per key. If one wants two (e.g. for hammer and damper sensors) the prices would double. If one
is interested in the absolutely lowest price, it may be possible to have only one (key) sensor per note and use it for note-on, note-off (damper)
and polyphonic aftertouch (some more tests are needed to confirm this is possible, but it seems to be the case). It should be no problem to
use one sensor for both polyphonic aftertouch and damper sensors (note-off), with a separate hammer sensor for note-on: this
is currently what I plan to do for my own implementation. Note that these analog sensors are not the same as the (often rubber-made)
on-off switches utilized in commercial projects, where they advertize the need for two and the "benefits" of having three "sensors"
(they are just switches, hence the quotes). The analog sensors utilized in this and similar projects are theoretically
an infinite number of switches per key. Even when including real life optical and electronic noises, they operate at least
as 64 switches per keys, and with some care they could act as many, many more.

### Caveats
Programming for a microcontroller has a number of warts, and the RP2040 makes no exception. Some of them are quite severe. In fact I have
**not** being able to have the I2C work bidirectionally as I initially intended, to achieve the typical linear bus topology
(see link below). While the I2C, the RP2040 and its SDK all claim to support bidirection communication, 
[in practice](https://github.com/davidedelvento/Rpi-pico-i2c-example) I have been unable to achieve it with the reliability and speed (not
to mention ease of coding, which I initially wanted, but then dropped as a requirement). So I changed my design to a ring, and the data
flows only in one direction (this is possible because each RP2040 has two I2C buses). This solution has a number of advantages and disadvantages
but I am not going to discuss them in this small margin. Another issue which I encountered was that doing board initialization with
the TinyUSB library (which I need to implement MIDI), very weirdly make only one of the two I2C buses work (yes, `board_init()` is not
for production systems, but still...)

If you plan to make any non-trivial code change, **be prepared to spend a possibly large amount of time for an unexpected problem like these.**

Switching to another kind of caveat. While the data I collected so far indicates that the platform is
adequate for the purpose, by any means I have not run all possible
tests and situation that could happen in real life playing. It might still turn out that the RP2040 is too wimpy of a microprocessor
(as I initially thought) to be able to address one of these situations, for which further testing is needed.



### Links
* https://en.wikipedia.org/wiki/Network_topology#Classification
* [RP2040 in bulk](https://www.raspberrypi.com/news/raspberry-pi-direct-buy-rp2040-in-bulk-from-just-0-70/)
* RP2040 in small quantities can be purchased from the usual places, Adafruit, Arrow, Digi-Key, Mouser, Pimoroni, etc
* Frequency of the sampling, discussed at https://github.com/jkominek/piano-conversion/issues/46 and links within.


### Last updated

All information about status of the code, prices, availability, etc is as of January 2022



