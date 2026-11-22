/* { dg-do compile } */
/* { dg-options "-march=lx5280 -mno-abicalls -fno-pic" } */

/*
   LX5280 must use byte/halfword/word-aligned fallback sequences for memory
   operations that generic MIPS I code may implement with LWL/LWR/SWL/SWR.
*/

struct __attribute__((packed)) lx5280_packed_word
{
  unsigned char prefix;
  unsigned int word;
};

struct __attribute__((packed)) lx5280_packed_bitfield
{
  unsigned char prefix;
  unsigned int word : 32;
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

__attribute__((noinline))
unsigned int
lx5280_load_packed_volatile_word (const volatile struct lx5280_packed_word *p)
{
  return p->word;
}

__attribute__((noinline))
unsigned int
lx5280_load_packed_bitfield (const struct lx5280_packed_bitfield *p)
{
  return p->word;
}

__attribute__((noinline))
void
lx5280_store_packed_bitfield (struct lx5280_packed_bitfield *p,
                              unsigned int value)
{
  p->word = value;
}

__attribute__((noinline))
void
lx5280_copy_unaligned_bytes (unsigned char *dest,
                             const unsigned char *source)
{
  __builtin_memcpy (dest + 1, source + 1, 8);
}

/* { dg-final { scan-assembler-not "\\<(lwl|lwr|swl|swr)\\>" } } */
