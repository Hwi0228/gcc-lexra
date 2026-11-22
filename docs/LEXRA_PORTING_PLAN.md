# GCC-Lexra Porting Plan

> Status: planning document. No compiler, assembler, emulator, or runtime support is implemented by this document.

## Project goal

Develop a maintainable GNU toolchain configuration for Lexra processors by reusing GCC's existing MIPS backend wherever the architectural and ABI specifications permit it.

The first implementation target is the Lexra LX5280 family. Other Lexra cores (including LX418x and LX458x variants) must be treated as separate targets or feature profiles until their ISA, endianness, ABI, and optional instruction sets have been verified from primary documentation or reliable hardware/toolchain evidence.

The project should prefer a small, auditable patch set over an unnecessary long-lived GCC fork. Keep changes structured so that individual patches can eventually be proposed upstream.

## Non-goals for the first milestone

- Do not create a new GCC machine-description backend from scratch.
- Do not claim complete Linux, libc, or board support before validating the ABI and runtime.
- Do not assume every Lexra core has the same instruction restrictions.
- Do not treat successful compilation for a generic MIPS CPU as proof of Lexra compatibility.
- Do not modify the GCC default branch directly.

## Architecture and compatibility research

Before changing code, record the following for each intended CPU model:

- Exact core name, revision, and supported ISA level.
- Endianness (little, big, or configurable).
- Register set and any architectural differences from the corresponding MIPS ISA.
- Supported, optional, and unsupported instructions.
- Branch-delay and load-delay behavior, if applicable.
- Unaligned load/store semantics and exception behavior.
- Multiply/divide and HI/LO behavior.
- FPU, DSP, and other optional extensions.
- ABI, calling convention, ELF machine flags, relocation types, and object-file conventions.
- Existing Linux kernel, bootloader, binutils, libc, and vendor-toolchain assumptions.

Create a source-and-evidence table in `docs/ARCHITECTURE.md`. Each non-obvious architectural claim should cite a datasheet, manual, upstream patch, disassembly, or reproducible hardware observation. Do not generalize a property of LX5280 to all Lexra processors.

## Proposed implementation phases

### Phase 0 — Establish a reproducible baseline

- Record the GCC upstream revision used by this fork.
- Record the corresponding Binutils, GDB, Linux, and libc versions considered for compatibility.
- Build an unmodified MIPS cross compiler as a baseline.
- Save configure options, build logs, compiler version output, and test results.
- Identify an existing MIPS CPU profile that is closest to each Lexra core, but do not assume it is equivalent.
- Add a short developer guide describing the supported host build environment.

**Exit criteria:** another developer can reproduce the baseline toolchain build and its test results.

### Phase 1 — Define the target model

- Decide whether the first target can be represented as a MIPS CPU tuning/ISA profile or requires explicit target hooks and feature flags.
- Define a canonical CPU name (initial proposal: `lx5280`) and document accepted aliases, if any.
- Define target defaults separately from user-overridable options.
- Ensure CPU selection rejects invalid combinations instead of silently falling back to generic MIPS.
- Confirm the correct ELF ABI, endianness, and assembler architecture attributes before advertising a Linux target triple.
- Document how `-march`, `-mtune`, `-mabi`, and endianness options interact.

**Exit criteria:** GCC recognizes the target selection consistently and reports the intended target configuration. No unsupported ABI or OS compatibility is implied.

### Phase 2 — GCC MIPS backend changes

Investigate the existing MIPS backend before editing it:

- `gcc/config/mips/` target option definitions and option override logic.
- CPU/ISA tables and architecture feature predicates.
- Machine-description patterns for loads, stores, unaligned accesses, and block moves.
- Built-in functions and instruction availability checks.
- Register, scheduling, and cost-model definitions.
- Multilib selection and target defaults.

For the first core:

- Add only verified architectural feature flags.
- Prevent instruction selection from emitting instructions absent from the target ISA.
- Implement correct fallback sequences for operations that the compiler normally expands using unavailable instructions.
- Ensure volatile accesses, packed structures, strict-alignment behavior, atomics, and block copies remain semantically correct.
- Check both optimized and unoptimized output; do not rely on a single source-level test.
- Keep CPU-specific behavior isolated so other MIPS targets do not regress.

**Exit criteria:** targeted assembly and object files contain no forbidden instructions, and semantic tests pass on a compatible execution model or hardware.

### Phase 3 — Binutils and ELF compatibility

GCC alone is not a complete toolchain. Determine whether the selected Binutils version already understands the target's instruction subset and object-file conventions.

Review:

- GAS CPU/architecture selection and instruction acceptance.
- Disassembler support and correct decoding.
- ELF machine flags, ABI flags, relocations, and linker emulation.
- Linker scripts and startup object expectations.
- Whether generic MIPS ELF output is genuinely compatible with the target environment.

Add or update Binutils support only where evidence requires it. A compiler-side restriction is not sufficient if inline assembly or hand-written assembly can still introduce unsupported instructions.

**Exit criteria:** assembler, linker, and disassembler agree on the target architecture and produce compatible ELF artifacts.

### Phase 4 — Runtime and system integration

- Validate libgcc helper routines, especially arithmetic and memory-operation helpers.
- Establish the required libc and sysroot separately from compiler support.
- Verify startup files, dynamic loader assumptions, TLS, exceptions, and stack alignment as applicable.
- Check kernel/bootloader expectations before claiming Linux execution support.
- Keep bare-metal and Linux targets distinct if their runtime requirements differ.

**Exit criteria:** representative programs link against a documented sysroot and execute correctly in the supported environment.

### Phase 5 — Regression tests and CI

Add tests in layers:

1. **Option tests:** accepted/rejected CPU, ISA, ABI, and endianness combinations.
2. **Compile tests:** C and (if supported) C++ at `-O0`, `-O1`, `-O2`, `-O3`, and `-Os`.
3. **Instruction tests:** scan disassembly for every instruction known to be unavailable on the selected core.
4. **Semantic tests:** packed structures, byte-wise and unaligned accesses, memcpy/memmove, integer arithmetic, branches, calls, stack frames, and volatile memory.
5. **Assembler tests:** unsupported mnemonics must be rejected when the architecture mode is selected.
6. **Link tests:** relocations, ABI flags, startup files, and representative static binaries.
7. **Execution tests:** run under a Lexra-aware emulator or real hardware when available.

QEMU's generic MIPS CPU models may be useful for testing shared MIPS behavior, but they are not a Lexra conformance oracle unless a model explicitly enforces the relevant Lexra restrictions. A passing test on generic MIPS does not prove Lexra compatibility.

For instruction validation, prefer parsing the final object-file disassembly over grepping compiler assembly alone. Include inline assembly and linked library objects in the validation scope. Maintain a per-core forbidden/required instruction list backed by the architecture evidence.

**Exit criteria:** CI produces reproducible pass/fail results and catches deliberate insertion of a forbidden instruction.

### Phase 6 — Hardware validation and release

- Identify the exact Lexra board and silicon revision.
- Record boot firmware, kernel, memory map, peripheral assumptions, and available debug access.
- Run arithmetic, memory, alignment, calling-convention, exception, and library tests.
- Compare results against a trusted vendor toolchain or known-good binaries where possible.
- Publish supported CPU models, known limitations, build instructions, and test coverage.
- Tag releases only after the supported configuration is reproducible.

## Testing strategy without Lexra hardware

Testing should be explicit about what it proves:

| Test environment | What it can establish | What it cannot establish by itself |
| --- | --- | --- |
| GCC compile-only tests | Target option handling and code-generation patterns | Runtime correctness |
| Object disassembly checker | Absence of known forbidden instructions in inspected objects | Correct behavior of every instruction sequence |
| Generic MIPS QEMU | Shared MIPS execution behavior | Lexra-specific instruction restrictions or timing |
| Lexra-aware emulator | Behavior implemented by that emulator model | Silicon quirks not modeled |
| Real Lexra board | Hardware behavior for the tested board/core revision | Compatibility with every Lexra model |

A Lexra-aware QEMU model is a separate project and should follow, not block, the first compiler-side milestones. Emulator behavior must be validated against primary ISA documentation or hardware observations.

## Repository organization

Suggested documentation and test layout:

- `docs/ARCHITECTURE.md` — per-core ISA/ABI facts and evidence.
- `docs/BUILDING.md` — reproducible cross-toolchain build instructions.
- `docs/TESTING.md` — test layers, commands, expected results, and limitations.
- `docs/LEXRA_PORTING_PLAN.md` — this roadmap.
- `gcc/testsuite/gcc.target/mips/` — GCC target regression tests, following existing GCC conventions.
- `toolchain-tests/` — project-level scripts for disassembly and ELF validation, if needed.

Do not add generated compiler binaries, sysroots, or large build artifacts to Git.

## Contribution and change management

- Keep one functional change per commit.
- Separate architecture research, GCC target changes, Binutils changes, runtime changes, and CI changes.
- Include a test command and its result in every implementation pull request.
- Preserve existing GCC source structure and coding conventions.
- Avoid unrelated formatting or mass refactoring.
- Never describe a feature as supported until its tests and evidence are present.

## Immediate next tasks

1. Confirm the exact intended first core (LX5280 is the current proposal).
2. Gather and cite its primary ISA and ABI documentation.
3. Record the fork's GCC revision and reproduce a baseline MIPS cross-compiler build in Codespaces.
4. Inspect the current MIPS backend option tables and unaligned-access expansion paths.
5. Write minimal compile-only tests that expose the current MIPS code-generation behavior.
6. Decide whether the first patch is a target-option/feature-model change or a smaller backend correction.
7. Add a disassembly-based forbidden-instruction test before implementing broad optimizations.

## Definition of done for the first usable milestone

The first milestone is complete only when:

- The target is selected explicitly and documented.
- GCC does not emit any instruction documented as unavailable on that exact core in the tested code paths.
- GAS rejects unsupported instructions in the corresponding architecture mode, or the limitation is explicitly documented.
- Final linked objects pass the ISA checker.
- Representative semantic tests pass in a Lexra-aware emulator or on hardware.
- Build and test instructions are reproducible by another contributor.
