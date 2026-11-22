/* { dg-do compile } */
/* { dg-options "-march=lx5280 -mno-abicalls -fno-pic" } */

/*
   LX5280 must use byte/halfword/word-aligned fallback sequences for memory
   operations that generic MIPS I code may implement with LWL/LWR/SWL/SWR.
*/

typedef unsigned char lx5280_u8;
typedef unsigned short lx5280_u16;
typedef unsigned int lx5280_u32;

struct __attribute__((packed)) lx5280_packed_fields
{
  lx5280_u8 prefix;
  lx5280_u16 half;
  lx5280_u32 word;
};

struct __attribute__((packed)) lx5280_packed_bitfields
{
  lx5280_u8 prefix;
  unsigned int low : 7;
  unsigned int high : 25;
};

__attribute__((noinline))
lx5280_u16
lx5280_load_packed_half (const struct lx5280_packed_fields *p)
{
  return p->half;
}

__attribute__((noinline))
void
lx5280_store_packed_half (struct lx5280_packed_fields *p, lx5280_u16 value)
{
  p->half = value;
}

__attribute__((noinline))
lx5280_u32
lx5280_load_packed_word (const struct lx5280_packed_fields *p)
{
  return p->word;
}

__attribute__((noinline))
void
lx5280_store_packed_word (struct lx5280_packed_fields *p, lx5280_u32 value)
{
  p->word = value;
}

__attribute__((noinline))
lx5280_u16
lx5280_load_volatile_packed_half
  (const volatile struct lx5280_packed_fields *p)
{
  return p->half;
}

__attribute__((noinline))
void
lx5280_store_volatile_packed_half
  (volatile struct lx5280_packed_fields *p, lx5280_u16 value)
{
  p->half = value;
}

__attribute__((noinline))
lx5280_u32
lx5280_load_volatile_packed_word
  (const volatile struct lx5280_packed_fields *p)
{
  return p->word;
}

__attribute__((noinline))
void
lx5280_store_volatile_packed_word
  (volatile struct lx5280_packed_fields *p, lx5280_u32 value)
{
  p->word = value;
}

__attribute__((noinline))
lx5280_u32
lx5280_load_packed_bitfields (const struct lx5280_packed_bitfields *p)
{
  return p->low | (p->high << 7);
}

__attribute__((noinline))
void
lx5280_store_packed_bitfields (struct lx5280_packed_bitfields *p,
                               lx5280_u32 value)
{
  p->low = value & 0x7f;
  p->high = value >> 7;
}

__attribute__((noinline))
void
lx5280_copy_unaligned_bytes (lx5280_u8 *dest, const lx5280_u8 *source)
{
  __builtin_memcpy (dest + 1, source + 1, 12);
}

__attribute__((noinline))
void
lx5280_move_unaligned_bytes (lx5280_u8 *dest, const lx5280_u8 *source)
{
  __builtin_memmove (dest + 1, source + 2, 12);
}

/* { dg-final { scan-assembler-not "\\<(lwl|lwr|swl|swr)\\>" } } */
