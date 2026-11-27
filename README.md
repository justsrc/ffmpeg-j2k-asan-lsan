# FFmpeg JPEG 2000 decoder: ASan and LSan checks

Runs the final JPEG 2000 performance branches of
[justsrc/FFmpeg](https://github.com/justsrc/FFmpeg) under AddressSanitizer and
LeakSanitizer on GitHub's Ubuntu 26.04 x86_64 and arm64 runners:

- `perf/j2k-dwt` (`9bcf7fc576`): 9/7 DWT blocking and fused lifting
- `perf/j2k-tier1` (`738522d0e4`): packed MQ/tier-1 state and packed output
- `ci/j2k-combined`: both series merged for the combined build

The `linux` job:

- builds a minimal FFmpeg with `--toolchain=clang-asan` and symbols
- generates JPEG 2000 samples with the distribution FFmpeg: 8/12/16-bit,
  5/3 and 9/7, tiled, JP2, odd sizes, and a three-frame 4096x1714 stream
- decodes every sample at 1, 4 and 8 threads
- decodes the 240-frame 4096x1714 DCI 4K XYZ 12-bit corpus at 1, 4 and
  8 threads
- runs `libavcodec/tests/jpeg2000dwt` on every ref, and
  `libavcodec/tests/mqc` where the ref contains it
- runs `checkasm --test=jpeg2000dsp`
- runs a deliberate-leak program first, so a silent LSan failure cannot be
  mistaken for a clean result

The `fate` job builds the same sanitizer configuration with the framecrc
muxer, scale filter and MXF demuxer, fetches the ITU-T T.803 conformance
codestreams and the D-Cinema MXF sample from the FFmpeg FATE suite, and runs
`make fate-jpeg2000dec`.

The `fuzz` job runs the 2268 malformed and truncated inputs from the J2K
validation fuzz corpus, one ASan+LSan process per input. It fails on any
sanitizer marker, timeout, or crash.

Logs are uploaded as an artifact per architecture, ref and job.

## Corpus

The 4K corpus is the 240-frame 4096x1714 XYZ 12-bit DCI stream from the
`dcp-media` validation set, published as the
[`j2k-corpus-2026-11-27`](https://github.com/justsrc/ffmpeg-j2k-asan-lsan/releases/tag/j2k-corpus-2026-11-27)
release asset because it is 176 MB. The workflow verifies its SHA-256
(`f19a668d861c41745ab644fc0df7557c1c7974de89a9d441c5d389b8b21a42ae`) before
decoding.

The malformed corpus is published as the
[`j2k-fuzz-corpus-2026-11-27`](https://github.com/justsrc/ffmpeg-j2k-asan-lsan/releases/tag/j2k-fuzz-corpus-2026-11-27)
release asset (4.6 MB compressed, 2268 inputs, SHA-256
`8fd38e74779bb41f6e4ba44d5839a578b3917e430b5dc63fd3fd40e735c10667`).

## Versions

- Runners: `ubuntu-26.04` and `ubuntu-26.04-arm`, the newest GA images.
  `ubuntu-latest` still points at Ubuntu 24.04.
- `actions/checkout@v7.0.1`
- `actions/upload-artifact@v7.0.2`

## Running

Push to `main` or start the workflow manually. The default matrix tests all
three refs; pass a single `ref` input to test one:

```sh
gh workflow run "ASan and LSan" --repo justsrc/ffmpeg-j2k-asan-lsan
gh workflow run "ASan and LSan" --repo justsrc/ffmpeg-j2k-asan-lsan \
  -f ref=perf/j2k-tier1
```

This repository is CI scaffolding, not an FFmpeg submission.
