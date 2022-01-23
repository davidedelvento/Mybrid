cmake_minimum_required(VERSION 3.13)
include(sdk_pico_import.cmake)

project(pico-piano C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

add_executable(midi-controller pico-piano.c usb_descriptors.c)
set_target_properties(midi-controller PROPERTIES COMPILE_FLAGS "-DMIDI_CONTROLLER")

add_executable(worker pico-piano.c)
set_target_properties(worker PROPERTIES COMPILE_FLAGS "-DWORKER")

pico_enable_stdio_usb(midi-controller 0)
pico_enable_stdio_uart(midi-controller 1)
#pico_enable_stdio_usb(worker 1)    # need to remove tinyUSB and its timing/LED stuff
#pico_enable_stdio_uart(worker 0)

# use fast/compact math implementation
pico_set_float_implementation(midi-controller pico)
pico_set_float_implementation(worker pico)

target_include_directories(midi-controller PRIVATE ${CMAKE_CURRENT_LIST_DIR})
target_include_directories(worker PRIVATE ${CMAKE_CURRENT_LIST_DIR})

pico_add_extra_outputs(midi-controller)
target_compile_options(midi-controller PRIVATE -Wall)
target_compile_options(worker PRIVATE -Wall)
target_link_libraries(midi-controller PRIVATE
	pico_stdlib
	pico_multicore
	tinyusb_device
	tinyusb_board
	hardware_adc
	hardware_i2c
	)

pico_add_extra_outputs(worker)
target_link_libraries(worker PRIVATE
	pico_stdlib
	pico_multicore
	tinyusb_device
	tinyusb_board
	hardware_adc
	hardware_i2c
	)
