/* { dg-do compile } */
/* { dg-options "-march=mips1 -mno-abicalls -fno-pic" } */

/*
   Baseline regression test for the generic GCC MIPS-I profile.

   This remains a generic MIPS-I control case. LX5280-specific code-generation
   checks are covered by lexra-lx5280-no-unaligned.c.
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
