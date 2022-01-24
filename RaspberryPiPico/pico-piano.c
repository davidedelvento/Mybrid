#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "pico/binary_info.h"
#include "pico/float.h"
#include "hardware/gpio.h"
#include "hardware/adc.h"
#include "hardware/i2c.h"
#include "bsp/board.h"
#include "pico/util/queue.h"

#include "My_MIDI_constants.h"

#ifdef MIDI_CONTROLLER
#include "tusb.h"
#endif

#ifdef MIDI_CONTROLLER
#ifdef WORKER
#error A build can be either MIDI_CONTROLLER or WORKER but not both
#endif
#endif

#ifndef MIDI_CONTROLLER
#ifndef WORKER
#error A build must be MIDI_CONTROLLER or WORKER
#endif
#endif

// getting I2C working in duplex is a pain, so going one direction
// only is best. To do so, I am daisy chaining each Pico into the
// next, master/controller on the sending (output) channel, namely i2c0
// and slave/worker on the receiving (input) channel, namely i2c1.
// The output from the last one goes back to the first (midi controller).
// As such a single address is sufficient for an unlimited number
// of Picos.
#define I2C_ADDRESS 75

#define in_SDA_PIN 14
#define in_SCL_PIN 15
#ifdef MIDI_CONTROLLER     // for ease of wiring I used different pins on the controller...
#define out_SDA_PIN 16
#define out_SCL_PIN 17
#elif defined WORKER       // ...compared to the worker, for output communication
#define out_SDA_PIN 0
#define out_SCL_PIN 1
#endif

enum  {
  BLINK_FAST = 100,
  BLINK_NOT_MOUNTED = 250,
  BLINK_MOUNTED = 1000,
  BLINK_SUSPENDED = 2500,
};

enum {
  IDLE = 1,
  FLY = 2,
  SOUND = 4,
};

#define N_ADC 3                // number of ADC channels
#define FIRST_NOTE 65
#define SYSEX_PKG_LEN 6        // warning, assumption below needs to be fixed before change
                               // must also be less than hw Tx FIFO, which is 16
static uint8_t status[N_ADC];
static uint32_t start_t[N_ADC];
static uint16_t LET_OFF[N_ADC];
static uint16_t STRIKE[N_ADC];
static uint16_t DROP[N_ADC];
// perhaps not much would be lost by making these integers?
static float VEL_CONST[N_ADC];
static float VEL_SLOPE[N_ADC];

static volatile uint32_t blink_interval_ms = BLINK_NOT_MOUNTED;
static uint32_t calibration_ms = 500;

void count_loop_iterations(void);
void led_blinking_task(void);
void midi_out_task(void);
void midi_in_task(void);
void i2c_listener();
#ifdef MIDI_CONTROLLER
void send_some_junk();
#elif defined WORKER
static volatile bool have_been_init = false;
static queue_t sysex_buffer;
#endif
static volatile uint8_t my_pico_id = 0;
static volatile uint8_t n_pico = 0;

// this runs on core0
int main() {
  stdio_init_all();
  adc_init();
  adc_gpio_init(26);
  adc_gpio_init(27);
  adc_gpio_init(28);
  adc_select_input(0);
  // 0b0001 is 26
  // 0b0010 is 27
  // 0b0100 is 28
  // 0b0111 = 0x07 is all of the previous
  adc_set_round_robin(7);

  for(int i=0; i<N_ADC; i++) {
    status[i] = IDLE;
    LET_OFF[i] = 2500;
    STRIKE[i] = 2100;
    DROP[i] = 3000;
    // see https://pianoclack.com/forum/d/289-scanning-speed-and-velocity-mapping-of-cybrid/3
    // MIDI_VEL  = 57.96 + 71.3 * log10f(2.0 / time) =
    //           = 57.96 + 71.3 * log10f(2.0) - 71.3 * log10f(time)
    VEL_CONST[i] = 57.96 + 71.3 * log10f(2.0);
    VEL_SLOPE[i] = 71.3;
    // perhaps not much would be lost by making these integers?
  }

  // I2C0 is the output bus, where data is written
  // each pico must be the controller of this bus, because
  // the worker-writer i2c interface does not work and it does
  // need to write data, so it must be a controller-writer (1)
  gpio_init(out_SDA_PIN);
  gpio_init(out_SCL_PIN);
  gpio_set_function(out_SCL_PIN, GPIO_FUNC_I2C);
  gpio_set_function(out_SDA_PIN, GPIO_FUNC_I2C);
  gpio_pull_up(out_SDA_PIN);
  gpio_pull_up(out_SCL_PIN);
  i2c_init(i2c0, 100 * 1000);

  // I2C1 is the input bus
  // must be worker since the previous pico is controller on the output
  // see (1) and (2)
  gpio_init(in_SDA_PIN);
  gpio_init(in_SCL_PIN);
  gpio_set_function(in_SDA_PIN, GPIO_FUNC_I2C);
  gpio_set_function(in_SCL_PIN, GPIO_FUNC_I2C);
  gpio_pull_up(in_SDA_PIN);
  gpio_pull_up(in_SCL_PIN);
  i2c_init(i2c1, 100 * 1000);
  i2c_set_slave_mode(i2c1 ,true, I2C_ADDRESS);    // (2)

  //board_init();  this was silently breaking some I2C communications
  gpio_init(PICO_DEFAULT_LED_PIN);
  gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);
#ifdef MIDI_CONTROLLER
  tusb_init();
  sleep_ms(500);
  send_some_junk();                       // otherwise the first MIDI messages will be lost
#endif
  multicore_launch_core1(i2c_listener);

#ifdef WORKER
  queue_init(&sysex_buffer, SYSEX_PKG_LEN * sizeof(uint8_t), 10);  // keep at most 10 packets
  blink_interval_ms = BLINK_FAST;
  while(!have_been_init) {
    led_blinking_task();
    sleep_ms(10);
  }
  blink_interval_ms = BLINK_MOUNTED;
#endif

  while (1)
  {
#ifdef MIDI_CONTROLLER
    tud_task(); // keep MIDI over USB alive
#endif
    midi_out_task();
    midi_in_task();
    count_loop_iterations();
    led_blinking_task();
  }
}

#ifdef MIDI_CONTROLLER
void send_some_junk() {
    uint8_t packet[SYSEX_PKG_LEN];

    tud_task(); // keep MIDI over USB alive

    packet[0] = MIDI_SYS_EX;
    packet[1] = MIDI_VENDOR;
    packet[2] = MIDI_ITER_PER_MS;
    packet[3] = 0x7F;
    packet[4] = 0x7F;
    packet[5] = MIDI_END_SYSEX;

    // only sending junk MIDI packets or only sleeping does not avoid
    // dropping the subsequent MIDI messages. The combination
    // below is the most reasonable one WRT time spent and
    // number of junk MIDI packets sent VS reliably transmit
    // all subsequent MIDI packets
    for(int i=0; i<100; i++) {
      tud_midi_stream_write(0, packet, SYSEX_PKG_LEN);
      tud_task();                                       // keep MIDI over USB alive
      sleep_ms(10);
    }
}
#elif defined WORKER
static void inline sysex_enqueue(uint8_t *packet) {
  if (!queue_is_full(&sysex_buffer)) {
    uint8_t copy[SYSEX_PKG_LEN];           // needs to preserve the content even if
    for (int i=0; i<SYSEX_PKG_LEN; i++) {  // original is overwritten
      copy[i] = packet[i];
    }
    queue_add_blocking(&sysex_buffer, copy);
  } // else { // TODO send "too many requests" error
}
#endif

void inline send(const uint8_t *src) {
  i2c_write_blocking(i2c0, I2C_ADDRESS, src, SYSEX_PKG_LEN, false);
}

static void inline receive(uint8_t *src) {
  i2c_read_raw_blocking(i2c1, src, SYSEX_PKG_LEN);
}

#define STATS_EVERY 5000 // average and report iterations and roundtrips every 5 seconds

void i2c_listener() {
  uint8_t packet[SYSEX_PKG_LEN];
#ifdef MIDI_CONTROLLER
  packet[0] = MIDI_SYS_EX;
  packet[1] = MIDI_VENDOR;
  packet[2] = INIT_PICO;
  packet[3] = 0x00;
  packet[4] = 0x77;
  packet[5] = MIDI_END_SYSEX;
  send(packet);
#endif

  receive(packet);
  if (packet[0] == MIDI_SYS_EX &&
      packet[1] == MIDI_VENDOR &&
      packet[2] == INIT_PICO) {

#ifdef WORKER
    my_pico_id = ++packet[3];
    have_been_init = true;
    send(packet);
#elif defined MIDI_CONTROLLER
    n_pico = ++packet[3]; // TODO bail out if more than possible (see also MIDI_ERROR definition)
    tud_midi_stream_write(0, packet, SYSEX_PKG_LEN);  // let the computer know
#endif

  }
#ifdef WORKER
  else {                      // gotten an non-init packet, should never happen
    send(packet);             // rely whatever the packet was and send an error
    packet[0] = MIDI_SYS_EX;
    packet[1] = MIDI_VENDOR;
    packet[2] = MIDI_ERROR;
    packet[3] = 0x66;
    packet[4] = 0x66;
    packet[5] = MIDI_END_SYSEX;
    send(packet);
  }                           // TODO should also continue waiting for the missing init packet?
#endif

  uint32_t current_time, time_when_sent = 0;
  bool received = false;
  while(true) {
#ifdef MIDI_CONTROLLER
    current_time = board_millis();
    if (current_time - time_when_sent >= ITERATIONS_EVERY && received){
      packet[0] = MIDI_SYS_EX;
      packet[1] = MIDI_VENDOR;
      packet[2] = MIDI_ROUNDTRIP_TIME;
      send(packet);
      received = false;
      time_when_sent = current_time;
    }
#endif
    receive(packet);
#ifdef MIDI_CONTROLLER
    current_time = board_millis();
    if (packet[0] == MIDI_SYS_EX &&
        packet[1] == MIDI_VENDOR &&
        packet[2] == MIDI_ROUNDTRIP_TIME) {
      uint32_t roundtrip = current_time - time_when_sent;
      if (roundtrip > 0x3FFF) {
        roundtrip = 0x3FFF; // max value possible via MIDI
      }
      packet[3] = 0x7F & (roundtrip >> 7);
      packet[4] = 0x7F & roundtrip;
      packet[5] = MIDI_END_SYSEX;
      received = true;
      tud_midi_stream_write(0, packet, SYSEX_PKG_LEN);
      }
    }
#elif defined WORKER
    send(packet);
#endif

    if (packet[0] != MIDI_SYS_EX) {
#ifdef MIDI_CONTROLLER
      tud_midi_stream_write(0, packet, 3);
#endif
    } else {
#ifdef WORKER
      sysex_enqueue(packet);
#elif defined MIDI_CONTROLLER
      tud_midi_stream_write(0, packet, SYSEX_PKG_LEN);
#endif
    }
  }
}

#ifdef MIDI_CONTROLLER
void tud_mount_cb(void) {    // Invoked when device is mounted
  blink_interval_ms = BLINK_MOUNTED;
}
void tud_umount_cb(void) {   // Invoked when device is unmounted
  blink_interval_ms = BLINK_NOT_MOUNTED;
}
void tud_suspend_cb(bool remote_wakeup_en) {  // Invoked when usb bus is suspended
// remote_wakeup_en : if host allow us  to perform remote wakeup
  (void) remote_wakeup_en;
  blink_interval_ms = BLINK_SUSPENDED;
}
void tud_resume_cb(void) {   // Invoked when usb bus is resumed
  blink_interval_ms = BLINK_MOUNTED;
}
#endif

uint8_t midi_vel(uint32_t time, uint8_t note) {
  uint8_t ret = (uint8_t)(VEL_CONST[note] - VEL_SLOPE[note] * log10f(time));
  ret = 80;
  return ret;  // TODO
}

void parse_distance(uint8_t *status, uint16_t d, uint32_t *start_time, uint8_t note) {
  switch (*status) {
    case IDLE:
      if (d < LET_OFF[note]) {
        *status = FLY;
        *start_time = board_millis();
      }
      break;
    case FLY:
      if (d < STRIKE[note]) {
        *status = SOUND;
        uint8_t vel = midi_vel(board_millis() - *start_time, note);
        uint8_t msg_on[SYSEX_PKG_LEN] = {MIDI_NOTE_ON,
		                         note + FIRST_NOTE + my_pico_id * N_ADC,
					 vel};
#ifdef WORKER
        send(msg_on);
#elif defined MIDI_CONTROLLER
        tud_midi_stream_write(0, msg_on, 3);
#endif
      } else if (d > LET_OFF[note]) {
        *status = IDLE;
      }
      break;
    case SOUND:
      if (d > DROP[note]) {
        *status = IDLE;
        uint8_t msg_off[SYSEX_PKG_LEN] = {MIDI_NOTE_OFF,
		                          note + FIRST_NOTE + my_pico_id * N_ADC,
					  0};
#ifdef WORKER
        send(msg_off);
#elif defined MIDI_CONTROLLER
        tud_midi_stream_write(0, msg_off, 3);
#endif
      }
      break;
  }
}

void midi_out_task(void) {
  uint16_t distance[N_ADC];
  for (int i=0; i<N_ADC; i++) {
    distance[i] = adc_read();
    parse_distance(&status[i], distance[i], &start_t[i], i);
  }
}

void dump_note_adc(uint8_t my_note) {
  uint8_t packet[SYSEX_PKG_LEN];
  uint8_t midi_note_id = FIRST_NOTE + my_pico_id * N_ADC + my_note;
  uint16_t distance[N_ADC];
  uint32_t last_sent_ms = 0;

  blink_interval_ms = BLINK_FAST;

  while(true) {
#ifdef MIDI_CONTROLLER
    tud_task(); // keep MIDI over USB alive
    if (tud_midi_available()) {
      tud_midi_stream_read(packet, SYSEX_PKG_LEN);
#elif defined WORKER
    if (queue_try_remove(&sysex_buffer, packet)) {
#endif
      if (packet[0] == MIDI_SYS_EX && packet[1] == MIDI_VENDOR) {
        if (packet[2] == MIDI_STOP_DUMP_ADC) {
	  break;
	}
      }
    }
    if (board_millis() - last_sent_ms > calibration_ms) {
      for (int i=0; i<N_ADC; i++) {  // needs to read all of them even if sending one only
        distance[i] = adc_read();
      }
      packet[0] = MIDI_SYS_EX;
      packet[1] = MIDI_VENDOR;
      packet[2] = 0x7F & (distance[my_note] >> 7);    // highest 7 bits, the ADC is 12 bit, max here is 31
      packet[3] = 0x7F & distance[my_note];           // lowest  7 bits
                                                      // if more than 14 bits, we need another byte
      packet[4] = midi_note_id;  // already 7 bits
      packet[5] = MIDI_END_SYSEX;
#ifdef WORKER
      send(packet);
#elif defined MIDI_CONTROLLER
      tud_midi_stream_write(0, packet, SYSEX_PKG_LEN);
#endif
    }
    led_blinking_task();
  }

  blink_interval_ms = BLINK_MOUNTED;
}

void send_int16_parameter(uint16_t param) {
  uint8_t packet[SYSEX_PKG_LEN];
  packet[0] = MIDI_SYS_EX;
  packet[1] = MIDI_VENDOR;
  packet[2] = MIDI_DUMP_REGULATION;
  packet[3] = 0x7F & (param >> 7);
  packet[4] = 0x7F & param;
  packet[5] = MIDI_END_SYSEX;

#ifdef WORKER
  send(packet);
#elif defined MIDI_CONTROLLER
  tud_task(); // keep MIDI over USB alive
  tud_midi_stream_write(0, packet, SYSEX_PKG_LEN);
#endif
  led_blinking_task();
}

void send_float_parameter(float param) {
  uint8_t packet[SYSEX_PKG_LEN];
  packet[0] = MIDI_SYS_EX;
  packet[1] = MIDI_VENDOR;
  packet[2] = MIDI_DUMP_REGULATION;
  packet[3] = 0x7F & (uint8_t)param;
  packet[4] = 0x7F & (uint8_t)( (param - (uint8_t)param) * 100 );
  packet[5] = MIDI_END_SYSEX;

#ifdef WORKER
  send(packet);
#elif defined MIDI_CONTROLLER
  tud_task(); // keep MIDI over USB alive
  tud_midi_stream_write(0, packet, SYSEX_PKG_LEN);
#endif
  led_blinking_task();
}

void dump_regulation_for_note(uint8_t my_note) {
  blink_interval_ms = BLINK_FAST;

  send_int16_parameter(LET_OFF[my_note]);
  send_int16_parameter(STRIKE[my_note]);
  send_int16_parameter(DROP[my_note]);
  send_float_parameter(VEL_CONST[my_note]);
  send_float_parameter(VEL_SLOPE[my_note]);

  blink_interval_ms = BLINK_MOUNTED;
}

void regulate_note(uint8_t my_note) {
  uint8_t packet[SYSEX_PKG_LEN];
  int i = 0;

  blink_interval_ms = BLINK_FAST;

  while(true) {
#ifdef MIDI_CONTROLLER
    tud_task(); // keep MIDI over USB alive
    if (tud_midi_available()) {
      tud_midi_stream_read(packet, SYSEX_PKG_LEN);
#elif defined WORKER
    if (queue_try_remove(&sysex_buffer, packet)) {
#endif
      if (packet[0] == MIDI_SYS_EX && packet[1] == MIDI_VENDOR) {
        if (packet[2] == MIDI_CONTINUE_REGULATION) {
	  if (i++ == 6) { // needs a final dummy 'continue' to exit
	    break;
	  }
	  switch (i) {    // TODO: packet is underutilized, add constant to select what to regulate, and repeat note number?
            case 1:
	      LET_OFF[my_note] = ((uint16_t)packet[3] << 7) + packet[4];
	      break;
	    case 2:
	      STRIKE[my_note] = ((uint16_t)packet[3] << 7) + packet[4];
	      break;
	    case 3:
	      DROP[my_note]   = ((uint16_t)packet[3] << 7) + packet[4];
	      break;
	    case 4:
              // perhaps not much would be lost by making these integers?
	      VEL_CONST[my_note] = packet[3] + packet[4] / 100.;
	      break;
	    case 5:
	      VEL_SLOPE[my_note] = packet[3] + packet[4] / 100.;  // perhaps divided by 127 instead?
	      break;
	  }
	}
      }
    }

  led_blinking_task();
  }

  blink_interval_ms = BLINK_MOUNTED;
}

static void inline process_midi_request(uint8_t *packet) {
  if (packet[0] == MIDI_SYS_EX && packet[1] == MIDI_VENDOR) {
    uint8_t note = packet[3] - FIRST_NOTE;
    uint8_t note_pico_id = note / N_ADC;
    if (note_pico_id != my_pico_id) {
      return; // not my business
    }
    uint8_t note_adc_id = note % N_ADC;
    if (packet[2] == MIDI_DUMP_NOTE_ADC) {
      dump_note_adc(note_adc_id);
    } else if (packet[2] == MIDI_REGULATE) {
      regulate_note(note_adc_id);
    } else if (packet[2] == MIDI_DUMP_REGULATION) {
      dump_regulation_for_note(note_adc_id);
    }
  }
}

void midi_in_task(void) {
  uint8_t packet[SYSEX_PKG_LEN] = {};
#ifdef WORKER
  if (!queue_try_remove(&sysex_buffer, packet)) {
    return;
  }
#elif defined MIDI_CONTROLLER
  // The MIDI interface always creates input and output port/jack descriptors
  // regardless of these being used or not. Therefore incoming traffic should be read
  // (possibly just discarded) to avoid the sender blocking in IO
  if (tud_midi_available()) {
    tud_midi_stream_read(packet, SYSEX_PKG_LEN);
    send(packet);                                 // to all other picos
  } else {
    return;
  }
  if (packet[0] == MIDI_SYS_EX && packet[1] == MIDI_VENDOR) {
    int note = packet[3];

    // send NO_SUCH_NOTE message if requested note is out of range
    if (note < FIRST_NOTE || note > FIRST_NOTE + n_pico * N_ADC) {
      packet[0] = MIDI_SYS_EX;
      packet[1] = MIDI_VENDOR;
      packet[2] = MIDI_NO_SUCH_NOTE;
      packet[3] = note;                 // already assigned, for clarity
      packet[4] = n_pico;
      packet[5] = MIDI_END_SYSEX;
    }
  }
#endif
  process_midi_request(packet);
}

void led_blinking_task(void) {
  static uint32_t start_ms = 0;
  static bool led_state = false;

  if ( board_millis() - start_ms < blink_interval_ms) return; // not enough time
  start_ms += blink_interval_ms;

  gpio_put(PICO_DEFAULT_LED_PIN, led_state);
  led_state = 1 - led_state; // toggle
}

void count_loop_iterations() {
  static uint64_t loop_iterations = 0;
  static uint32_t last_stats_time_ms = 0;
  loop_iterations ++;

  uint32_t current_time = board_millis();
  if (current_time - last_stats_time_ms >= ITERATIONS_EVERY) {
    last_stats_time_ms = current_time;
    uint8_t packet[SYSEX_PKG_LEN];
    packet[0] = MIDI_SYS_EX;
    packet[1] = MIDI_VENDOR;
    packet[2] = MIDI_ITER_PER_MS;
    packet[3] = my_pico_id;
    uint32_t iter_per_ms = (uint32_t) (loop_iterations / ITERATIONS_EVERY);
    if (iter_per_ms < 0x7F) {
      packet[4] = iter_per_ms & 0x7F;
    } else {                                 // overflow
      packet[4] = 0x7F;
    }
    packet[5] = MIDI_END_SYSEX;
#ifdef WORKER
    // reports 0x61 or 0x62 (i.e. 97-98)
    send(packet);
#elif defined MIDI_CONTROLLER
    // constantly reports 0x56 (i.e. 56)
    tud_midi_stream_write(0, packet, SYSEX_PKG_LEN);
#endif
    loop_iterations = 0;
  }
}
