#!/usr/bin/env python3
#
# #/************************************************************************************************************
# Low Complexity Communication Codec - LC3 Conformance Interoperability Test Software Release V1.0.5 2021/10/01
#
# (C) 2021 Copyright Ericsson AB and Fraunhofer Gesellschaft zur Foerderung
# der angewandten Forschung e.V. for its Fraunhofer IIS.
#
# This software and/or program is protected by copyright law and international
# treaties and shall solely be used as set out in the
# BLUETOOTH SPECIAL INTEREST GROUP LC3 CONFORMANCE INTEROPERABILTITY
# TEST SOFTWARE END USER LICENSE AGREEMENT
# (EULA, see https://btprodspecificationrefs.blob.core.windows.net/eula-lc3/Bluetooth-SIG-LC3-EULA.pdf)
#
# No copying, distribution, or use other than as expressly provided in the EULA
# is hereby authorized by implication, estoppel or otherwise.
# All rights not expressly granted are reserved.
# *************************************************************************************************************/
#
# Interoperability/Conformance Script V.0.6.1
#
# Changelog:
# Changelog moved to Readme

import argparse
import configparser
import datetime
import hashlib
import io
import itertools
import logging
import math
import os
import pathlib
import re
import shlex
import shutil
import struct
import subprocess
import sys
import wave
import zipfile
import filecmp
from concurrent.futures import ThreadPoolExecutor
try:
    import numpy
except ImportError:
    sys.exit('Numpy missing! Try running "pip3 install numpy".')
    
VERSION = '0.6.1'

LICENSE = '******************************************************************************************************************\n' \
           '* Low Complexity Communication Codec - LC3 Conformance Interoperability Test Software Release V1.0.5 2021/10/01  *\n' \
           '*                                                                                                                *\n' \
           '* (C) 2021 Copyright Ericsson AB and Fraunhofer Gesellschaft zur Foerderung                                      *\n' \
           '* der angewandten Forschung e.V. for its Fraunhofer IIS.                                                         *\n' \
           '*                                                                                                                *\n' \
           '* This software and/or program is protected by copyright law and international                                   *\n' \
           '* treaties and shall solely be used as set out in the                                                            *\n' \
           '* BLUETOOTH SPECIAL INTEREST GROUP LC3 CONFORMANCE INTEROPERABILTITY                                             *\n' \
           '* TEST SOFTWARE END USER LICENSE AGREEMENT                                                                       *\n' \
           '* (EULA, see https://btprodspecificationrefs.blob.core.windows.net/eula-lc3/Bluetooth-SIG-LC3-EULA.pdf).         *\n' \
           '*                                                                                                                *\n' \
           '* No copying, distribution, or use other than as expressly provided in the EULA                                  *\n' \
           '* is hereby authorized by implication, estoppel or otherwise.                                                    *\n' \
           '* All rights not expressly granted are reserved.                                                                 *\n' \
           '*                                                                                                                *\n' \
           '* Interoperability/Conformance Script V.{}                                                                    *\n' \
           '******************************************************************************************************************\n' \


# constants
MAX_DELAY = 322 # maximum in samples for 7.5ms framing at 44.1 kHz
MAX_SAMPLES_PER_FRAME = 480
SAMPLERATES = [8000, 16000, 24000, 32000, 44100, 48000]
SQAM_URL = 'https://tech.ebu.ch/docs/testmaterial/SQAM_FLAC.zip'
SQAM_SHA256 = '7d6fcd0fc42354637291792534b61bf129612f221f8efef97b62e8942a8686aa'
SOX_URL = 'https://sourceforge.net/projects/sox/files/sox/14.4.2/sox-14.4.2-win32.zip'
SOX_SHA256 = '8072cc147cf1a3b3713b8b97d6844bb9389e211ab9e1101e432193fad6ae6662'
SOX_EXE = pathlib.Path('SoX', 'sox-14.4.2', 'sox.exe')
RMS_EXE = './rms' if sys.platform != 'cygwin' else './rms.exe'
REFERENCE_ENCODER = 'LC3_bin_current/LC3.exe -E -q {options} "{input}" "{output}" {bitrate}'
REFERENCE_DECODER = 'LC3_bin_current/LC3.exe -D -q {options} "{input}" "{output}"'

ITEM_DIR = pathlib.Path('test_items')
ITEMS = {  # start, frag, SQAM name
    'ABBA': (7, 8, '69.flac'),
    'Castanets': (0, 8, '27.flac'),
    'Eddie_Rabbitt': (0, 8, '70.flac'),
    'Female_Speech_German': (0, 8, '53.flac'),
    'Glockenspiel': (0, 10, '35.flac'),
    'Piano_Schubert': (0, 8, '60.flac'),
    'Violoncello': (0, 10, '10.flac'),
    'Harpsichord': (39, 9, '40.flac'),
    'Male_Speech_English': (0, 8, '50.flac')
}
ITEM_HIGH_PASS = 'White_Noise_HP20'
ITEM_BAND_LIMIT = 'Female_Speech_German'
ITEM_RATE_SWITCHING = 'ABBA'
# Sampling rate, band width, bit rate
BAND_LIMITS_10MS = {
    16000: ([8000], 32000),
    24000: ([8000, 16000], 48000),
    32000: ([8000, 16000, 24000], 64000),
    44100: ([8000, 16000, 24000, 32000], 95550),
    48000: ([8000, 16000, 24000, 32000], 96000)
}

BAND_LIMITS_75MS = {
    16000: ([8000], 32000),
    24000: ([8000, 16000], 48000),
    32000: ([8000, 16000, 24000], 64000),
    44100: ([8000, 16000, 24000, 32000], 95060),
    48000: ([8000, 16000, 24000, 32000], 96000)
}

BANDWIDTHS = {8000: 'nb', 16000: 'wb', 24000: 'sswb', 32000: 'swb', 48000: 'fb'}

# config default values
DEFAULTS = {
    'configs':                 [],
    'high_pass_eng_threshold': 70,
    'metric':                  ('peaq', 'rms'),
    'test_band_limiting ':     True,
    'test_low_pass':           True,
    'test_rate_switching':     True,
    'test_sqam':               True,
}
METRICS = {
    'encode': 'peaq',
    'decode': 'rms',
    'encdec': 'peaq'
}
TEST_MODES = ['encode', 'decode', 'encdec', 'rate_switching_enc', 'rate_switching_ff', 'rate_switching_dec']
for mode in TEST_MODES:
    DEFAULTS[mode + '_odg_threshold'] = 0.06
    DEFAULTS[mode + '_rms_threshold'] = 14
    DEFAULTS[mode + '_mad_threshold'] = 0.00148 #1/(2**(14 - 4.6)) 

# html output stuff
HEADER_ALL  = ['Mode', 'Item', 'Samplingrate', 'Bitrate']
HEADER_PEAQ = ['ODG Ref', 'Delta ODG (threshold)']
HEADER_RMS  = ['Max. Abs. Diff (threshold)', 'RMS (threshold) [dB]', 'RMS reached (threshold) [bits]']
HEADER_OPT  = {'peaqrms':HEADER_PEAQ + HEADER_RMS, 'peaq':HEADER_PEAQ, 'rms': HEADER_RMS}
HEADER_ED   = ['Error Patterns match']
HEADER_HP20 = ['Energy (threshold) [dB]']
HEADER_CAP  = ['Capabilities confirmed']
HEADER = {
    'test_band_limiting'  : ('Band-limited signals', HEADER_OPT),
    'test_low_pass'       : ('Signals above 20kHz', HEADER_HP20),
    'test_rate_switching' : ('Bitrate switching', HEADER_OPT),
    'test_sqam'           : ('SQAM items', HEADER_OPT),
}
HTML_HEAD = ('<!DOCTYPE html><head><title>{title} Report</title><style>{style}</style></head><body>'
             '<h2>Conformance test for "{title}" (Frame Size {frame_ms} ms) {state}!</h2>')
HTML_TABLE_HEAD = '<div><table><tr><h3>{title}</h3></tr>\n'
HTML_TABLE_TAIL = '</table></div>'
HTML_TAIL = '</body>'
STYLE = ('body {font-family:sans-serif; color:#f8f8f2; background-color:#272822; font-size:80%} div {border:1px solid '
         '#8f908a; border-radius:4px; overflow:hidden; display:table; margin-left:30px; margin-bottom:30px} h2 {text-a'
         'lign:left; margin-left:30px} h3 {text-align:left; margin:4px} table {border-spacing:0px} th {padding:4px} td'
         ' {padding:4px} tr:nth-child(even) {background-color:rgba(255,255,255,0.1)} td.pass {background-color:rgba(0,'
         '192,255,0.4)} td.fail {background-color:rgba(255,0,0,0.4)} td.warn {background-color:rgba(214,137,16,0.4)}')


# convenience wrapper for os.makedirs
def makedirs(path):
    os.makedirs(str(path), exist_ok=True)
    return path

# returns true if path is a file
def is_file(path):
    return os.path.isfile(str(path))

# Run command and return output. cmd can be string or list. Commands with .exe suffix are automatically
# called with wine unless wine=False. Set unicode=False to get binary output. Set hard_fail=False to
# to ignore nonzero return codes.
def call(cmd, wine=True, unicode=True, hard_fail=True, log_output=True):
    if isinstance(cmd, str):
        cmd = [x for x in shlex.split(cmd) if x]
    if sys.platform != 'cygwin' and wine and cmd[0].lower().endswith('.exe'):
        cmd = ['wine'] + cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=unicode)
    out = p.communicate()[0] or (b'', '')[unicode]
    quoted_cmd = ' '.join(map(shlex.quote, cmd))
    now = datetime.datetime.now().strftime('%H:%M:%S')
    logging.debug('[{}] '.format(now) + quoted_cmd)
    if unicode and log_output:
        logging.debug(out)
    if hard_fail and p.returncode != 0:
        raise OSError(quoted_cmd + ' failed!')
    return out


# return url as as bytes object, validate against hash
def download(url, sha256=None):
    try:
        buf = call('curl --silent -L "{}"'.format(url), unicode=False)
    except OSError:
        sys.exit('Failed to download {}!'.format(url))
    if sha256 and hashlib.sha256(buf).hexdigest() != sha256:
        sys.exit('Failed to validate hash for {}!'.format(url))
    return buf


def download_sox():
    if not is_file(SOX_EXE):
        print('Downloading SoX ...')
        buf = download(SOX_URL, SOX_SHA256)
        zipfile.ZipFile(io.BytesIO(buf)).extractall(str(SOX_EXE.parent.parent))
        if sys.platform == 'cygwin':
            call('chmod -R +x "{}"'.format(SOX_EXE.parent))


def exe_exists(exe, wine=False):
    try:
        out = call(exe, wine=wine, hard_fail=False)
    except OSError:
        return False
    return not (wine and out.startswith('wine: ')) # detect wine: cannot find


def check_system(globvars):
    if sys.platform == 'win32':
        sys.exit('This script should run under cygwin')
    if not exe_exists('curl'):
        sys.exit('Curl not found')
    if sys.platform != 'cygwin' and not exe_exists('wine'):
        sys.exit("Wine not found")
    if not exe_exists('gcc'):
        sys.exit("Gcc not found")
    if not exe_exists(globvars['peaq_bin'], wine=True):
        sys.exit('{} not found. \nPlease install a PEAQ compliant tool (e.g. PEAQ ITU-BS.1387) and adjust config file'
                 .format(globvars['peaq_bin']))
    if not exe_exists(globvars['encoder'], wine=True):
        sys.exit('{} not found. \nPlease provide the test implementation of the LC3 encoder'
                 .format(globvars['encoder']))
    if not exe_exists(globvars['decoder'], wine=True):
        sys.exit('{} not found. \nPlease provide the test implementation of the LC3 decoder'
                 .format(globvars['decoder']))


def regex_search(expr, s):
    if not re.search(expr, s):
        sys.exit('No match for regular expression "{}"!'.format(expr))
    return re.search(expr, s).group(1)


# calculates the max xcorr of the two vectors 
def align_vec(x1, x2):
    # trims second vector(tst) to be in sync with first(ref)
    res = []
    # normalize to max of int16
    a = numpy.float32(x1) / 32767
    # padd with zeros in beginning
    x2 = (0,)*MAX_DELAY + x2
    b = numpy.float32(x2) / 32767

    for i in range(2*MAX_DELAY + 1):
        xlen = min(len(a),len(b)) - i
        xx = numpy.dot(a[0:xlen], b[i:xlen+i])
        res.append(xx)
    lag = numpy.array(res).argmax()
    x2 = x2[lag:]
    # padd/trim second vector(tst)
    logging.debug('[{}] Compensated delay: {} samples'.format(datetime.datetime.now().strftime('%H:%M:%S'), MAX_DELAY - lag))
    if len(x1)>len(x2):
        x2 = x2 + (0,)*(len(x1)-len(x2)) 
    else:
        x2 = x2[:len(x1)]
    return x2


# convert byte objects to signed int16
def byte_to_float(b, frames, channels):
    return struct.unpack("%ih" % (frames * channels), b)


# trim/padd file_2 to be in sync with file_1 and write to file_2.aligned.wav
def align_files(file_1, file_2, file_2_out):
    logging.debug('[{}] File alignment:\nFile to be aligned: "{}"\nReference file: "{}"\nAligned output file: "{}"'.format(datetime.datetime.now().strftime('%H:%M:%S'), file_2,file_1,file_2_out))
    file_1, file_2, file_2_out = str(file_1), str(file_2), str(file_2_out)
    # read in audio files
    with wave.open(file_1, 'rb') as wf1, wave.open(file_2, 'rb') as wf2:
        if abs(wf1.getnframes() - wf2.getnframes()) > MAX_SAMPLES_PER_FRAME:
            print('The difference between the number of samples in {} and {} is higher than {}'.format(file_1,file_2, MAX_SAMPLES_PER_FRAME))
            print('{}: {} samples'.format(file_1,wf1.getnframes()))
            print('{}: {} samples'.format(file_2,wf2.getnframes()))
            exit()
        b1 = wf1.readframes(wf1.getnframes())
        b2 = wf2.readframes(wf2.getnframes())
        x1 = byte_to_float(b1, wf1.getnframes(), wf1.getnchannels())
        x2 = byte_to_float(b2, wf2.getnframes(), wf2.getnchannels())
        par2 = wf2.getparams()
    # measure cross correlation -> delay between files and return trimmed vector
    y2 = align_vec(x1, x2)
    # write output file
    with wave.open(file_2_out, 'wb') as wf2:
        wf2.setparams(par2)
        wf2.setnframes(len(y2))
        b2 = struct.pack("%ih" % len(y2), *y2)
        wf2.writeframes(b2)


def build_tools():
    call('gcc -o rms rms.c -lm')


# call sox with args in repeatable mode, lazy skips execution if output already exists
def sox(*args, lazy=False):
    wavs = [x for x in map(str, args) if x.endswith('.wav')]
    if not (lazy and os.path.isfile(wavs[-1])): # last .wav is assumed to be output
        call('{} -R {}'.format(SOX_EXE, ' '.join(map(str, args))))


def resample(infile, outfile, fs, lazy=False):
    sox(infile, outfile, 'rate -vs', fs, lazy=lazy)


def low_pass(infile, outfile, fs, fc, lazy=False):
    tmpfile = infile.with_suffix('.{}k.wav'.format(fc // 1000))
    resample(infile, tmpfile, fc, lazy=lazy)
    resample(tmpfile, outfile, fs, lazy=lazy)


# apply func to list of argumets,
def thread_executor(func, args, workers):
    list(ThreadPoolExecutor(workers).map(lambda x: func(*x), args)) # list() to collect futures


def prepare_items(workers):
    fade_in, fade_out = 0.5, 0.7
    sqam_dir = pathlib.Path('SQAM')
    item_dir = makedirs(ITEM_DIR)
    if not sqam_dir.exists():
        print('Downloading test items ...')
        buf = download(SQAM_URL, SQAM_SHA256)
        zipfile.ZipFile(io.BytesIO(buf)).extractall(str(sqam_dir))

    def trim(name, start, end, iname):
        infile  = sqam_dir / iname
        outfile = item_dir / (name + '.wav')
        tmpfile = outfile.with_suffix('.tmp.wav')
        sox(infile, tmpfile, 'trim', start, end, 'remix -', lazy=True)
        wf = wave.open(str(tmpfile))
        length = wf.getnframes() / wf.getframerate()
        sox(tmpfile, outfile, 'fade', fade_in, length, fade_out, lazy=True)

    def resamp(name, fs):
        infile  = item_dir / (name + '.wav')
        outfile = item_dir / '{}_{}.wav'.format(name, fs)
        resample(infile, outfile, fs, lazy=True)

    def lpass20k(name, fs):
        infile  = item_dir / '{}_{}.wav'.format(name, fs)
        outfile = infile.with_suffix('.lp20.wav')
        low_pass(infile, outfile, fs, 40000, lazy=True)

    def blimit(fs, br, bw):
        infile = item_dir / '{}_{}.wav'.format(ITEM_BAND_LIMIT, fs)
        outfile = item_dir / '{}_{}_{}.wav'.format(ITEM_BAND_LIMIT, fs, BANDWIDTHS[bw])
        low_pass(infile, outfile, fs, bw, lazy=True)

    misc = [
        # HP20 item with 4 seconds of white noise above 20kHz
        lambda : sox('-n -r 48000 -c 1 -b 16', item_dir / (ITEM_HIGH_PASS + '.wav'), 'synth 4 white fir hp_fir_coef.txt', lazy=True),
        # rate switching item
        lambda: sox(item_dir / (ITEM_RATE_SWITCHING + '.wav'), item_dir / (ITEM_RATE_SWITCHING + '_16000.wav'), 16000, lazy=True),
    ]

    print('Preparing test items ...')
    thread_executor(trim, ((name, st, fr, iname) for name, (st, fr, iname) in ITEMS.items()), workers)
    thread_executor(resamp, itertools.product(ITEMS, SAMPLERATES), workers)
    thread_executor(lpass20k, itertools.product(ITEMS, (f for f in SAMPLERATES if f >= 44100)), workers)
    
    thread_executor(blimit, ((fs, br, bw) for fs, (bws, br) in BAND_LIMITS_10MS.items() for bw in bws), workers)
    thread_executor(lambda x: x(), ([f] for f in misc), workers)


def parse_config(path):
    def strip_comment(line):
        return line.split('#', 1)[0].strip()

    def split_list(line):
        return [x.strip() for x in strip_comment(line).split(',')]

    def parse_conf_line(line):
        try:
            mode, fs, br = split_list(line)
            if int(fs) not in SAMPLERATES:
                sys.exit('Unsupported sampling rate: {}!'.format(fs))
            if ':' in br:
                br_start, br_step, br_stop = map(int, br.split(':'))
                fs, br = int(fs), list(range(br_start, br_stop + 1, br_step))
            else:
                fs, br = int(fs), [int(br)]
            if fs == 8000 and max(br) > 64000:
                sys.exit('Narrowband (8 kHz) must use bitrates below 64 kBit/s')
            return mode, fs, br
        except ValueError:
            sys.exit('Syntax error in test config "{}"!'.format(line))

    if not os.path.isfile(path):
        sys.exit('No such file: ' + path)

    glob_keys = ['enabled_tests', 'encoder', 'decoder', 'peaq_bin', 'peaq_odg_regex', 'frame_ms']
    bool_keys = ['test_sqam', 'test_band_limiting',
	             'test_low_pass', 'test_rate_switching']
    str_keys  = ['options']
    globvars, tests = {}, {}

    try:
        parser = configparser.ConfigParser()
        parser.read(path)
        # parse global section
        for key in glob_keys:
            globvars[key] = strip_comment(parser['globals'][key])
        globvars['enabled_tests'] = split_list(parser['globals']['enabled_tests'])
        for key in parser['globals']:
            if key not in glob_keys:
                sys.exit('Unknown key "{}" in config'.format(key))
        # parse test sections
        for test in globvars['enabled_tests']:
            tests[test] = DEFAULTS.copy()
            for key in parser[test]:
                val = strip_comment(parser[test][key])
                if key in bool_keys:
                    tests[test][key] = val == '1'
                elif key in str_keys:
                    tests[test][key] = val
                elif key == 'configs':
                    tests[test]['configs'] = [parse_conf_line(l) for l in parser[test]['configs'].splitlines()]
                    mode = tests[test]['configs'][0][0]
                    if set([mode]) != set([l[0] for l in tests[test]['configs']]):
                        sys.exit('multiple modes in one test not allowed!')
                    tests[test]['metric'] = METRICS[mode]
                elif key.endswith('_threshold') and key in DEFAULTS:
                    try:
                        tests[test][key] = float(val)
                    except ValueError:
                        sys.exit('Invalid number in config: {} = {}'.format(key, val))
                else:
                    sys.exit('Unknown key "{}" in config'.format(key))
            tests[test].update(globvars)
    except KeyError as e:
        sys.exit('Missing "{}" in config'.format(e.args[0]))
    except configparser.DuplicateOptionError as e:
        sys.exit('Duplicate key "{}" in config'.format(e.args[1]))

    return globvars, tests


def compare_wav_energy(infile, reference, test, config, *_):
    eng = calc_energy(test)
    thresh = DEFAULTS['high_pass_eng_threshold']
    ok = eng <= thresh
    return ok, [(eng, ('fail', 'pass')[ok], thresh)]


def check_odg(mode, config, odg_ref, odg_tst, odg_thr_key):
    odg_diff = abs(odg_ref - odg_tst)
    odg_diff_thr = config[mode + '_odg_threshold']
    ok = odg_diff <= odg_diff_thr
    result = [(odg_ref, '', None), (odg_diff, ('fail', 'pass')[ok], odg_diff_thr)]
    if odg_thr_key:
        odg_thr = config[odg_thr_key]
        result.append((odg_tst, ('warn', 'none')[odg_tst >= odg_thr], odg_thr))
    return ok, result


def check_rms(mode, config, rms, bits, diff):
    rms_bits = config[mode + '_rms_threshold']
    rms_thr = 20 * math.log10(2 ** (-rms_bits + 1) / 12 ** 0.5)
    diff_thr = config[mode + '_mad_threshold']
    ok_rms, ok_diff = rms <= rms_thr, diff <= diff_thr
    result = [(diff,  ('fail', 'pass')[ok_diff], diff_thr),
              (rms, ('fail', 'pass')[ok_rms], rms_thr),
              (bits, ('warn', 'none')[bits >= rms_bits], rms_bits)]
    return ok_rms and ok_diff, result


def compare_wav(infile, reference, test, config, rms_thr_key, odg_thr_key=None):
    ok_peaq, result_peaq = False, []
    ok_rms, result_rms = False, []
    
    ref_al = reference.with_suffix('.aligned.wav')
    tst_al = test.with_suffix('.aligned.wav')

    align_files(infile, reference, ref_al)
    align_files(infile, test, tst_al)

    if 'peaq' in config['metric']:
        in48 = infile.with_suffix('.48k.wav')
        ref48 = ref_al.with_suffix('.48k.wav')
        tst48 = tst_al.with_suffix('.48k.wav')
        resample(infile, in48, 48000)
        resample(ref_al, ref48, 48000)
        resample(tst_al, tst48, 48000)
        # calculate odg between input and reference / test
        out_ref = call(config['peaq_bin'].format(reference=in48, test=ref48))
        odg_ref = float(regex_search(config['peaq_odg_regex'], out_ref))
        out_tst = call(config['peaq_bin'].format(reference=in48, test=tst48))
        odg_tst = float(regex_search(config['peaq_odg_regex'], out_tst))
        ok_peaq, result_peaq = check_odg(mode, config, odg_ref, odg_tst, odg_thr_key)

    if 'rms' in config['metric']:
        # calculate rms between reference and test
        out = call('{} {} {} {}'.format(RMS_EXE, ref_al, tst_al, config[rms_thr_key]))
        diff_samp = int(regex_search(r'different samples\s+: (\d+)', out))
        if diff_samp != 0:
            rms = float(regex_search(r'Overall RMS value\s+: (\S+) dB ---', out))
            diff = float(regex_search(r'Maximum difference\s+: (\S+) ---', out))
            bits = int(regex_search(r'RMS criteria\s+: (\d+) bit', out))
        else:
            rms, diff, bits = -999, 0, 24
        ok_rms, result_rms = check_rms(mode, config, rms, bits, diff)

    return ok_peaq or ok_rms, result_peaq + result_rms


# create file names for test
def make_files(files, work_dir, test, mode, item, fs, br):
    test_dir = makedirs(work_dir / test)
    protoyp = '{}_{}_{}_{}_'.format(mode, item, fs, br)
    return tuple(test_dir / (protoyp + f) for f in files)


# permutate test configs
def sqam_configs(config, items=ITEMS, lp20=False, bitrates=None, modes=None):
    for mode, fs, brs in config['configs']:
        if modes and mode not in modes:
            continue
        for item, br in itertools.product(items, bitrates or brs):
            infile = ITEM_DIR / '{}_{}.wav'.format(item, fs)
            if fs in (44100, 48000) and lp20:
                infile = infile.with_suffix('.lp20.wav')
            yield mode, item, fs, br, infile


def print_test(test, item, fs, br):
    print('Testing', test, '-', item, 'at', fs, 'Hz and', br, 'bit/s ...')


# apply test func to list of tests, multithreadded
def test_executor(func, tests, workers):
    return {cfg:res for cfg, res in ThreadPoolExecutor(workers).map(lambda x: func(*x), tests)}


def test_rate_switching(work_dir, test, config, workers):
    def func(mode, item, fs, br, infile):
        if mode == 'encode':
            print_test('bitrate switching ' + mode, item, fs, "swf_encoder.dat")
            cfg = ('rate_switching_enc', item, fs, br)
            file_names = ['tst.bin', 'ref.bin', 'ref_ref.wav', 'tst_ref.wav']
            tst_bin, ref_bin, ref_ref, tst_ref = make_files(file_names, work_dir, test, *cfg)
            call(config['encoder'].format(input=infile, output=tst_bin, bitrate='swf_encoder.dat', frame_ms=config['frame_ms'], options=''))
            call(REFERENCE_ENCODER.format(input=infile, output=ref_bin, bitrate='swf_encoder.dat', options='-frame_ms ' + config['frame_ms']))
            call(REFERENCE_DECODER.format(input=tst_bin, output=tst_ref, options=''))
            call(REFERENCE_DECODER.format(input=ref_bin, output=ref_ref, options=''))
            return cfg, compare_wav(infile, ref_ref, tst_ref, config, 'rate_switching_enc_rms_threshold')
        if mode == 'decode':
            print_test('bitrate switching ' + mode, item, fs, "swf_decoder.dat")
            cfg = ('rate_switching_dec', item, fs, br)
            file_names = ['ref.bin', 'ref_ref.wav', 'ref_tst.wav']
            ref_bin, ref_ref, ref_tst = make_files(file_names, work_dir, test, *cfg)
            call(REFERENCE_ENCODER.format(input=infile, output=ref_bin, bitrate='swf_decoder.dat', options='-frame_ms ' + config['frame_ms']))
            call(REFERENCE_DECODER.format(input=ref_bin, output=ref_ref, options=''))
            call(config['decoder'].format(input=ref_bin, output=ref_tst, options=''))
            return cfg, compare_wav(infile, ref_ref, ref_tst, config, 'rate_switching_dec_rms_threshold')

    tests = sqam_configs(config, modes=['encode', 'decode'], bitrates=['NA'])
    result = test_executor(func, tests, workers)

    fs, br = 16000, 'NA'
    print_test('bitrate switching (first frame)', ITEM_RATE_SWITCHING, fs, br)
    infile = ITEM_DIR / '{}_{}.wav'.format(ITEM_RATE_SWITCHING, fs)
    cfg = ('rate_switching_ff', ITEM_RATE_SWITCHING, fs, br)
    file_names = ['ref.bin', 'tst.bin', 'ref_ref.wav', 'tst_tst.wav']
    ref_bin, tst_bin, ref_ref, tst_tst = make_files(file_names, work_dir, test, *cfg)
    call(config['encoder'].format(input=infile, output=tst_bin, bitrate='swfFirstFrame.dat', frame_ms=config['frame_ms'], options=''))
    call(config['decoder'].format(input=tst_bin, output=tst_tst, options=''))
    call(config['encoder'].format(input=infile, output=ref_bin, bitrate=16000, frame_ms=config['frame_ms'], options=''))
    call(config['decoder'].format(input=tst_bin, output=ref_ref, options=''))
    result[cfg] = compare_wav(infile, ref_ref, tst_tst, config, 'rate_switching_ff_rms_threshold')
    return result


def test_item(work_dir, test, config, infile, mode, item, fs, br, compare=compare_wav):
    file_names = ['ref.bin', 'tst.bin', 'ref_ref.wav', 'tst_tst.wav', 'ref_tst.wav', 'tst_ref.wav']
    file_tuple = make_files(file_names, work_dir, test, mode, item, fs, br)
    ref_bin, tst_bin, ref_ref, tst_tst, ref_tst, tst_ref = file_tuple
    call(REFERENCE_ENCODER.format(input=infile, output=ref_bin, bitrate=br, options='-frame_ms ' + config['frame_ms']))
    call(REFERENCE_DECODER.format(input=ref_bin, output=ref_ref, options=''))
    if mode.startswith('encode'):
        call(config['encoder'].format(input=infile, output=tst_bin, bitrate=br, frame_ms=config['frame_ms'], options=''))
        call(REFERENCE_DECODER.format(input=tst_bin, output=tst_ref, options=''))
        return compare(infile, ref_ref, tst_ref, config, 'encode_rms_threshold')
    if mode.startswith('decode'):
        call(config['decoder'].format(input=ref_bin, output=ref_tst, options=''))
        return compare(infile, ref_ref, ref_tst, config, 'decode_rms_threshold')
    if mode.startswith('encdec'):
        call(config['encoder'].format(input=infile, output=tst_bin, bitrate=br, frame_ms=config['frame_ms'], options=''))
        call(config['decoder'].format(input=tst_bin, output=tst_tst, options=''))
        return compare(infile, ref_ref, tst_tst, config, 'encdec_rms_threshold')


def test_sqam(work_dir, test, config, workers):
    def func(mode, item, fs, br, infile):
        print_test('sqam ' + mode, item, fs, br)
        cfg = (mode, item, fs, br)
        return cfg, test_item(work_dir, test, config, infile, *cfg)

    return test_executor(func, sqam_configs(config, lp20=True), workers)


def test_low_pass(work_dir, test, config, workers):
    if set(mode for mode, *_ in config['configs']) & {'encode', 'encdec'}:
        fs, br = 48000, 96000
        print_test('high pass filter', ITEM_HIGH_PASS, fs, br)
        cfg = ('encode', ITEM_HIGH_PASS, fs, br)
        infile = ITEM_DIR / (ITEM_HIGH_PASS + '.wav')
        res = test_item(work_dir, test, config, infile, *cfg, compare=compare_wav_energy)
        return {cfg:res}
    return {}


def test_band_limiting(work_dir, test, config, workers):
    infile = ITEM_DIR / (ITEM_BAND_LIMIT + '.wav')
    def func(fs, br, bw):
        item = '{}_{}_{}'.format(ITEM_BAND_LIMIT, bw, BANDWIDTHS[bw])
        item_in = ITEM_DIR / '{}_{}_{}.wav'.format(ITEM_BAND_LIMIT, fs, BANDWIDTHS[bw]) 
        print_test('bandwidth detector (encoder)', item, fs, br)
        cfg = ('encoder', item, fs, br)
        file_names = ['tst.bin', 'ref.bin', 'ref_ref.wav', 'tst_ref.wav']
        
        tst_bin, ref_bin, ref_ref, tst_ref = make_files(file_names, work_dir, test, *cfg)
        call(config['encoder'].format(input=item_in, output=tst_bin, bitrate=br, frame_ms=config['frame_ms'], options=''))
        call(REFERENCE_ENCODER.format(input=item_in, output=ref_bin, bitrate=br, options='-frame_ms ' + config['frame_ms']))
        call(REFERENCE_DECODER.format(input=tst_bin, output=tst_ref, options=''))
        call(REFERENCE_DECODER.format(input=ref_bin, output=ref_ref, options=''))
        return cfg, compare_wav(item_in, ref_ref, tst_ref, config, 'encode_rms_threshold')

    rates = set(fs for mode, fs, _ in config['configs'] if mode in ('encode', 'encdec'))
    
    if config['frame_ms'] == '10':
        bandlimits_array = BAND_LIMITS_10MS
    else:
        bandlimits_array = BAND_LIMITS_75MS
    
    tests = [(fs, br, bw) for fs, (bws, br) in bandlimits_array.items() for bw in bws if fs in rates]
    return test_executor(func, tests, workers)


def calc_energy(test):
    with wave.open(str(test), 'rb') as tst_wf:
        bytes_tst = tst_wf.readframes(tst_wf.getnframes())
        tst = byte_to_float(bytes_tst, tst_wf.getnframes(), tst_wf.getnchannels())
        eng = sum(numpy.square(tst))
        return 10 * math.log10(eng)


def check_results(results):
    return all(ok for test in results for ok, _ in results[test].values())


def fstr(x, d_num):
    # converts float to string in format 0.00000XXX wihtout scientific notation 
    # d_num is the number of non-zero digits (number of X in 0.00000XXX)
    if type(x) == float:
        if x == 0:
            return '0'
        if abs(x) < 1:
            e=int(numpy.floor(numpy.log10(abs(x))))
            fff='{{:.{}f}}'.format(-e+d_num-1)
            out = fff.format(x)
            while out[-1] == '0':
                out = out[:-1]
        if abs(x) > 1:
            fff='{{:.{}f}}'.format(d_num)
            out = fff.format(x)
            if out[-3:] == '.00':
                out = out[:-3]
            if out[-2:] == '.0':
                out = out[:-2]
            if out[-1:] == '0' and out[-3] == '.':
                out = out[:-1]
        return out
    else:
        return str(x)



def table_stats(results, header):
    header = header[len(HEADER_ALL):] # extract column values
    passed = round(100 * sum(ok for ok, _ in results.values()) / (len(results) or 1))
    head   = ' - {}%'.format(passed)
    stats  = ['worst value'] + [''] * (len(HEADER_ALL) - 1)
    if header in (HEADER_PEAQ + HEADER_RMS, HEADER_PEAQ):
        stats += ['', fstr(max(x[1][1][0] for x in results.values()),3)]
    if header in (HEADER_PEAQ + HEADER_RMS, HEADER_RMS):
        pos = 0 if header == HEADER_RMS else 2
        stats += [fstr(max(x[1][pos + 0][0] for x in results.values()),3)]
        stats += [fstr(max(x[1][pos + 1][0] for x in results.values()),3)]
        stats += [ str(min(x[1][pos + 2][0] for x in results.values()))]
    return head, stats


def write_table(htmlfile, results, config, title, header):
    header = HEADER_ALL + (header if type(header) == list else header[''.join(config['metric'])])
    percent, stats = table_stats(results, header)
    htmlfile.write(HTML_TABLE_HEAD.format(title=title + percent))
    htmlfile.write('<tr>' + ''.join('<th>{}</th>'.format(x) for x in header) + '</tr>\n')
    htmlfile.write('<tr>' + ''.join('<td>{}</td>'.format(x) for x in stats) + '</tr>\n')
    for conf, (_, result) in sorted(results.items()):
        htmlfile.write('<tr>' + ''.join('<td>{}</td>'.format(x) for x in conf))
        for value, clazz, thresh in result:
            thresh = ' ({})'.format(fstr(thresh,3)) if thresh != None else ''
            htmlfile.write('<td class={}>{}{}</td>'.format(clazz, fstr(value,3), thresh))
        htmlfile.write('</tr>\n')
    htmlfile.write(HTML_TABLE_TAIL)


def save_html(results, path, title, config):
    state = 'passed' if check_results(results) else 'failed'
    with open(path, 'w') as htmlfile:
        htmlfile.write(HTML_HEAD.format(title=title, style=STYLE, state=state, frame_ms=config['frame_ms']))
        for mode in sorted(results):
            name, header = HEADER[mode]
            write_table(htmlfile, results[mode], config, name, header)
            htmlfile.write(HTML_TAIL)


def is_valid_mode(mode, config):
    enc_test_modes = ['test_band_limiting', 'test_low_pass']
    dec_test_modes = []
    enc_modes = set(m[0] for m in config['configs'])
    check1 = enc_modes == {'encode'} and mode in dec_test_modes
    check2 = enc_modes == {'decode'} and mode in enc_test_modes
    return config[mode] and not check1 and not check2


def init_logging(verbose):
    time_stamp   = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    logfile     = 'conformanceCheck_{}.log'.format(time_stamp)
    file_handler = logging.FileHandler(filename=str(logfile))
    file_handler.setLevel(logging.DEBUG)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG if verbose else logging.WARNING)
    handlers = [file_handler, stdout_handler]
    formater  = '[%(levelname)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, handlers=handlers, format=formater)

def printLicense():
    print(LICENSE.format(VERSION))

def main():
    parser = argparse.ArgumentParser(description='Low Complexity Communication Codec - LC3: \n'
                                                 'Conformance Interoperability Test Software\n'
                                                 'Interoperability/Conformance Script V.{}\n'.format(VERSION))
    parser.add_argument('-v', action="store_true", dest='verbose', help='Activate verbose output')
    parser.add_argument('-w', dest='workers', type=int, default=os.cpu_count(), help='Number of worker threads')
    parser.add_argument('-keep', action="store_true", dest='keep_files', help='Keep all files (+log) produced in the test run')
    parser.add_argument('config', help='Conformance config file')
    parser.add_argument('-system_sox', action='store_true', help='Use system sox')
    args = parser.parse_args()
    
    global SOX_EXE
    if args.system_sox:
        SOX_EXE = 'sox'

    time_stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    work_dir = makedirs(pathlib.Path('lc3_conformance_' + time_stamp))

    try:
        printLicense()
        init_logging(args.verbose)

        globvars, tests = parse_config(args.config)
        check_system(globvars)
        build_tools()
        if not args.system_sox:
            download_sox()
        prepare_items(args.workers)

        test_modes = {'test_band_limiting': test_band_limiting, 'test_low_pass': test_low_pass,
                      'test_rate_switching': test_rate_switching,
                      'test_sqam': test_sqam}

        for test, config in tests.items():
            results = {}
            for mode in sorted(test_modes):
                if is_valid_mode(mode, config):
                    results[mode] = test_modes[mode](work_dir, test, config, args.workers)

            if not results:
                sys.exit('Please select at least one test in the configuration file or adjust the modes (enc, dec, encdec) to match the respective tests.')

            save_html(results, '{}_{}.html'.format(test, time_stamp), test, config)
            state = 'passed' if check_results(results) else 'failed'
            print('\nConformance test for "{}" (Frame Size {} ms) {}!\n'.format(test, config['frame_ms'], state))
            print('For detailed results see {}_{}.html\n'.format(test, time_stamp))

    finally:
        logging.shutdown()
        if not args.keep_files:
            shutil.rmtree(str(work_dir), ignore_errors=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\rExiting. Please wait while workers shut down ...')
    except OSError as E:
        sys.exit('Subprocess failed! See log for details. ' + str(E))
    except FileNotFoundError as E:
        sys.exit(E.strerror)
