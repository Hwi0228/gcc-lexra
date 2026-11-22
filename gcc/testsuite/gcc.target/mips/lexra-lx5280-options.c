/* { dg-do compile } */
/* { dg-options "-march=lx5280 -mtune=r3000 -mabi=32 -mno-abicalls -fno-pic" } */

/* -march selects the ISA; -mtune selects the scheduling/cost profile.  */
#ifndef _MIPS_ARCH_LX5280
#error "-march=lx5280 did not select the LX5280 architecture"
#endif

#ifndef _MIPS_TUNE_R3000
#error "-mtune=r3000 did not select the R3000 tuning profile"
#endif

#if __mips != 1
#error "LX5280 must select the MIPS-I ISA level"
#endif

#if __mips_fpr != 32
#error "the initial LX5280 profile expects 32-bit FPR mode"
#endif

#if _MIPS_SIM != _ABIO32
#error "the initial Linux cross-toolchain profile expects the o32 ABI"
#endif

#ifndef __mips_soft_float
#error "LX5280 must default to the soft-float ABI"
#endif

#ifdef __mips_hard_float
#error "soft-float must be the default unless explicitly overridden"
#endif

int
lx5280_options_arch_lx5280_tune_r3000 (void)
{
  return __mips;
}
