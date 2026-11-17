# Tracer build used by the accepted Checkstyle case

`report.json` records the actually built strace 7.0 binary with libdw, its source
archive hash and downloaded package hashes. Its absolute RPATH selects libraries
unpacked under `/home/pratz/guardianai-tools/strace-libdw-v1/deps`; the binary is
not independently relocatable. No system packages were installed. The runtime
command supplies this sensor explicitly with `--sensor`; the older sensor remains.

`build.py` is the initial attempt. It downloaded and unpacked dependencies and
the official source but failed its header check. `continue_build.py` supplied the
missing include/library paths and built successfully. The failed configure log,
successful build log and download log are retained. These are development
commands, not a promise that unversioned future repository downloads reproduce
the recorded package bytes. Check the hashes in `report.json` for this edition.

The downloaded archives, unpacked dependencies and compiled tracer live outside
the project run dataset. The source URL is
[strace 7.0](https://strace.io/files/7.0/strace-7.0.tar.xz). The existing upstream
[libdw backend](https://raw.githubusercontent.com/strace/strace/v7.0/src/unwind-libdw.c)
is used without a custom unwinder implementation. A build and one successful
workload do not establish all tracer/backend behaviors.
