/* { dg-do compile } */
/* { dg-options "-march=mips1 -mno-abicalls -fno-pic -O2" } */

/*
   Baseline regression test for the GCC MIPS backend.

   This deliberately uses the generic MIPS-I profile because the LX5280
   target option has not been implemented yet. When that target is added,
   switch the options to -march=lx5280 and keep these code-generation checks.
*/

struct aligned_words
{
  unsigned int word[4];
};

__attribute__((noinline))
unsigned int
lexra_ci_sum_words (const volatile struct aligned_words *p)
{
  return p->word[0] + p->word[1] + p->word[2] + p->word[3];
}

/* Aligned accesses must not require MIPS unaligned left/right instructions. */
/* { dg-final { scan-assembler-not "\\<(lwl|lwr|swl|swr)\\>" } } */
