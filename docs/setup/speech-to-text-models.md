# Speech-to-text evaluation models

## Scope and source layout

These are evaluation candidates, not an accepted production engine. They are
downloaded locally for CPU evaluation on a development computer before testing
on the Raspberry Pi 3. Downloading weights does not install the inference engines.

Under [ADR-0002](../decisions/0002-split-source-by-runtime-pc-pi-shared.md),
the production SpeechToText interface and engine adapters belong in
`src/pi/speech_to_text/`, with tests in `tests/pi/speech_to_text/`.
Running preliminary benchmarks on a PC does not move this component to `src/pc`.
Evaluation scripts belong in `scripts/benchmarks/`. Model weights belong outside
`src`, in the ignored local directory `models/stt/`.

## Candidates and download locations

| Engine | Model | Local path |
| --- | --- | --- |
| Vosk | Spanish small 0.42 | `models/stt/vosk/vosk-model-small-es-0.42/` |
| whisper.cpp | Multilingual tiny | `models/stt/whisper/ggml-tiny.bin` |
| whisper.cpp | Multilingual base | `models/stt/whisper/ggml-base.bin` |
| whisper.cpp | Multilingual small Q5_1 | `models/stt/whisper/ggml-small-q5_1.bin` |

Sources: [Vosk models](https://alphacephei.com/vosk/models) and
[whisper.cpp model repository](https://huggingface.co/ggerganov/whisper.cpp).
The Whisper models are multilingual, without the English-only `.en` suffix.
Disk size is not a measurement of runtime RAM.

## Download procedure

From the repository root, on Linux:

```bash
mkdir -p models/stt/vosk models/stt/whisper
curl --fail --location --retry 2 --output models/stt/vosk/vosk-model-small-es-0.42.zip https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
curl --fail --location --retry 2 --output models/stt/whisper/ggml-tiny.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin
curl --fail --location --retry 2 --output models/stt/whisper/ggml-base.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
python3 -m zipfile -e models/stt/vosk/vosk-model-small-es-0.42.zip models/stt/vosk
curl --fail --location --retry 2 --output models/stt/whisper/ggml-small-q5_1.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small-q5_1.bin
sha256sum models/stt/vosk/vosk-model-small-es-0.42.zip models/stt/whisper/ggml-tiny.bin models/stt/whisper/ggml-base.bin
```

Record downloaded hashes and engine versions with benchmark results. The URLs
above may change their contents upstream; hashes identify the actual files used.
Downloading needs Internet access; inference must work offline after the engines
and models have been installed. Raspberry Pi OS and architecture compatibility
remain to be checked on the actual board before selecting an engine.

## Inference engines on the development computer

Vosk 0.3.45 is installed in `.venv`. Its optional dependency is declared as
`stt-vosk` in `pyproject.toml`. To prepare a fresh environment:

```bash
python3 -m venv .venv
.venv/bin/pip install ".[stt-vosk]"
```

### Active Conda environment

When `CONDA_PREFIX` is set, `scripts/setup.sh` and `scripts/setup.ps1` install
into that environment using its own Python. Without an active Conda environment,
they create or reuse `.venv`. An invalid active environment causes an explicit
error instead of silently installing elsewhere.

To install development dependencies and Vosk on Linux:

```bash
conda activate voicestock
./scripts/setup.sh --stt
```

On PowerShell, activate the desired Conda environment first, then run:

```powershell
.\scripts\setup.ps1 -Stt
```

For Vosk alone in an already activated environment:

```bash
python -m pip install "vosk==0.3.45"
```

Conda activation must happen in the same terminal that launches setup. The
model files and whisper.cpp executable remain in their project locations and
can be used from either environment; whisper.cpp is a native executable, not
a Python package requiring a duplicate installation into Conda.

Vosk loads the extracted Spanish model into a `vosk.Model`, creates a
`KaldiRecognizer` with sample rate 16000, and consumes PCM chunks from the WAV.
`Result()` returns completed segments; `FinalResult()` returns the remainder.
The WAV header is read separately, not passed as PCM to the recognizer.

whisper.cpp is compiled locally for CPU at
`.tools/stt/whisper.cpp/build/bin/whisper-cli`. All Whisper model sizes use this binary.
The source revision downloaded for this setup is
`d1be6fde11ac6e0407606b4e42fe72d34add8037` (1.9.5-dev).
Source and build output are excluded from Git. Reproduce this build with Git,
CMake and a C/C++ compiler installed:

```bash
mkdir -p .tools/stt
git clone https://github.com/ggml-org/whisper.cpp.git .tools/stt/whisper.cpp
git -C .tools/stt/whisper.cpp checkout d1be6fde11ac6e0407606b4e42fe72d34add8037
cmake -S .tools/stt/whisper.cpp -B .tools/stt/whisper.cpp/build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DGGML_VULKAN=OFF -DGGML_METAL=OFF -DWHISPER_BUILD_TESTS=OFF
cmake --build .tools/stt/whisper.cpp/build --target whisper-cli -j 2
```

To transcribe an existing WAV locally, select Spanish and disable GPU use:

```bash
.tools/stt/whisper.cpp/build/bin/whisper-cli -m models/stt/whisper/ggml-tiny.bin -f path/to/audio.wav -l es -ng -t 4
.tools/stt/whisper.cpp/build/bin/whisper-cli -m models/stt/whisper/ggml-base.bin -f path/to/audio.wav -l es -ng -t 4
```

The binary built on this x86 computer cannot be copied to the Raspberry Pi.
Compile on the target architecture or use an appropriate ARM build there.
These installations prepare evaluation; accuracy and resource measurements
require the common Spanish audio corpus and later validation on the Pi 3.

## Additional exploratory engine: Moonshine

Spanish Tiny Streaming (34M parameters) and Small Streaming (123M parameters)
are evaluated as another engine. Install `.[stt-moonshine]` in the active Conda
environment or existing venv and run `scripts/benchmarks/download_moonshine_models.py`.
See [benchmark protocol](../testing/speech-to-text-benchmark.md#moonshine-spanish-comparison)
for full-file evaluation and resource measurement. This exploration does not
select a production adapter or establish Raspberry Pi 3 performance.

## Selected candidate and hardware boundary

The working selection is Whisper Small Q5_1 with whisper.cpp, pending actual
Raspberry Pi 3 validation. See [ADR-0005](../decisions/0005-use-whisper-small-q5-for-offline-stt.md)
and [recorded evidence](../research/speech-to-text-engine-evaluation.md).
This setup reproduces PC exploration; the actual Pi OS/architecture build,
installation walkthrough, offline check and usability verdict are still pending.
The production public interface and adapter under `src/pi/speech_to_text/`
are not implemented by these scripts.

## Raspberry SSH integration preparation

A separate `WhisperAdapter` and `SpeechToText` port now exist in
`src/pi/speech_to_text/`. See [the public contract](../interfaces/speech-to-text.md)
and [the target build/SSH procedure](../testing/raspberry-stt-ssh.md).
On the Pi, `bash scripts/setup.sh` creates/reuses `.venv` when Conda is not active;
install `.[stt-integration]` for resource instrumentation. Conda is not required
on the Pi. The existing `--stt` setup option adds Vosk, not this Whisper build.
Hardware execution is still pending; the old PC exploration results are not
validation of the new adapter.
