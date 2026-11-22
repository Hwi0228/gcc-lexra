#!/usr/bin/env python3
"""Check LX5280 option separation, ABI defaults, and the real GCC-to-GAS path."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys


FORBIDDEN = {"lwl", "lwr", "swl", "swr"}
INSTRUCTION = re.compile(
    r"^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2,8}\s+)+"
    r"([a-z][a-z0-9_.]*)\b",
    re.IGNORECASE,
)


def run(command: list[str], *, input_text: str | None = None,
        expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if expect_success and result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + shlex.join(command)
            + "\n--- stdout ---\n"
            + result.stdout
            + "\n--- stderr ---\n"
            + result.stderr
        )
    if not expect_success and result.returncode == 0:
        raise RuntimeError(
            "Command unexpectedly succeeded:\n" + shlex.join(command)
        )
    return result


def parse_macros(output: str) -> dict[str, str]:
    macros: dict[str, str] = {}
    for line in output.splitlines():
        match = re.match(r"^#define\s+([A-Za-z_][A-Za-z0-9_]*)\s*(.*)$", line)
        if match:
            macros[match.group(1)] = match.group(2).strip()
    return macros


def macro_value(macros: dict[str, str], name: str) -> str:
    if name not in macros:
        raise RuntimeError(f"Required preprocessor macro is missing: {name}")
    return macros[name].strip().strip('"')


def check_macro(macros: dict[str, str], name: str, expected: str) -> None:
    actual = macro_value(macros, name)
    if actual != expected:
        raise RuntimeError(
            f"{name} mismatch: expected {expected!r}, got {actual!r}"
        )


def get_macros(cc: str, build_gcc_dir: str,
               options: list[str]) -> dict[str, str]:
    result = run(
        [cc, f"-B{build_gcc_dir}/", *options,
         "-dM", "-E", "-x", "c", "-"],
        input_text="int lx5280_option_probe;\n",
    )
    return parse_macros(result.stdout)


def check_macro_profiles(args: argparse.Namespace, artifact_dir: Path) -> None:
    # Architecture and tuning are deliberately crossed in both directions.
    lx_arch = get_macros(
        args.cc, args.build_gcc_dir,
        ["-march=lx5280", "-mtune=r3000"],
    )
    check_macro(lx_arch, "_MIPS_ARCH", "lx5280")
    check_macro(lx_arch, "_MIPS_TUNE", "r3000")
    check_macro(lx_arch, "__mips", "1")
    check_macro(lx_arch, "__mips_fpr", "32")
    check_macro(lx_arch, "_MIPS_SIM", "_ABIO32")
    check_macro(lx_arch, "_ABIO32", "1")
    if "__mips_soft_float" not in lx_arch:
        raise RuntimeError("-march=lx5280 did not default to soft-float")
    if "__mips_hard_float" in lx_arch:
        raise RuntimeError("LX5280 unexpectedly defaulted to hard-float")

    r3000_arch = get_macros(
        args.cc, args.build_gcc_dir,
        ["-march=r3000", "-mtune=lx5280", "-msoft-float"],
    )
    check_macro(r3000_arch, "_MIPS_ARCH", "r3000")
    check_macro(r3000_arch, "_MIPS_TUNE", "lx5280")
    check_macro(r3000_arch, "__mips", "1")
    if "__mips_soft_float" not in r3000_arch:
        raise RuntimeError("explicit -msoft-float was not reflected in macros")

    hard_float = get_macros(
        args.cc, args.build_gcc_dir,
        ["-march=lx5280", "-mtune=r3000",
         "-mhard-float", "-mfp32"],
    )
    check_macro(hard_float, "_MIPS_ARCH", "lx5280")
    check_macro(hard_float, "_MIPS_TUNE", "r3000")
    if "__mips_hard_float" not in hard_float:
        raise RuntimeError("explicit -mhard-float did not override the default")
    if "__mips_soft_float" in hard_float:
        raise RuntimeError("hard-float override left the soft-float ABI enabled")

    # MIPS-I is a 32-bit ISA; 64-bit ABIs must not be accepted silently.
    source = artifact_dir / "abi-rejection.c"
    source.write_text("int lx5280_abi_rejection;\n", encoding="utf-8")
    for abi in ("64", "n32"):
        run(
            [args.cc, f"-B{args.build_gcc_dir}/", "-march=lx5280",
             f"-mabi={abi}", "-fsyntax-only", str(source)],
            expect_success=False,
        )

    macro_lines = []
    for label, macros in (
        ("march=lx5280 mtune=r3000", lx_arch),
        ("march=r3000 mtune=lx5280", r3000_arch),
        ("march=lx5280 explicit-hard-float", hard_float),
    ):
        macro_lines.append(f"[{label}]")
        macro_lines.extend(
            f"#define {name} {value}" for name, value in sorted(macros.items())
            if name.startswith("_MIPS_") or name.startswith("__mips")
        )
    (artifact_dir / "option-macros.txt").write_text(
        "\n".join(macro_lines) + "\n", encoding="utf-8"
    )


def find_assembler_command(transcript: str, expected_as: str) -> list[str]:
    expected_name = Path(expected_as).name
    candidates: list[list[str]] = []
    for line in transcript.splitlines():
        try:
            tokens = shlex.split(line)
        except ValueError:
            continue
        if not tokens:
            continue
        if Path(tokens[0]).name == expected_name:
            candidates.append(tokens)
    if not candidates:
        raise RuntimeError(
            f"GCC -v output did not invoke the configured assembler "
            f"{expected_as!r}.\n{transcript}"
        )
    return candidates[-1]


def scan_disassembly(text: str) -> tuple[int, list[str]]:
    decoded = 0
    forbidden: list[str] = []
    for line in text.splitlines():
        match = INSTRUCTION.match(line)
        if not match:
            continue
        decoded += 1
        mnemonic = match.group(1).lower()
        if mnemonic in FORBIDDEN:
            forbidden.append(mnemonic)
    return decoded, forbidden


def check_driver_path(args: argparse.Namespace, artifact_dir: Path) -> None:
    source = artifact_dir / "driver-check.c"
    assembly = artifact_dir / "driver-check.s"
    obj = artifact_dir / "driver-check.o"
    disassembly_file = artifact_dir / "driver-check.dis"
    readelf_file = artifact_dir / "driver-check.readelf"
    driver_log = artifact_dir / "driver-check.verbose.log"

    source.write_text(
        """
struct __attribute__((packed)) lx5280_driver_probe
{
  unsigned char prefix;
  unsigned int value;
};

__attribute__((noinline))
unsigned int
lx5280_driver_probe_load (const volatile struct lx5280_driver_probe *p)
{
  return p->value;
}
""".lstrip(),
        encoding="utf-8",
    )

    common = [
        args.cc, f"-B{args.build_gcc_dir}/", "-march=lx5280",
        "-mtune=r3000", "-msoft-float", "-mfp32",
        "-mno-abicalls", "-fno-pic",
    ]

    run([*common, "-S", str(source), "-o", str(assembly)])
    asm_text = assembly.read_text(encoding="utf-8")
    if ".module\tarch=mips1" not in asm_text and ".module arch=mips1" not in asm_text:
        raise RuntimeError("GCC assembly did not identify its GAS ISA as MIPS-I")
    if ".module\tsoftfloat" not in asm_text and ".module softfloat" not in asm_text:
        raise RuntimeError("GCC assembly did not mark the soft-float ABI")

    # This executes the GCC driver, which must launch the configured cross GAS.
    result = run([*common, "-v", "-c", str(source), "-o", str(obj)])
    transcript = result.stdout + "\n" + result.stderr
    driver_log.write_text(transcript, encoding="utf-8")
    if not obj.is_file() or obj.stat().st_size == 0:
        raise RuntimeError("GCC -c did not produce a non-empty object file")

    as_command = find_assembler_command(transcript, args.assembler)
    if any("lx5280" in token.lower() for token in as_command[1:]):
        raise RuntimeError(
            "GCC incorrectly forwarded the GCC-only -march=lx5280 option to GAS:\n"
            + shlex.join(as_command)
        )
    if "-mips1" not in as_command:
        raise RuntimeError(
            "GCC did not translate LX5280 to a GAS-compatible MIPS-I option:\n"
            + shlex.join(as_command)
        )

    header = run([args.readelf, "-h", str(obj)]).stdout
    readelf_file.write_text(header, encoding="utf-8")
    if "ELF32" not in header or "little endian" not in header:
        raise RuntimeError("GCC/GAS output is not ELF32 little-endian")
    flags = next(
        (line for line in header.splitlines() if "Flags:" in line), ""
    )
    if "o32" not in flags or "mips1" not in flags:
        raise RuntimeError(
            "ELF flags do not record the expected o32/MIPS-I profile:\n" + header
        )

    disassembly = run([args.objdump, "-d", str(obj)]).stdout
    disassembly_file.write_text(disassembly, encoding="utf-8")
    decoded, forbidden = scan_disassembly(disassembly)
    if decoded == 0:
        raise RuntimeError("objdump decoded no instructions from the GCC object")
    if forbidden:
        raise RuntimeError(
            "GCC/GAS object contains forbidden LX5280 instructions: "
            + ", ".join(forbidden)
        )

    (artifact_dir / "assembler-command.txt").write_text(
        shlex.join(as_command) + "\n", encoding="utf-8"
    )
    print(
        "GCC driver/GAS check passed: "
        f"{decoded} decoded instructions, ELF32/o32/MIPS-I, "
        "no LWL/LWR/SWL/SWR"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cc", required=True)
    parser.add_argument("--build-gcc-dir", required=True)
    parser.add_argument("--assembler", required=True)
    parser.add_argument("--objdump", required=True)
    parser.add_argument("--readelf", required=True)
    parser.add_argument("--artifacts", required=True)
    args = parser.parse_args()

    artifact_dir = Path(args.artifacts)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    try:
        check_macro_profiles(args, artifact_dir)
        check_driver_path(args, artifact_dir)
    except (OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("LX5280 option/ABI/driver validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
