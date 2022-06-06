# Protocol
All fields are sent LSB first. 0x12345678 will be transmitted as 78563412. All samples are 
16 bit signed integers. 

## OPCODES
The first byte of the packet denotes the OPCODE. OPCODES are separated into Commands and Events.
Commands are send from the host to the controller. Events are sent from the controller to the host. 
Each command is acknowledged by an event. 

### Commands
#### 01: Start encoding command
Send this command to initialize the encoder.

- **Byte 0:0** : 01
- **Byte 1:1** : Frame duration
    - 0x0A for 10 ms frames 
    - 0x4B for 7.5 ms frames
- **Byte 2:3** : Sample rate
- **Byte 4:7** : Bit rate

#### 02: Encode frame command
Encode 1 frame.

- **Byte 0:0**      : 02
- **Byte 1:2n+1**   : Samples, where n is the number of samples

#### 03: Start decoding command
Send this command to initialize the decoder.

- **Byte 0:0** : 03
- **Byte 1:1** : Frame duration
    - 0x0A for 10 ms frames 
    - 0x4B for 7.5 ms frames
- **Byte 2:3** : Sample rate
- **Byte 4:7** : Bit rate

#### 04: Decode frame command
Decode 1 frame.

- **Byte 0:0**      : 04
- **Byte 1:n+1**    : Samples, where n is the number of bytes

### Events
#### 05: Status event
Acknowledges the start encoding and start decoding commands.

- **Byte 0:0** : 05
- **Byte 1:1** : Status
    - 0: Success
    - 1: Error
- **Byte 2:2** : Command being acknowledged

#### 06: Encoding result event
Returns the encoded bytes.

- **Byte 0:0** : 06
- **Byte 1:1** : Status
    - 0: Success
    - 1: Error
- **Byte 2:3** : Number of bytes
- **Byte 4:n-4** : Encoded bytes, where n is the number of bytes

#### 07: Decoding result event
Returns the decoded samples.

- **Byte 0:0** : 07
- **Byte 1:1** : Status
    - 0: Success
    - 1: Error
- **Byte 2:3** : Number of bytes
- **Byte 4:2n-4** : Decoded samples, where n is the number of samples

## Encoding sequence

- Start encoding command
    - Wait for Status event
- Encode frame 0 command
    - Wait for Encoding result event

- ...

- Encode frame n command
    - Wait for Encoding result event


## Decoding sequence

- Start decoding command
    - Wait for Status event
- Decode frame 0 command
    - Wait for Decoding result event

...

- Decode frame n command
    - Wait for Decoding result event