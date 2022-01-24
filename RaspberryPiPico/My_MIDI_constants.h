#define MIDI_SYS_EX              0xF0   // System Exclusive messages
#define MIDI_END_SYSEX           0xF7   // End of System Exclusive, aka EOX
#define MIDI_VENDOR              0x7D   // Prototype

#define MIDI_DUMP_NOTE_ADC       0x7F   // custom command to start sending ADC data over MIDI
#define MIDI_STOP_DUMP_ADC       0x7E   // custom command to stop  sending ADC data over MIDI
// we could probably use 0x7D skipping to avoid confusion with MIDI_VENDOR
#define MIDI_REGULATE            0x7C   // custom command to start regulating one note
#define MIDI_CONTINUE_REGULATION 0x7B   // custom command to continue (or finish) regulating
#define MIDI_DUMP_REGULATION     0x7A   // custom command to dump regulation parameters for one note
#define INIT_PICO                0x79   // custom command to init each pico (at the beginning) or measuring roundtrip time
#define MIDI_ROUNDTRIP_TIME      0x79   // custom command to init each pico (at the beginning) or measuring roundtrip time
#define MIDI_NO_SUCH_NOTE        0x78
#define MIDI_ERROR               0x77
#define MIDI_ITER_PER_MS         0x40   // bits the ADC will never use, adding one for each pico, can be max 0x77

#define MIDI_MAX_ADC_VALUE       0x31   // maximum value of the highest byte of the ADC. Make sure
                                        // all other MIDI constants here are higher than this.

#define MIDI_NOTE_ON       0x90
#define MIDI_NOTE_OFF      0x80
