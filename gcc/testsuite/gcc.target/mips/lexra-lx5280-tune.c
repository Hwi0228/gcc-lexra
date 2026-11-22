/* { dg-do compile } */
/* { dg-options "-march=r3000 -mtune=lx5280 -msoft-float -mno-abicalls -fno-pic" } */

/* Reversing the options must reverse only the selected architecture/tuning
   names, not conflate -mtune with -march.  */
#ifndef _MIPS_ARCH_R3000
#error "-march=r3000 did not select the R3000 architecture"
#endif

#ifndef _MIPS_TUNE_LX5280
#error "-mtune=lx5280 did not select the LX5280 tuning profile"
#endif

#if __mips != 1
#error "R3000 must remain MIPS-I"
#endif

int
lx5280_options_arch_r3000_tune_lx5280 (void)
{
  return __mips;
}
