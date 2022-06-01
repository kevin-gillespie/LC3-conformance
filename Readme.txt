***************************************************************************************************************
 Low Complexity Communication Codec - LC3 Conformance Interoperability Test Software Release V1.0.6 2022/01/11

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

This package contains the Conformance Interoperability Test Software for the Low Complexity Communication Codec LC3
as described in the LC3 Test Suite LC3.TS.p01.

The following structure outlines the content of this package:

    /LC3_Reference_Binary/LC3.exe                 : LC3 Fixed Point Reference binary for Windows 32-bit
    /LC3_Conformance_Interoperability_Script/     : LC3 conformance script (conformanceCheck.py) and helper files

Please refer to the respective Readme files for more information:

    /LC3_Reference_Binary/Readme.txt              : Readme for LC3 Reference Binary
    /LC3_Conformance_Interoperability_Script/     : Readme for LC3 Python Conformance Script
    

Changelog
---------
    - V.1.0.6 2022/01/11
        - Added optional encoder-decoder chain tests to .cfg files

    - V.1.0.5 2021/10/01
        - Fixed uninitialized variables in rms.c (required for conformanceCheck.py)

    - V.1.0.4 2021/08/20
        - Fixes in conformanceCheck.py and configuration files
          see conformance script Readme for more information

    - V.1.0.3 2021/06/17
        - Corrected copyright header (removed software version number(s) from header and placed it below)
        - LC3.exe bitexact to V.1.0.2
          
    - V.1.0.2 2021/06/15
        - Updates on reference binary readme:
          removed obsolete RFU field from bitstream header description
    
    - V.1.0.1 2021/06/07
        - Updates on reference binary and readme:
          see binary readme for more information

    - V.1.0.0 2021/05/25
        - Initial Release
