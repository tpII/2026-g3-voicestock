#!/usr/bin/env bash
# Run on the target Raspberry Pi; builds no model weights into the executable.
set -euo pipefail
TASK_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASK_WHISPER_ROOT="$TASK_REPO_ROOT/.tools/stt/whisper.cpp"
TASK_REVISION="d1be6fde11ac6e0407606b4e42fe72d34add8037"
mkdir -p "$TASK_REPO_ROOT/.tools/stt"
if [[ ! -d "$TASK_WHISPER_ROOT" ]]; then
  git clone https://github.com/ggml-org/whisper.cpp.git "$TASK_WHISPER_ROOT"
  git -C "$TASK_WHISPER_ROOT" checkout "$TASK_REVISION"
fi
if [[ "$(git -C "$TASK_WHISPER_ROOT" rev-parse HEAD)" != "$TASK_REVISION" ]]; then
  printf 'Whisper source revision differs; use the documented pinned revision.\n' >&2
  exit 1
fi
cmake -S "$TASK_WHISPER_ROOT" -B "$TASK_WHISPER_ROOT/build" \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DGGML_VULKAN=OFF \
  -DGGML_METAL=OFF -DWHISPER_BUILD_TESTS=OFF
cmake --build "$TASK_WHISPER_ROOT/build" --target whisper-cli -j "${STT_BUILD_JOBS:-1}"
g++ -O2 -std=c++17 "$TASK_REPO_ROOT/scripts/benchmarks/native/whisper_worker.cpp" \
  -I "$TASK_WHISPER_ROOT/include" -I "$TASK_WHISPER_ROOT/ggml/include" \
  -L "$TASK_WHISPER_ROOT/build/bin" \
  -Wl,-rpath,'$ORIGIN/whisper.cpp/build/bin' -lwhisper \
  -o "$TASK_REPO_ROOT/.tools/stt/whisper-benchmark-worker"
printf 'Worker compiled for this machine. Model weights must be installed separately.\n'
