# ALSA microphone profile for the Logitech G435

VoiceStock records signed 16-bit mono PCM at 16000 Hz. Some USB microphones
do not accept that format on the raw hardware device. ALSA can convert the
format when the application opens a `plug` device instead of `hw:`.

This page records the profile that was verified with a Logitech G435 Wireless
Gaming Headset on the project Raspberry Pi. It is a deployment choice for that
headset. It is not the only microphone VoiceStock can use, and the application
does not install or rewrite `~/.asoundrc` when it starts.

The capture contract and the device selector are described in the
[push-to-talk capture interface](../interfaces/push-to-talk-capture.md). Button
wiring and a capture run are in the
[push-to-talk setup](push-to-talk.md).

## What ALSA is responsible for

On Raspberry Pi OS the path is:

```text
USB microphone
    → ALSA hardware device (hw:CARD,DEV)
    → optional ALSA plug conversion
    → PortAudio
    → sounddevice
    → VoiceStock
```

The microphone advertises the rates and channel counts its hardware
implements. PortAudio does not resample when that hardware rejects the
requested rate. ALSA can resample, change the sample format, and adapt the
channel count when the opened PCM is a `plug` device (`type plug`, `plughw`,
or often `default`) rather than the raw device `hw:`.

VoiceStock still asks PortAudio for 16000 Hz, one channel, and `int16`. It
does not contain its own resampler. A microphone that already accepts that
contract is selected by name and does not need this profile. A microphone that
rejects it, and has no plug device in front of it, fails with
`AudioDeviceUnsupportedError`.

## Why this headset needs conversion

The G435 receiver was enumerated by PortAudio as a direct hardware device
similar to `G435 Wireless Gaming Headset: USB Audio (hw:2,0)`. On that device,
opening 16000 Hz, 32000 Hz, or 44100 Hz mono `int16` failed. 48000 Hz mono
`int16` succeeded.

The card id observed during that validation was `Headset`. Capturing through
`plughw:CARD=Headset,DEV=0` at 16000 Hz, mono, signed 16-bit PCM succeeded.
The conversion was done by ALSA, not by VoiceStock.

`CARD=Headset` is that card's ALSA id, not a VoiceStock constant. Another Pi,
another USB port, or another receiver can expose a different id. See
[Find the card id](#find-the-card-id) before installing the profile on a
machine that has not been checked.

## The `type plug` device

The versioned snippet is
[`deploy/alsa/voicestock-mic-g435.asoundrc`](../../deploy/alsa/voicestock-mic-g435.asoundrc):

```conf
pcm.voicestock_mic {
    type plug
    slave.pcm "hw:CARD=Headset,DEV=0"

    hint {
        show on
        description "VoiceStock G435 microphone with ALSA format conversion"
    }
}
```

`type plug` inserts the ALSA `plug` plugin in front of the slave. VoiceStock
opens `voicestock_mic` and requests 16000 Hz mono signed 16-bit PCM. The plug
plugin converts those samples to the format the slave hardware accepts. For
this headset the slave is `hw:CARD=Headset,DEV=0`, which accepted 48000 Hz.
Sample-rate conversion therefore happens inside ALSA, before PortAudio delivers
buffers to `SoundDeviceBackend`. The WAV file is still the VoiceStock contract:
16000 Hz, one channel, signed 16-bit PCM.

`hint { show on }` makes the name visible to enumerators such as `arecord -L`
and PortAudio. The description text is only a hint. It does not select the
device.

This profile is specific to the G435 layout used in validation (`CARD=Headset`,
device 0). Do not point every microphone at `voicestock_mic`.

## Install

From the repository root, on the user that will run VoiceStock:

```bash
bash deploy/alsa/install-voicestock-mic.sh
```

The script writes `~/.asoundrc` for the current user. That is the file that
was used in validation (`/home/g3voicestock/.asoundrc` on that Pi). It does
not edit `/etc/asound.conf`, and it does not need `sudo`.

Behavior:

| Situation | What the script does |
| --- | --- |
| `~/.asoundrc` does not exist | Creates it with only the marked profile. |
| The marked profile is already present and identical | Exits without writing. |
| The marked profile is present but differs | Replaces that block and leaves the rest of the file. |
| The file has other PCM definitions and no `pcm.voicestock_mic` | Appends the marked block. |
| `pcm.voicestock_mic` already exists without the markers | Exits with an error and does not change the file. |
| The target is a symlink or a directory | Exits with an error and does not change it. |

The block is delimited by:

```text
# >>> voicestock_mic G435 >>>
# <<< voicestock_mic G435 <<<
```

Before the first modification of an existing file, the script copies it once
to `~/.asoundrc.voicestock.bak`. A later run does not overwrite that backup.

Another path can be used when the home file is not the one you want to edit:

```bash
bash deploy/alsa/install-voicestock-mic.sh --file /path/to/asoundrc
```

To install by hand, copy the snippet between those markers into `~/.asoundrc`.
Do not delete unrelated PCM or control definitions already in the file. If
`pcm.voicestock_mic` is already defined, do not add a second one.

If `arecord -l` shows a card id other than `Headset`, change `slave.pcm` in
your installed file to `hw:CARD=<that id>,DEV=0`. Keep the name
`voicestock_mic` if you want the selector documented here. Editing the
versioned example is optional; the installed user file is the one ALSA reads.

Changing the card id means the profile is no longer the exact G435 validation
snippet. Record the id you used. Do not commit a personal card id as if it
were the validated headset.

## Select the device in VoiceStock

Restart is not always required for a user `~/.asoundrc`, but a process that
already opened PortAudio should be started again after the file changes.

List ALSA PCMs:

```bash
arecord -L
```

`voicestock_mic` should appear, with the hint description.

List PortAudio inputs from the repository, with the virtual environment
active:

```bash
python -c "from pi.audio.sounddevice_backend import list_input_devices; \
[print(d.name, '|', d.host_api, '|', d.default_samplerate) for d in list_input_devices()]"
```

Use the printed name with `--input-device`. For this profile that name is
`voicestock_mic`. A descriptive query such as `voicestock_mic` matches the
[device selector](../interfaces/push-to-talk-capture.md#microphone-selection).
Do not pass a PortAudio index.

Confirm the contract before a button run:

```bash
python -c "import sounddevice as sd; sd.check_input_settings(device='voicestock_mic', channels=1, dtype='int16', samplerate=16000); print('16000 Hz mono int16 accepted')"
```

Then point the command at that name:

```bash
voicestock-pi-ptt \
  --pin 17 \
  --bounce-time 0.05 \
  --input-device "voicestock_mic" \
  --output-directory recordings
```

`voicestock-pi` takes the same `--input-device` value. A different microphone
that already accepts 16000 Hz keeps its own PortAudio name. Do not set it to
`voicestock_mic` unless that plug device is the one you intend to open.

## Verify a recording with ALSA

`arecord` is a diagnostic. It is not the VoiceStock recorder.

```bash
arecord -D voicestock_mic -f S16_LE -r 16000 -c 1 -d 3 /tmp/voicestock-mic.wav
```

A successful run is three seconds of signed 16-bit mono PCM at 16000 Hz
(48000 frames, plus the WAV header). Playback:

```bash
aplay /tmp/voicestock-mic.wav
```

If this command works and PortAudio still rejects `voicestock_mic`, the
process likely has a stale device list or is opening a different name. Start
it again and pass `voicestock_mic`, not the `hw:` name.

## Find the card id

```bash
arecord -l
```

Example shape:

```text
card 2: Headset [G435 Wireless Gaming Headset], device 0: USB Audio [USB Audio]
```

The token after `card N:` (`Headset` here) is the ALSA card id used in
`hw:CARD=Headset,DEV=0`. The number is not stable across reboots and plugs.
Prefer `CARD=<id>`.

If the id is not `Headset`, the checked-in slave string will not open. Update
the installed `slave.pcm` line as described above, or skip this profile when
the microphone is not the G435.

`arecord -L` lists plug names such as `plughw:CARD=Headset,DEV=0`. That name
is a useful manual check. VoiceStock selects the PCM by the PortAudio device
name, which for this file is `voicestock_mic`.

## Other microphones

| Microphone | What to do |
| --- | --- |
| Accepts 16000 Hz mono `int16` directly | Select its PortAudio name. Do not install this profile for it. |
| Logitech G435 with card id `Headset` | Install this profile and select `voicestock_mic`. |
| Same headset, different card id | Install the profile only after changing `slave.pcm` to that card. |
| Another device that rejects 16000 Hz | VoiceStock returns `AudioDeviceUnsupportedError`. This profile does not fix it. Add a separate plug PCM for that hardware if you need one; do not rename it over `voicestock_mic` unless you mean to replace the G435 slave. |

There is no microphone-selection screen in the application. The choice is the
`--input-device` string. There is no automatic fallback from a failing
hardware device to `voicestock_mic`.

## Recovery when ALSA shows no microphone

1. Confirm the USB receiver is plugged in and powered. The G435 headset must
   be linked to that receiver; the headset radio by itself is not a USB audio
   device.
2. Run `arecord -l`. If the card is missing, PortAudio will not list it
   either. Try another USB port, then check `dmesg` for USB audio connect
   messages.
3. If `arecord -l` shows the card but `voicestock_mic` is absent from
   `arecord -L`, the user configuration was not loaded. Confirm the file is
   `~/.asoundrc` for the user running the command, and that the PCM name is
   `voicestock_mic`.
4. If the name is present and `arecord -D voicestock_mic ...` fails, the
   slave card id is wrong or the device number is not 0. Compare `slave.pcm`
   with `arecord -l`.
5. VoiceStock's `AudioDeviceNotFoundError` means the `--input-device` string
   matched no PortAudio input. `AudioDeviceUnsupportedError` means a device
   matched but rejected 16000 Hz mono `int16`.

## Roll back

Remove only the marked block:

```bash
bash deploy/alsa/install-voicestock-mic.sh --remove
```

The rest of `~/.asoundrc` stays. If the file contained nothing else, the
script deletes it. Running `--remove` again does nothing.

Restore the backup taken before the first scripted edit:

```bash
cp -p ~/.asoundrc.voicestock.bak ~/.asoundrc
```

That backup is not refreshed on later installs. If you edited the file after
the backup, prefer `--remove`, which only deletes the marked block.

After rollback, `arecord -L` should no longer list `voicestock_mic`, and
`--input-device voicestock_mic` should fail device lookup until a profile is
installed again. The raw headset device, if it is still plugged in, remains
visible under its hardware name and still has to accept 16000 Hz on its own.

## What this page does not do

- It does not change application code or hard-code the G435.
- It does not run during `voicestock-pi` or `voicestock-pi-ptt` startup.
- It does not claim that every future demonstration microphone needs this
  file.
- It does not replace the formal Raspberry Pi capture procedure. A working
  `arecord` check is not a passed application test.
