
/*************************************************************************************************************
 Low Complexity Communication Codec - LC3 Conformance Interoperability Test Software Release V1.0.3 2021/06/17

 (C) 2021 Copyright Ericsson AB and Fraunhofer Gesellschaft zur Foerderung
 der angewandten Forschung e.V. for its Fraunhofer IIS.

 This software and/or program is protected by copyright law and international
 treaties and shall solely be used as set out in the
 BLUETOOTH SPECIAL INTEREST GROUP LC3 CONFORMANCE INTEROPERABILTITY
 TEST SOFTWARE END USER LICENSE AGREEMENT
 (EULA, see https://btprodspecificationrefs.blob.core.windows.net/eula-lc3/Bluetooth-SIG-LC3-EULA.pdf)

 No copying, distribution, or use other than as expressly provided in the EULA
 is hereby authorized by implication, estoppel or otherwise.
 All rights not expressly granted are reserved.
**************************************************************************************************************/

Fixed Point Reference Executable
  Encoder Software V1.6.1B
  Decoder Software V1.6.1B


Description
-----------
The software uses fixed-point arithmetic utilizing the ITU-T STL2009 including
the latest updates introduced by 3GPP.


Features
--------
    - Supported configurations:
    8    kHz, 24000 bps (10 ms), 27734 bps (7.5 ms)
    16   kHz, 32000 bps (10 ms and 7.5 ms)
    24   kHz, 48000 bps (10 ms and 7.5 ms)
    32   kHz, 64000 bps (10 ms and 7.5 ms), 61867 bps for 7.5 ms in HFP
    44.1 kHz, 79380 bps, 95550 (95060 bps for 7.5 ms) bps and 123480 bps (10 ms and 7.5 ms)
    48   kHz, 80000 bps, 96000 bps, 124000 bps (10 ms) and 124800 bps (7.5 ms)
    - Frame duration of 10 ms and 7.5 ms
    - Multichannel support by multi-mono coding
    - Packet loss concealment: Standard

Changelog
---------

    - V.1.6.1 2021-06-07
        - Core coder
            - Removed support of multichannel audio
            - Reverted bitstream header to format as in version V1.4.17
            - Added description of missing field in bitstream header (signal_len_red)
            - Corrected size of signal_len field in bitstream header description
            - Updated tinwavein_c.h to most current version
            - Robustness fixes based on code fuzzing

    - V.1.6.0 2021-05-25
        - Core coder
            - Updated supported configurations in LC3 Bluetooth reference binary to match
              LC3 TS section 4 (Test Cases)
            - Removed WMOPS and memory analysis for better performance
            - Robustness fixes based on code fuzzing
            - Dynamic memory optimizations





Usage
-----
    The following example commands explain the usage of the LC3 binary. A
    complete list is available by calling ./LC3 -h.

    To call encoder and decoder at the same time
        ./LC3 INPUT.wav OUTPUT.wav BITRATE

    To call encoder
        ./LC3 -E INPUT.wav OUTPUT.bin BITRATE

    To call decoder
        ./LC3 -D INPUT.bin OUTPUT.wav

    To specify bitrate switching file instead of fixed bitrate
        ./LC3 INPUT.wav OUTPUT.wav FILE
    where FILE is a binary file containing the bitrate as a
    sequence of 64-bit values.


    To disable frame counter (quiet mode)
        ./LC3 -q INPUT.wav OUTPUT.wav BITRATE

    To activate verbose mode (print switching commands)
        ./LC3 -v INPUT.wav OUTPUT.wav BITRATE

    To use the G192 bitstream format
        ./LC3 -E -formatG192 INPUT.wav OUTPUT.g192 BITRATE
        ./LC3 -D -formatG192 INPUT.g192 OUTPUT.wav
    Note that an additional file OUTPUT.cfg will be created by the encoder.
    Note that an additional file INPUT.cfg is expected by the decoder.
    To explicitly specify the configuration file, the flag -cfgG192
    FILE can be used, where FILE is the path to the configuration file.
    Note that the same flags (-formatG192 and -cfgG192) shall be used
    for encoding as well as for decoding,

    To call decoder with frame loss simulations
        ./LC3 -D -epf <FILE> INPUT.bin OUTPUT.wav
        where <FILE> is a binary file containing a sequence of
        16-bit values, non-zero values indicating a frame loss

    To write error detection pattern (from arithmetic decoder) into a 16-bit binary file
        ./LC3 -D -edf  <FILE> INPUT.bin OUTPUT.wav
        where  <FILE> is a binary file containing a sequence of
        16-bit values, non-zero values indicating a detected frame loss

     To set the frame size
        ./LC3 -frame_ms <FRAME_MS> INPUT.wav OUTPUT.wav BITRATE
        where <FRAME_MS> is either 10 or 7.5. The default value is 10 ms.


    The parameter bitrate also allows the usage of switching files
    instead of a fixed number.
    For the bitrate switching, each value in the switching file
    represents a frame's bitrate.

    Switching files can be created with 'gen_rate_profile' available
    from ITU-T G191. If the switching file is shorter than the input it
    is looped from the beginning.  The switching files contain data
    stored as little-endian 64-bit values.

Binary File Format
------------------
    Note: The binary file format is intended only for testing purposes. It is
    not specified in any other location than in this Readme file and may change in the future.
    The file starts with a config header structure as follows.

    Field         Bytes   Content
    ------------------------------------------------------------
    file_id           2       file identifier, value 0xcc1c
    header_size       2       total config header size in bytes
    samplingrate      2       sampling frequency / 100
    bitrate           2       bitrate / 100
    channels          2       number of channels
    frame_ms          2       frame duration in ms * 100
    RFU               2       reserved for future use
    signal_len        2       input signal length in samples
    signal_len_red    2       signal_len >> 16

    All fields are stored in little-endian byte order. The config header could
    be extended in the future so readers should seek up to header_size to skip any
    unknown fields.
    The header is immediately followed by a series of coded audio frames, where
    each frame consists of a two-byte frame length information and the current
    coded frame.
    Note that when reading a bitstream, the LC3 reference binary calculates the signal length as follows:
    uint32_t length = (uint32_t)signal_len | ((uint32_t)signal_len_red << 16);
