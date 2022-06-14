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
import os

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class Encoder:

    def __init__(self):
        pass



    def encode(hci, input, output, bitrate, frame_len=10):
        print("\nEncoder")
        
        # Parse the wave file
        input_wav = wave.open(input, 'rb')

        nchannels = input_wav.getnchannels()
        samplewidth = input_wav.getsampwidth()
        framerate = input_wav.getframerate()
        nframes = input_wav.getnframes()

        frame_samples = int(framerate*(int(frame_len)/1000))
        frame_count = int(nframes / frame_samples)

        print("Channels     :", nchannels)
        print("Sample width :", samplewidth)
        print("Sample Rate  :", framerate)
        print("Samples      :", nframes)
        print("Frame Len    :", frame_len)
        print("Bitrate      :", bitrate)
        print("Frame samples:", frame_samples)
        print("Frame count  :", frame_count)

        # Send the command to initialize the encoder
        if(not hci.init_encoder(frame_len, framerate, bitrate)):
            return 1

        # wave class calls each sample a frame, whereas we're calling a frame 
        # a set of samples equaling frame_len
        samples = input_wav.readframes(input_wav.getnframes())

        # Segment the samples into frames of frame_len, easy sample is 2 bytes
        frames = chunks(samples, frame_samples*2)

        # Setup the output bin file
        output_bin = open(output, 'wb')
        output_bin.write((0xcc1c).to_bytes(2, 'little')) # File ID
        output_bin.write((0x0012).to_bytes(2, 'little')) # Header length
        output_bin.write(int((int(framerate)/100)).to_bytes(2, 'little'))
        output_bin.write(int((int(bitrate)/100)).to_bytes(2, 'little'))
        output_bin.write((nchannels).to_bytes(2, 'little'))
        output_bin.write(int((int(frame_len)*100)).to_bytes(2, 'little'))
        output_bin.write((0x0000).to_bytes(2, 'little')) # RFU
        output_bin.write((nframes & 0xFFFF).to_bytes(2, 'little'))
        output_bin.write(((nframes & 0xFFFF0000) >> 16).to_bytes(2, 'little'))

        # Save the encoded samples to the output bin file
        for frame in frames:
            # Send the encode command for each frame
            encoded_frame, execTime = hci.encode(frame)

            if(encoded_frame == None):
                print("Error encoding frame")
                return 1

            output_bin.write(encoded_frame)

            print(os.path.basename(input),",",framerate,",",bitrate,",",execTime,", encode")
                
        output_bin.close();

        return 0

### ------------------------------------------------------------------------ ###
