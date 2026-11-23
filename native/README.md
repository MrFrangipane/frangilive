### JACK matrix

On Linux, install a C11 compiler, `make`, `pkg-config`, and JACK development headers (for example `libjack-jackd2-dev`), then run `make -C native`. Start an existing JACK server and run:

```
native/jack-matrix --inputs 8 --outputs 8 --name jack-matrix --fade-ms 5
```

Inputs and outputs are required and range from 1 to 128. The optional name defaults to `jack-matrix`; startup fails if that exact client name is unavailable. The fade defaults to 5 ms (0 selects one sample), with a maximum of 10000 ms. Ports are named `in_0`, `in_1`, ... and `out_0`, `out_1`, ... . Connect external JACK ports to these ports independently. All routes start disabled; enabled inputs are summed without limiting or normalization.

Send newline-terminated ASCII commands on stdin and read one newline-terminated response per command on stdout:

```
SET 0 1 1
OK
SET 0 1 0
OK
QUIT
OK
```

`MATRIX 0,1 2,3` replaces the entire routing matrix with the listed input,output pairs; `MATRIX` with no pairs disables every route. Indices are zero-based, duplicates are harmless, and an invalid pair rejects the whole command without changing the matrix. `SET input output enabled` remains available for individual changes, with enabled equal to 0 or 1. Each accepted command publishes a complete snapshot; the audio callback adopts the latest snapshot at a block boundary, so all changed routes start fading together. Rapid commands can be coalesced before the next block. `OK` acknowledges receipt, not completion of the fade; malformed commands return `ERR invalid command`. Lines exceeding the input buffer (131087 characters before the terminating NUL) return `ERR line too long`. `QUIT` or stdin EOF closes the client. Diagnostics are written to stderr. Routes ramp linearly from their current level.

Run the native mixing and fade tests with `make -C native test`. They require the JACK development library but not a running JACK server.
