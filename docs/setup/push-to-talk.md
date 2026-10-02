# Push-to-talk setup and manual test

How to wire the button, point the capture command at a USB microphone, and
check one recording on a Raspberry Pi. The contract being checked is the
[push-to-talk capture interface](../interfaces/push-to-talk-capture.md). Why
this stack was chosen is
[ADR-0003](../decisions/0003-use-event-driven-gpio-and-sounddevice-for-ptt-capture.md).

This procedure has not been run on the project Raspberry Pi. Automated tests
cover the logic without GPIO hardware and without a microphone. The checks
below are still pending on the real board.

## Preconditions

- Raspberry Pi 3, powered as a fixed prototype from a 5 V / 2.5 A supply.
- A push button, jumpers, and a USB microphone.
- Python 3.11 or newer.
- The VoiceStock repository checked out on the Pi.
- No speech-to-text step. This procedure ends at the WAV file.

## Install

On the Pi, from the repository root, use the project setup script. It creates
`.venv` and installs the project, including `gpiozero` and `sounddevice`:

```bash
./scripts/setup.sh
source .venv/bin/activate
```

`sounddevice` does not ship PortAudio. On Linux the shared library has to
already be on the system. The capture research names `libportaudio2` as the
usual Debian and Raspberry Pi OS package. That package has not been confirmed
on the project image, so do not treat an install command as part of this
procedure until someone verifies it there. If `import sounddevice` fails with a
missing PortAudio library, record the exact message and the system package
that provides it.

GPIO Zero is the Python package from the project install. This procedure does
not add an apt package for it.

## Wiring

BCM numbering. The pin in the command is an example, not a product pin.
Internal pull-up stays enabled. Do not add an external pull-up.

```text
GPIO17 (BCM) ---- button ---- GND
internal pull-up enabled in software
```

Released leaves the pin high. Pressed connects it to ground, so the pin reads
low. The application does not offer another polarity.

`0.05` seconds of debounce in the command below is an example passed through
to GPIO Zero. It is not a value proven on every switch. Change it only after
watching the real button.

## Find the microphone

Plug in the USB microphone, then list what PortAudio can record from:

```bash
python -c "from pi.audio.sounddevice_backend import list_input_devices; \
[print(d.name, '|', d.host_api) for d in list_input_devices()]"
```

Use one printed name, or a distinctive part of it, as `--input-device`.
Do not save a PortAudio index. Indexes move when devices are replugged.

Optional ALSA check, if `arecord` is already installed. It is a diagnostic,
not the VoiceStock recorder:

```bash
arecord -l
```

## Run one capture

```bash
mkdir -p recordings
voicestock-pi-ptt \
  --pin 17 \
  --bounce-time 0.05 \
  --input-device "USB Audio" \
  --output-directory recordings \
  --max-duration 60
```

`--pin`, `--bounce-time`, `--input-device`, and `--output-directory` are
required. `--max-duration` defaults to 60 seconds. `--input-device` must match
the list from the previous section; `USB Audio` is only a placeholder.

The process waits until Ctrl+C. Ctrl+C closes the button and the controller.
A WAV already printed is left on disk. A hold that is still recording when
you press Ctrl+C is finished and reported as `RELEASED`.

1. Start the command and wait for `Waiting for the push-to-talk button`.
2. Press the button, speak, and release it.
3. Read the printed result. The command does not delete that WAV.

The printout looks like this. The id, path, and duration will differ:

```text
Capture completed
Artifact ID: <uuid>
Path: recordings/<uuid>.wav
Duration: <seconds>s
Termination: RELEASED
Format: WAV / 16 kHz / mono / 16-bit
```

## Check the WAV

The module is valid when that file exists and the header matches the contract.
Playback is how a person hears the take; it is not what decides the format.

From the repository, with the virtual environment active:

```bash
python -c "import wave,sys; w=wave.open(sys.argv[1]); \
print(w.getnchannels(), w.getframerate(), w.getsampwidth(), w.getnframes())" \
  recordings/<uuid>.wav
```

Expect `1 16000 2` and a frame count greater than zero. Duration in seconds is
that frame count divided by 16000.

If `aplay` is installed, play the same path and listen for the phrase you
spoke:

```bash
aplay recordings/<uuid>.wav
```

## Maximum duration

Use a short limit so the wait is a few seconds, not a minute:

```bash
voicestock-pi-ptt \
  --pin 17 \
  --bounce-time 0.05 \
  --input-device "USB Audio" \
  --output-directory recordings \
  --max-duration 5
```

1. Press the button and hold it for more than five seconds.
2. The recording should stop while the button is still down.
3. The printout should say `Termination: MAX_DURATION`.
4. The WAV should still play, or at least open with the same header check.
5. Release the button. That does not print a second result.
6. Press, speak, and release again. A new capture should print `RELEASED`.

Holding past the limit and then releasing is the physical check that the
controller waited for release before starting another take.

## Troubleshooting

### No matching input device

`Capture error:` followed by `AudioDeviceNotFoundError`, or the message
`No input device matches ...`.

Check that the USB plug is seated, that `list_input_devices()` prints the
microphone, and that `--input-device` is a substring of that name and host
API. An empty selector fails the same way.

### Ambiguous device

`AudioDeviceAmbiguousError`, with the query and the names that matched.

Pass a longer substring, or the exact device name, or `name, host API` as
printed. A short word that appears in several names is not a stable selector.

### Unsupported format

`AudioDeviceUnsupportedError`: the device cannot capture 16 kHz mono signed
16-bit PCM.

VoiceStock does not resample. Try the device name that PortAudio lists for the
microphone rather than a raw hardware id you typed by hand. If
`check_input_settings` still rejects it, the microphone needs a later capture
change. Do not describe that as a working configuration.

`arecord -D hw:<card>,<device> -f S16_LE -r 16000 -c 1 -d 2 /tmp/hw.wav` can
show whether the card itself accepts the rate. That command is optional and
was not run on the project microphone. A failure there, with success through
the `default` device, means ALSA may be converting. The application still
requires the PortAudio check to pass for the name you pass to `--input-device`.

### The button does nothing

Confirm BCM numbering, the `--pin` value, and the wire from that GPIO pin
through the switch to a ground pin. The internal pull-up is on; the other side
of the switch is ground, not 3.3 V. `PushToTalkButton` has no polarity flag.

### Presses repeat or fire at once

Look at the switch and the wiring before changing debounce. A floating wire or
a short looks like extra edges. `bounce_time` is in seconds and is not tuned
for a specific part. Increase it only after a repeated run shows the contact
bouncing, and keep the value you actually observed.

### Recording stops with MAX_DURATION before you release

The hold reached `--max-duration`, or the release edge never arrived. Check
the value you passed, whether the button is stuck closed, and whether release
returns the pin to the pull-up. After that stop, a new take starts only once
the button has been released.

## Not done

This procedure does not cover speech-to-text, a language model, inventory,
confirmation audio, LEDs, a buzzer, a web page for choosing the microphone,
automatic deletion after transcription, or resampling. None of that is
implemented on this path.

Still pending on the physical Pi: GPIO press and release, USB microphone
detection, a real 16 kHz mono 16-bit open, one press-talk-release, one
maximum-duration cut, and listening to the WAV.
