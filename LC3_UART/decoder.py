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

## encoder.py
 #
 # LC3 encoder wrapper
 #

import wave
from hci import HCI

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class Decoder:

    def __init__(self):
        pass

    def decode(hci, input, output):
        print("\nDecoder")

        # Setup the output bin file
        input_bin = open(input, 'rb')

        # Check the file ID
        fileId = input_bin.read(2)
        fileId = int.from_bytes(fileId, 'little')
        if(fileId != 0xcc1c):
            print("Error decoding input bin")
            return 1
        print("fileId: ",hex(fileId))

        headerLen = input_bin.read(2)
        headerLen = int.from_bytes(headerLen, 'little')
        print("headerLen: ", hex(headerLen))

        frameRate = input_bin.read(2)
        frameRate = int.from_bytes(frameRate, 'little')*100
        print("frameRate: ", frameRate)

        bitRate = input_bin.read(2)
        bitRate = int.from_bytes(bitRate, 'little')*100
        print("bitRate: ", bitRate)

        channels = input_bin.read(2)
        channels = int.from_bytes(channels, 'little')
        print("channels: ", channels)

        frameLen = input_bin.read(2)
        frameLen = int.from_bytes(frameLen, 'little')/100
        print("frameLen: ", frameLen)

        rfu = input_bin.read(2)

        signalLen = input_bin.read(4)
        signalLen = int.from_bytes(signalLen, 'little')
        print("signalLen: ", signalLen)

        # Send the command to initialize the decoder
        hci.init_decoder(frameLen, frameRate, bitRate)

        # Setup the wav file
        output_wav = wave.open(output,'wb')

        output_wav.setnchannels(channels)
        output_wav.setsampwidth(2)
        output_wav.setframerate(frameRate)
        output_wav.setnframes(signalLen)

        # Decode each frame
        while(True):
            # Read the number of bytes in the frame
            frame = input_bin.read(2)

            # See if we've reached EOF
            if(len(frame) < 2):
                break

            # Convert to int
            frameBytes = int.from_bytes(frame, 'little')

            # Read the frame, decode and write to the wave file
            frameData = input_bin.read(frameBytes)
            decodedSamples = hci.decode(frameData)
            output_wav.writeframes(decodedSamples)
        
        output_wav.close()

        return 0

### ------------------------------------------------------------------------ ###
