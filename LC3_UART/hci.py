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

## hci.py
 #
 # Host Controller Interface with a UART transport
 #

import serial
import datetime
from time import sleep
import codecs

class HCI:

    def __init__(self, serial_port):
        self.serial_port = serial_port

    ## Parse int to hex string, LSB first.
     #
     # Reverses a hex number to bytes, LSB first.
    ################################################################################
    def parseIntHexString(self, num, numNibbles=8):

        # Make sure the numNibbles is even
        if(numNibbles % 2 != 0):
            print("Error: numNimbbles must be even")
            return ""

        # Convert int to hex string
        num = hex(int(num))

        # Remove the 0x
        num = num[2:]

        # Add a leading zero if necessary
        if(len(num) % 2 != 0):
            num = "0" + num

        # Make sure we don't overflow numNibbles
        if(len(num) > numNibbles):
            print("Error, numNimbbles overflow")
            return ""

        # Pad out to the number of nibbles
        if(len(num) < numNibbles):
            for i in range (0,(numNibbles - len(num))):
                num = "0"+num

        # Split the number into bytes
        chunks, chunk_size = numNibbles, 2
        addrBytes = [ num[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]

        # Reverse the bytes to LSB first
        numString = ""
        for i in range (int(numNibbles/2)-1, -1, -1):
            numString = numString + addrBytes[i]

        return numString


    ## Wait for an HCI event.
     #
     # Waits for an HCI event, optionally prints the received event. 
     # Will timeout on the serial port if nothing arrives.
    ################################################################################
    def wait_event(self, print_evt = True, timeout=1.0):

        # Set the serial port timeout
        self.serial_port.timeout=timeout

        # Receive the event
        evt=self.serial_port.read(size=1)
        if(len(evt) == 0):
            self.serial_port.flush()
            return ""

        evt=int(codecs.encode(evt, 'hex_codec'),16)
        status_string = '%02X'%evt

        if(evt == 5):
            # Receive the status event
            hdr = self.serial_port.read(size=2)
            hdr=int(codecs.encode(hdr, 'hex_codec'),16)
            packet_len = 0
            status_string+= '%04X'%hdr


        elif(evt == 6):
            # Receive the encode event status
            status = self.serial_port.read(size=1)
            status = int(codecs.encode(status, 'hex_codec'),16)
            status_string+= '%02X'%status

            # Receive the length, byte swap from LSB first
            packet_len0 = self.serial_port.read(size=1)
            packet_len0 = int(codecs.encode(packet_len0, 'hex_codec'),16)
            packet_len1 = self.serial_port.read(size=1)
            packet_len1 = int(codecs.encode(packet_len1, 'hex_codec'),16)

            status_string+= '%02X'%packet_len0
            status_string+= '%02X'%packet_len1
            packet_len = packet_len0 + (packet_len1 << 8)
            packet_len = int(packet_len)

        elif(evt == 7):
            # Receive the encode event status
            status = self.serial_port.read(size=1)
            status = int(codecs.encode(status, 'hex_codec'),16)
            status_string+= '%02X'%status

            # Receive the length, byte swap from LSB first
            packet_len0 = self.serial_port.read(size=1)
            packet_len0 = int(codecs.encode(packet_len0, 'hex_codec'),16)
            packet_len1 = self.serial_port.read(size=1)
            packet_len1 = int(codecs.encode(packet_len1, 'hex_codec'),16)
            
            # Length is number of 16 bit samples
            status_string+= '%02X'%packet_len0
            status_string+= '%02X'%packet_len1
            packet_len = packet_len0 + (packet_len1 << 8)
            packet_len = int(packet_len*2)

        else:
            print("Error: unknown evt = "+str(evt))
            return

        # Read the payload and append to the event
        payload = self.serial_port.read(size=packet_len)
        for i in range(0,packet_len):
            status_string += '%02X'%payload[i]

        # Print the packet
        if(print_evt):
            print(str(datetime.datetime.now()) + " <", status_string)

        return status_string

    ## Wait for HCI events.
     #
     # Waits to receive HCI events, prints the timestamp every 30 seconds.
    ################################################################################
    def wait_events(self, seconds = 2, print_evt = True):
        # Read events from the device for a few seconds
        start_time = datetime.datetime.now()
        delta = datetime.datetime.now() - start_time
        while((delta.seconds < seconds) or (seconds == 0)):
            self.wait_event(print_evt = print_evt, timeout=0.1)
            delta = datetime.datetime.now() - start_time
            if((delta.seconds > 30) and ((delta.seconds % 30) == 0)) :
                print(str(datetime.datetime.now()) + " |")

    ## Send HCI command.
     #
     # Send a HCI command to the serial port. Will add a small delay and wait for
     # and print an HCI event by default.
    ################################################################################
    def send_command(self, packet, resp = True, delay = 0.01, print_cmd = True):
        # Send the command and data
        if(print_cmd):
          print(str(datetime.datetime.now()) + " >", packet)

        self.serial_port.write(bytearray.fromhex(packet))
        sleep(delay)

        if(resp):
            return self.wait_event(print_evt = print_cmd)

    def init_encoder(self, frame_len, sample_rate, bitrate):
        print("Initializing encoder")

        # Send the command to initialize the encoder
        frame_len_str = self.parseIntHexString(frame_len, 2)
        sample_rate_str = self.parseIntHexString(sample_rate, 4)
        bitrate_str = self.parseIntHexString(bitrate, 8)

        status_evt = self.send_command("01"+frame_len_str+sample_rate_str+bitrate_str)

        # Return the status
        if("0501" in status_evt):
            print("Error initializing encoder")
            return False

        return True

    def encode(self, samples):

        # Send the command to encode the samples
        samplesHexString = samples.hex()
        status_evt = self.send_command("02"+samplesHexString, print_cmd=False)

        # Check the error code
        if(status_evt[:4] != "0600"):
            return None

        # Get the number of bytes
        byteCount0 = int(status_evt[4:6],16)
        byteCount1 = int(status_evt[6:8],16)

        # Write the number of bytes at the start of the frame
        frameBytes = bytearray()
        frameBytes.append(byteCount0)
        frameBytes.append(byteCount1)
        byteCount = byteCount0 + (byteCount1 << 8)

        # Split the frame into bytes
        chunks, chunk_size = byteCount*2, 2
        frameBytesString = [ status_evt[8:][i:i+chunk_size] for i in range(0, chunks, chunk_size) ]

        # Convert data from string to bytes
        for byte in frameBytesString:
            frameBytes.append(int(byte,16))

        # Return the encoded data
        return frameBytes
    
    def init_decoder(self, frame_len, sample_rate, bitrate):
        print("Initializing decoder")

        # Send the command to initialize the encoder
        frame_len_str = self.parseIntHexString(frame_len, 2)
        sample_rate_str = self.parseIntHexString(sample_rate, 4)
        bitrate_str = self.parseIntHexString(bitrate, 8)

        status_evt = self.send_command("03"+frame_len_str+sample_rate_str+bitrate_str)

        # Return the status
        if("0501" in status_evt):
            print("Error initializing encoder")
            return False

        return True

    def decode(self, data):

        # Send the command to encode the samples
        dataHexString = data.hex()
        status_evt = self.send_command("04"+dataHexString, print_cmd=False)

        # Check the error code
        if(status_evt[:4] != "0700"):
            return None

        # Get the number of samples
        sampleCount0 = int(status_evt[4:6],16)
        sampleCount1 = int(status_evt[6:8],16)

        sampleCount = sampleCount0 + (sampleCount1 << 8)

        # Split the frame into samples
        chunks, chunk_size = sampleCount*4, 4
        frameSampleString = [ status_evt[8:][i:i+chunk_size] for i in range(0, chunks, chunk_size) ]

        # Convert data from string to bytes
        frameSamples = bytearray()
        for sample in frameSampleString:
            frameSamples.append(int(sample[:2],16))
            frameSamples.append(int(sample[2:],16))

        # Return the encoded data
        return frameSamples