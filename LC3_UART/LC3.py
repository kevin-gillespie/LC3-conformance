#! /usr/bin/env python3

################################################################################
 # Copyright (C) 2020 Maxim Integrated Products, Inc., All Rights Reserved.
 #
 # Permission is hereby granted, free of charge, to any person obtaining a
 # copy of this software and associated documentation files (the "Software"),
 # to deal in the Software without restriction, including without limitation
 # the rights to use, copy, modify, merge, publish, distribute, sublicense,
 # and/or sell copies of the Software, and to permit persons to whom the
 # Software is furnished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included
 # in all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 # OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 # MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 # IN NO EVENT SHALL MAXIM INTEGRATED BE LIABLE FOR ANY CLAIM, DAMAGES
 # OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
 # ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 # OTHER DEALINGS IN THE SOFTWARE.
 #
 # Except as contained in this notice, the name of Maxim Integrated
 # Products, Inc. shall not be used except as stated in the Maxim Integrated
 # Products, Inc. Branding Policy.
 #
 # The mere transfer of this software does not imply any licenses
 # of trade secrets, proprietary technology, copyrights, patents,
 # trademarks, maskwork rights, or any other form of intellectual
 # property whatsoever. Maxim Integrated Products, Inc. retains all
 # ownership rights.
 #
 ###############################################################################

## LC3.py
 #
 # LC3 interface using a UART transport.
 #

import serial
import sys
import argparse
from argparse import RawTextHelpFormatter
from encoder import Encoder
from hci import HCI

# Setup the default serial port settings
defaultBaud=115200
defaultSP="/dev/ttyUSB0"

# Setup the command line description text
descText = """
LC3 interface with UART transport.

This tool is used in tandem with the LC3 controller example. This tools sends
commands through the serial port to the target device. It will receive and print
the events received from the target device.

Serial port is configured as 8N1, no flow control, default baud rate of """+str(defaultBaud)+""".
"""

# Parse the command line arguments
parser = argparse.ArgumentParser(description=descText, formatter_class=RawTextHelpFormatter)
parser.add_argument('serialPort', nargs='?', default=defaultSP,
                    help='Serial port path or COM#, default: '+defaultSP)
parser.add_argument('baud', nargs='?', default=defaultBaud,
                    help='Serial port baud rate, default: '+str(defaultBaud))


subparsers = parser.add_subparsers(dest='command')

encode_parser = subparsers.add_parser("E", help="Encode")
dencode_parser = subparsers.add_parser("D", help="Decode")

encode_parser.add_argument('INPUT', help='Input wav file')
encode_parser.add_argument('OUTPUT', help='Output wav file')
encode_parser.add_argument('BITRATE', help='Bitrate for encoding')
encode_parser.add_argument('-fm', '--frame_ms', default="10", help="Frame duration in ms, must be 10 or 7.5, default 10")

dencode_parser.add_argument('INPUT', help='Input wav file')
dencode_parser.add_argument('OUTPUT', help='Output wav file')

args = parser.parse_args()


if(args.command == None):
    print("Must select either E or D")
    exit(1)

# Open the serial port
try:
    # Open serial port
    port = serial.Serial(
        port=str(args.serialPort),
        baudrate=args.baud,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        rtscts=False,
        dsrdtr=False,
        timeout=1.0
    )
    port.isOpen()
except serial.SerialException as err:
    print(err)
    sys.exit(1)

hci = HCI(port)

# Print the arguments
print("LC3 UART tool")
for arg in args.__dict__:
    if args.__dict__[arg] is not None:
        print(str(arg)+ ": "+str(args.__dict__[arg]))

if(args.command == "E"):
    print("Encoding")

    # encoder = Encoder()
    Encoder.encode(hci, args.INPUT, args.OUTPUT, args.BITRATE, args.frame_ms)

else:
    print("TODO: Decode")

