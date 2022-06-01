
***************************************************************************************************************
 Low Complexity Communication Codec - LC3 Conformance Interoperability Test Software Release V1.0.5 2021/10/01

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
**************************************************************************************************************

================================
LC3 Conformance script V0.6.1
================================

Changelog:

0.6.1 - Fixed bitrate in band limitation test (48 kHz 92 kbps -> 96 kbps)
      - Removed obsolete prepare step for 7 kHz and 96 kHz files that was initially used for 
        the sanity-checks test as this test was already removed from the script
      - Removed test_error_detection as it is not featured in the LC3 TS
      - Fixed bitrate in test_low_pass from 80 kbps to 96 kbps as 80 kbps no longer supported for 48 kHz
      - Updated default enabled tests in .cfg files
      - Added additional BAND_LIMITS array for 7.5 ms to account for different bitrates
      
0.6   - Updated copyright header

0.5.5 - imporved logging, small fixes
      - changed scientific to decimal notation in html file
      - simplyfied energy calculation
      - set max. abs. diff. threshold to 0.00148
      - set rms as decoder metric and peaq as encoder/encdec metric
      - renamed test_high_pass test_low_pass
      - added -system_sox option
      
0.5.4 Fixed file alignment for files with same length

0.5.3 Fixed bandlimit test as wrong input items was used

0.5.2 Added frame_ms option

0.5.1 Better command logging

0.5.0 Initial release


Pre-requisites
==============

 - python3
 - python numpy module
 - SoX (http://sox.sourceforge.net), Windows binary (sox-14.4.2-win32.zip), downloaded automatically
 - An ITU-BS.1387 (PEAQ - advanced) implementation
 - On non-Windows platforms: Wine; Win32 is the reference platform to ensure
   bit exact behavior
 - On Windows: Cygwin and the following packages installed through Cygwin:
   -python3
   -numpy
   -curl
   -gcc
   
To-Do's on first time usage
============================

If you are running the script for the very first time, please make sure to do the following things:

-replace "peaq_binary" in desired configuration file by path to PEAQ executables 
-adjust PEAQ regular expression in the configuration file to find ODG of PEAQ output
-create a folder called 'LC3_bin_current' in the same folder as the conformance script and put the reference
 executable provided by Fraunhofer & Ericsson in there, i.e. your structure should look like './LC3_bin_current/LC3.exe'
-set paths to encoder and decoder executables under test in the configuration file [globals]


Usage of the script:
====================

python3 conformanceCheck.py [-h] [-v] [-w WORKERS] [-keep] [-system_sox] CONFIG

LC3 conformance tool - checks if a vendor implementation of the LC3 codec is
conforming to the binary provided by Fraunhofer & Ericsson using PEAQ and RMS metrics.

optional arguments:
  -h, --help      show this help message and exit
  -v              Activate verbose output
  -keep           Keep all files produced in the test run
  -w              Number of workers (threads) for multithreaded execution. Equals number of CPU cores by default.
  -system_sox     Use SoX installed on system instead of Windows binary with Wine

The script requires a configuration file which contains paths to executables and
operating points to be tested. Each test configuration is indicated by a
configuration name in squared brackets. The configuration to be tested is
selected by 'enabled_tests=CONFIG'. A detailed description of the configuration
file can be found in this Readme.

On Windows the script must be executed from Cygwin!


Usage of configuration file
============================

The configuration file is separated in sections by square brackets. Within each
section, variables can be set by 'variable=value'. Text behind a hash # is a
comment and will be ignored.

In the [globals] section, general parameters are defined, e.g. which
configurations to process, paths and command line for the test executables.
This section also specifies the command line for the PEAQ executable and the
regular expression to its output. The example lists all parameters:

[globals]
enabled_tests=Aprofile                                     # configurations to be tested
encoder = CutEnc.exe {input} {output} {bitrate} {options}  # test encoder command line
decoder = CutDec.exe {input} {output} {options}            # test decoder command line
peaq_bin = PQevalAudio {reference} {test}                  # PEAQ command line
peaq_odg_regex = Objective Difference Grade: (-?\d+\.\d+)  # regular expression parsing ODG
frame_ms = 10                                              # Frame size: 10 ms or 7.5 ms

Please note that the user is allowed to change the order of the parameters in {}-brackets above. The script does not care about the order of those parameters.

After the globals section, a number of [test] sections can be
specified describing an individual test for a profile, including operating
points and threshold criteria. The following parameters define a test set:

[Aprofile]                                 # configuration label
# mode can be: encode, decoder, encdec
#         mode, samplingrate, bitrates
configs = encode, 16000, 32000              # SQ sender
          encode, 24000, 48000              # HQ sender

test_sqam           = 1                     # regular sqam test, testing set of files with conditions
test_band_limiting  = 0                     # test band limited signal, e.g. nb signal at 48 kHz
test_low_pass       = 0                     # test for low pass filter of codec for 20 kHz signal
test_rate_switching = 0                     # test for bitrate switching

- default rms threshold is -89 dB RMS and 0.00148 Max.Abs.Diff
- default odg threshold is 0.06
- each line in configs=... defines a new operating point and must be indented
- sampling rate can be 8000, 16000, 24000, 32000, 44100, 48000
- bitrate can be set as single integer or in form of start:step:end
  for example, configure bitrates 16000, 24000, 32000:
    'configs = decode,44100,16000:8000:32000'
- only one mode (e.g. encode) is allowed per [test] section. To test more modes another [test] section has to be added.

By default, all test modes are active and all thresholds are set to their default value. The user is able to deactivate certain tests and to adjust the thresholds.


Limitations
===========

The user can set up a test with a preferred sampling rate and bit rate. However
it is not advised to test narrow band signals at a bitrate higher than 64
kBit/s since most PEAQ implementations have trouble with such signals.
Therefore, the conformance script will reject such configurations.


What does the script produce?
=============================

1.) Command line output with 'passed' or 'failed' results
    encoder/encdec test:
        - passed: if Delta ODG < threshold
                  for all tests
        - failed: if Delta ODG > threshold
                  for any test
    decoder test:
        - passed: if Max.Abs.Diff < threshold and RMS < threshold
                  for all tests
        - failed: if Max.Abs.Diff > threshold or RMS > threshold
                  for any test
              
    + results of other tests like codec limits or bitrate switching

2.) Detailed results are saved in html files. For each configuration, the
    following columns are displayed depending on test mode:
	- Mode: encode, decode or encdec, etc...
	- Item: name of SQAM-item
	- Sampling rate
	- Bitrate
	- Delta ODG (threshold): Absolute Difference between ODG (PEAQ - BS.1387)
      of reference and test.
	- Max. Abs. Diff. (threshold): Maximum of absolute difference between all
      samples of reference and test.
	- RMS (threshold) [dB]: Root Mean Square of difference between reference
      and test in dB.
	- RMS reached (threshold) [bits]: Reached RMS criteria in bits.

If a certain threshold has not been passed for the ODG or RMS criteria, the 
respective cell will appear marked as red. Otherwise it will appear in blue. 
The result files will contain the current date and time as well as the section 
name that was selected in the configuration file.

Each test set will also contain statistics displaying the percentage of passed operating points.


How is conformance measured?
============================

For each test configuration given by 'Mode','Sampling rate' and 'Bitrate' in
the config-file, the script will perform a conformance test on specified
EBU-SQAM items, downloaded from https://tech.ebu.ch/publications/sqamcd. The
stereo items are downmixed to mono ((Ch1 + Ch2) / 2) before further processing.
'Mode' specifies whether encoder or decoder is tested. Mode=encdec runs
encode and decoder in a row (ref_ref.wav vs. tst_tst.wav).

The flow chart below shows exemplary how the conformance metric Delta_ODG is
measured for a certain sqam-item with sampling rate(fs), bitrate(br) and
Mode=encoder

                 sqam-item
                    |
                 resample(fs)
                    |
sqam-item        low pass(20kHz)
    |               |
resample(fs)     reference_encoder(br)
    |               |
low pass(20kHz)  reference_decoder
    |               |
resample(48kHz)  resample(48kHz)
    |               |
align      <->   align
    |               |
orig.wav ------- ref_ref.wav   ------> ODG_ref_ref = PEAQ(orig.wav,ref_ref.wav)---,
                                                                                  |
                 sqam-item                                                        |
                 resample(fs)                                                     |
sqam-item        low pass(20kHz)                                                  |
resample(fs)     'encoder_under_test'(br)                                         |
low pass(20kHz)  reference_decoder                                              -(+)-> abs() -> Delta_ODG(encoder)                                                                |
resample(48kHz)  resample(48kHz)                                                  |
align      <->   align                                                            |
    |               |                                                             |
orig.wav         tst_ref.wav   ------> ODG_tst_ref = PEAQ(orig.wav,tst_ref.wav)---'

The conformance can either be verified by a PEAQ tool using the objective
difference grade (for encoder/encdec tests) 
or by the provided RMS tool (for decoder tests). The RMS tool checks the root mean
square error and the maximum absolute difference between two files and
calculates the k-criteria that should not be lower than a given threshold. The
tool implements the RMS conformance according to the Bluetooth A2DP test
specification, section 6.4.1 [1].

Exemplary flowchart of for RMS conformance metric with sampling rate(fs),
bitrate(br) and Mode=encoder:

sqam-item               sqam-item
resample(fs)            resample(fs)
low pass(20kHz)         low pass(20kHz)
reference_encoder(br)   'encoder_under_test'(br)
reference_decoder       reference_decoder
align           <->     align
   |                       |
tst_ref.wav ---------- ref_ref.wav   ------> RMS( ref_ref - tst_ref)

The default SQAM conformance test can be switched on/off by setting test_sqam = 1/0 in the configuration file.

File alignment:
To compensate small delays between reference and test file before 
evaluation with PEAQ/RMS, the files are aligned.
A maximum delay of 322 samples can be compensated 
and the sample sizes of reference and test file must not differ 
more than 480 samples. The reference binary produces 
a wave file with the original sample size by zero padding.


How does the RMS tool work?
===========================

Usage:
    ./rms file1.wav file2.wav [k]
    Where k is an optional parameter to lower the conformance thresholds in the
    range of 1 to 16.

The RMS tool compares two wave files and calculates the following values:
         - Maximum absolute difference of two samples
         - Overall RMS (Root Mean Squared) value in dB
         - Segmental SNR in dB

The segment length for the segmental SNR is set to 320 samples for all sampling
rates.

More detailed descriptions of the RMS calculations can be found in [1] and [2].

The RMS tool compares the calculated values with the respective thresholds. The
threshold can be lowered by giving an external [k] parameter. If the given RMS
threshold k was not reached, the RMS tool calculates the threshold k' that
would have been reached.


Test for signals higher than 20kHz
==================================
This test is designed to verify the low pass behaviour of LC3 for frequencies 
above 20kHz. For that, the signal White_Noise_HP20 is generated, which consists of
white noise above 20kHz. The energy of the test signal is calculated as shown in 
the flowchart below. The metric En is calculated only for the encoder mode and a 
bitrate(br) of 80 kbps for the item White_Noise_HP20.

White_Noise_HP20
'encoder_under_test'(br)
reference_decoder
  |
tst_ref.wav   ------> En = 10 * log10 ( sum( tst_ref ^2) )

In order to pass the conformance, En must be below the threshold (70 dB) independently 
of the other metrics.

An additional table in the output file lists the tested configurations:
- Mode: encode, decode or encdec
- Item: name of SQAM-item
- Sampling rate
- Bitrate
- Energy (threshold) in dB

The test can be switched on/off by setting test_low_pass = 1/0.


Test for band limited signals
=============================
To test the bandlimited signals, the item SQAM/Female_Speech_German is
resampled and low pass filtered at the following configurations:

 Samplingrate | Bandwidth         | Bitrate
--------------+-------------------+---------
 16000        | NB                | 32000 
 24000        | NB, WB            | 48000
 32000        | NB, WB, SSWB      | 64000
 48000        | NB, WB, SSWB, SWB | 96000

The generated items are then processed using the delta_ODG and RMS criteria as
mentioned above. Since the bandwidth detector is part of the encoder, only the encoder is tested. 
The reference decoder is used to decode both bitstreams (ref_bin, tst_bin). 
This test can be switched on/off by setting test_band_limiting = 1/0.
For the ODG evaluation, the bandlimited file is used as the reference.

Test for bitrate switching
==========================
The conformance tool is also testing the capability of the codec to switch to
a different bitrate during runtime. In order to check that behavior, switching
files are used called 'swf_encoder.dat', 'swf_decoder.dat' and 'swfFirstFrame.dat'. The files are written
in binary 16-bit integer format and contain the bitrate value divided by eight
(8) for each frame. If the end of the file was reached, the file is read again
from the beginning. The bitrate switching test consists of two tests:

1) The SQAM items are coded using the bitrate switching files 'swf_encoder.dat' and 'swf_decoder.dat' with
   the reference and the test codec and compared with PEAQ and RMS. The
   pass/fail criteria for that test is the same as for the SQAM test, i.e.
   there should be no significant quality difference between the two
   implementations.
   The file 'swf_encoder.dat' contains the bitrates 32000, 64000, 96000 and 128000
   bit/s with a respective duration of one second each (equals 100 frames),
   i.e. the first 100 frames shall be coded with 32 kBit/s, the next 100
   frames with 64 kBit/s, etc. This test file is used to test the encoder, i.e. the reference
   and the test encoder are used to create two bitstreams, afterwards those two streams 
   are decoded with the reference decoder.
   For the decoder test (reference encoder, reference decoder + test decoder), the file 'swf_decoder.dat' is used
   which contains the bitrates 32000, 64000, 96000 and 128000 in an arbitrary order with a duration of 10 frames each.
   Both tests should ensure that all codec settings, especially LTPF settings and OLA memory buffers are updated/kept correctly.

2) The SQAM items are coded with the bitrate switching file
   'swfFirstFrame.dat'. The file contains only one bitrate (32000), i.e. the
   test implementation shall switch to that bitrate before the first frame is
   coded and stay with that bitrate. Afterwards, the same files are coded
   directly with a bitrate of 32000 and compared for bit exactness with the RMS
   tool. The test can be considered as passed if the files are bit exact. A
   sampling rate of 48 kHz is used for that test.

The test is optional and can be switched on/off in the configuration file
by setting test_rate_switching = 1/0.
It is required for the test implementation to accept a switching file instead of the bitrate parameter. The test implementation shall 
detect such a switching file, initialize the codec at a dummy bitrate of 16 kbps and switch to the bitrates from the bit rate switching file.


References
==========
[1] Bluetooth A2DP Test Spec, https://www.bluetooth.org/docman/handlers/DownloadDoc.ashx?doc_id=40353
[2] LC3 TS, https://www.bluetooth.org/docman/handlers/downloaddoc.ashx?doc_id=502301

Troubleshooting
===============
Be careful when using quotes in additional arguments passed to the codec under
test, for example:
    RIGHT SYNTAX: var = -f pattern.txt
    WRONG SYNTAX: var = '-f pattern.txt'
