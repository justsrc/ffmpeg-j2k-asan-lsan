# FFmpeg JPEG 2000 decoder: ASan and LSan checks

Runs the `jpeg2000-native-perf-v2` branch of
[justsrc/FFmpeg](https://github.com/justsrc/FFmpeg) under AddressSanitizer and
LeakSanitizer on GitHub's Ubuntu 26.04 x86_64 and arm64 runners.

The job:

- builds a minimal FFmpeg with `--toolchain=clang-asan` and symbols
- generates JPEG 2000 samples with the distribution FFmpeg: 8/12/16-bit,
  5/3 and 9/7, tiled, JP2, odd sizes, and 4096x1714
- decodes every sample at 1 and 4 threads
- runs `libavcodec/tests/jpeg2000dwt` and
  `checkasm --test=jpeg2000dsp`
- runs a deliberate-leak program first, so a silent LSan failure cannot be
  mistaken for a clean result

Logs are uploaded as an artifact for both architectures.

## Versions

- Runners: `ubuntu-26.04` and `ubuntu-26.04-arm`, the newest GA images.
  `ubuntu-latest` still points at Ubuntu 24.04.
- `actions/checkout@v7.0.1`
- `actions/upload-artifact@v7.0.2`

## Running

Push to `main` or start the workflow manually:

```sh
gh workflow run "ASan and LSan" --repo justsrc/ffmpeg-j2k-asan-lsan
```

This repository is CI scaffolding, not an FFmpeg submission.
