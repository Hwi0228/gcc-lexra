# LX5280 GCC backend status

The initial backend increment adds "-march=lx5280" to GCC's MIPS backend.
It selects MIPS I and uses conservative generic instruction-cost defaults;
no LX5280-specific latency or throughput claims are made.

The profile disables the ISA_HAS_LWL_LWR capability predicate. This prevents
affected machine-description expansions and block-move logic from selecting
LWL, LWR, SWL, or SWR for compiler-generated code. The datasheet describes
an optional coprocessor interface, not an unconditional floating-point unit,
so the target defaults to soft-float. Systems with a verified compatible
coprocessor can explicitly select hard-float.

This is a GCC-only increment. GAS and the disassembler do not yet have an
LX5280 CPU entry. GCC therefore maps emitted module architecture metadata to
mips1 and does not forward "-march=lx5280" to GAS. It does not yet select
Radiax instructions.

This stage does not make the assembler reject unsupported instructions in
user inline assembly and does not provide LX5280-aware object attributes or
disassembly; those require Binutils work.

The DejaGNU tests cover:
- Separation of `-march` and `-mtune`, checked through GCC's
  `_MIPS_ARCH` and `_MIPS_TUNE` predefined macros.
- The MIPS-I profile, the configured cross-compiler default o32 ABI, and the
  default soft-float ABI, including an explicit hard-float override for
  systems with a compatible coprocessor. The o32 default comes from this
  CI target configuration (`--with-abi=32`), not from the LX5280 ISA itself.
- Packed halfword/word loads and stores, volatile accesses, bitfields,
  `memcpy`, and `memmove`, with a negative scan for LWL/LWR/SWL/SWR.

The project-level script
`toolchain-tests/lx5280/check_driver.py` additionally checks ABI rejection
for 64-bit ABIs, invokes the branch `xgcc -c` driver, verifies that it calls
the configured cross GAS with `-mips1` (not the GCC-only
`-march=lx5280`), and inspects the resulting ELF header and disassembly.

## Initial Radiax compiler interface

The first Radiax subset exposes two LX5280-only built-ins:

- `__builtin_mips_lx5280_mfru(index)` reads a Radiax user register.
- `__builtin_mips_lx5280_mtru(value, index)` writes a Radiax user register.

The index must be a compile-time constant naming a documented user register:
CBS0/CBS1/CBS2 (0-2), CBE0/CBE1/CBE2 (4-6), LPS0/LPE0/LPC0 (16-18),
or MMD (24). Kernel-reserved MFRK/MTRK operations are deliberately not exposed.

GCC currently emits the documented LEXOP/SUBOP words using `.word`, so this
subset can be assembled by a stock MIPS GAS. It does not add Radiax mnemonic
parsing or disassembly to Binutils. The CI script checks the exact MFRAD/MTRAD
SUBOP values and register fields in emitted words, then confirms that GAS
accepts the object. Arithmetic, dual-MAC, circular-buffer load/store, and
loop-control instructions remain outside this first subset.

The encoding is based on the Lexra LX5280 Data Sheet, Release 1.9,
§§5.2.1, 5.3.5 and 5.3.7 (pages 53 and 59-61).

Run these tests with a GCC built from this branch, not a stock system
cross-compiler. The current CI cross target is little-endian
`mipsel-linux-gnu`; the LX5280 ISA profile itself does not select endianness.
