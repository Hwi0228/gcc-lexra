/* { dg-do compile } */
/* { dg-options "-O2 -march=lx5280 -mno-abicalls -fno-pic" } */

struct __attribute__((packed)) lx5280_packed_word
{
  unsigned char prefix;
  unsigned int word;
};

__attribute__((noinline))
unsigned int
lx5280_load_packed_word (const struct lx5280_packed_word *p)
{
  return p->word;
}

__attribute__((noinline))
void
lx5280_store_packed_word (struct lx5280_packed_word *p, unsigned int value)
{
  p->word = value;
}

/* { dg-final { scan-assembler-not "\\<(lwl|lwr|swl|swr)\\>" } } */
