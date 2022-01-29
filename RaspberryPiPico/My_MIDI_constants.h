#define MIDI_SYS_EX              0xF0   // System Exclusive messages
#define MIDI_END_SYSEX           0xF7   // End of System Exclusive, aka EOX
#define MIDI_VENDOR              0x7D   // Prototype

#define MIDI_DUMP_NOTE_ADC       0x7F   // custom command to start sending ADC data over MIDI
#define MIDI_STOP_DUMP_ADC       0x7E   // custom command to stop  sending ADC data over MIDI
// we could probably use 0x7D skipping to avoid confusion with MIDI_VENDOR
#define MIDI_REGULATE            0x7C   // custom command to start regulating one note
#define MIDI_CONTINUE_REGULATION 0x7B   // custom command to continue (or finish) regulating
#define MIDI_DUMP_REGULATION     0x7A   // custom command to dump regulation parameters for one note
#define INIT_PICO                0x75   // custom command to init each pico
#define MIDI_ROUNDTRIP_TIME_uS   0x79   // custom command to measure roundtrip time
#define MIDI_NO_SUCH_NOTE        0x78

#define MIDI_ERROR               0x77
#define TOO_MANY_PICOS           0x07   // only used as a field of MIDI_ERROR, no limitations other than using only 7 bits
#define EXPECTING_INIT           0x17
#define TOO_MANY_PACKETS         0x27

#define MIDI_ITER_PER_MS         0x76

#define MIDI_RTC                 0x20   // potentially allowing 5 bits of additional time data, if desired

#define MIDI_MAX_ADC_VALUE       0x1F   // maximum value of the highest byte of the ADC. Make sure all other MIDI constants
                                        // here are higher than this, otherwise ambiguity in packets meaning will arise.
					// Note that the RP2040 ADC is 12 bit and can be split in 7 + 5. Even a 14 bit
					// ADC will require full 7 + 7 bit which is the maximum possible payload
					// in MIDI v1 for the selected packet size. So we'd have to increase packet size
					// or switch to Universal Midi Packet (UMP) which implies MIDI v2
					//
					// See VERY IMPORTANT comment in the C code to see how it works.
					
#define MIDI_NOTE_ON       0x90
#define MIDI_NOTE_OFF      0x80
