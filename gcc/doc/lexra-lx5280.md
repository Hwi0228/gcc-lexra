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

The DejaGNU test
"gcc/testsuite/gcc.target/mips/lexra-lx5280-no-unaligned.c" checks optimized
packed loads and stores for the absence of LWL/LWR/SWL/SWR. It must be run
with a GCC built from this branch, not a stock system cross-compiler.
