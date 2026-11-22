/* { dg-do compile } */
/* { dg-options "-march=lx5280 -mno-abicalls -fno-pic" } */

/* The immediate selects a user-visible Radiax register:
   CBS0=0, CBS2=2, CBE0=4, CBE2=6, LPS0=16, LPC0=18, MMD=24.  */

__attribute__((noinline))
unsigned int
lx5280_read_cbs0 (void)
{
  return (unsigned int) __builtin_mips_lx5280_mfru (0);
}

__attribute__((noinline))
unsigned int
lx5280_read_mmd (void)
{
  return (unsigned int) __builtin_mips_lx5280_mfru (24);
}

__attribute__((noinline))
void
lx5280_write_cbs2 (unsigned int value)
{
  __builtin_mips_lx5280_mtru (value, 2);
}

__attribute__((noinline))
void
lx5280_write_lpc0 (unsigned int value)
{
  __builtin_mips_lx5280_mtru (value, 18);
}

/* { dg-final { scan-assembler "\\.word[[:space:]]+0x7c" } } */
