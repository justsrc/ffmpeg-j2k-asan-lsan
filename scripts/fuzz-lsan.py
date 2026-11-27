#!/usr/bin/env python3
"""Run malformed JPEG 2000 inputs through an ASan+LSan build.

Usage: fuzz-lsan.py FFMPEG INPUT_DIR OUTPUT_JSON
"""
import concurrent.futures
import json
import os
import subprocess
import sys
import time

if len(sys.argv) != 4:
    sys.exit("usage: fuzz-lsan.py FFMPEG INPUT_DIR OUTPUT_JSON")

ffmpeg, inputs, out = sys.argv[1:]
markers = (
    "AddressSanitizer",
    "LeakSanitizer",
    "UndefinedBehaviorSanitizer",
    "runtime error:",
    "SEGV",
    "stack-overflow",
    "allocation-size-too-big",
    "SUMMARY:",
)
env = dict(os.environ)
# FUZZ_ASAN_OPTIONS exists so the script can be smoke-tested on platforms
# without LSan; CI keeps the leak-enabled default.
env["ASAN_OPTIONS"] = os.environ.get(
    "FUZZ_ASAN_OPTIONS",
    "detect_leaks=1:abort_on_error=1:strict_string_checks=1:"
    "detect_stack_use_after_return=1",
)
env["LSAN_OPTIONS"] = "exitcode=23:report_objects=1"
env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"


def run(path):
    started = time.monotonic()
    try:
        p = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
             "-threads", "1", "-f", "image2pipe", "-c:v", "jpeg2000",
             "-i", path, "-f", "null", "-"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            timeout=20, env=env,
        )
        elapsed = time.monotonic() - started
        err = p.stderr.decode("utf-8", "replace")
        bad = [m for m in markers if m in err]
        return {
            "file": os.path.relpath(path, inputs),
            "rc": p.returncode,
            "seconds": round(elapsed, 3),
            "sanitizer": bad,
            "stderr": err[-4000:] if bad else "",
        }
    except subprocess.TimeoutExpired as e:
        err = (e.stderr or b"").decode("utf-8", "replace")
        return {
            "file": os.path.relpath(path, inputs),
            "rc": "timeout",
            "seconds": 20,
            "sanitizer": ["timeout"],
            "stderr": err[-4000:],
        }


files = sorted(
    os.path.join(root, name)
    for root, _, names in os.walk(inputs)
    for name in names
)
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for i, r in enumerate(pool.map(run, files), 1):
        results.append(r)
        if i % 250 == 0:
            print(f"{i}/{len(files)}", flush=True)

bad = [r for r in results if r["sanitizer"]]
summary = {
    "inputs": len(files),
    "decoded": sum(1 for r in results if r["rc"] == 0),
    "rejected": sum(1 for r in results if isinstance(r["rc"], int) and r["rc"] != 0),
    "timeouts": sum(1 for r in results if r["rc"] == "timeout"),
    "sanitizer_findings": len(bad),
    "findings": bad[:20],
}
with open(out, "w") as f:
    json.dump({"summary": summary, "all": results}, f, indent=1)
print(json.dumps(summary, indent=2))
sys.exit(1 if bad else 0)
