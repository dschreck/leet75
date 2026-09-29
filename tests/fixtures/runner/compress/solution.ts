export function compress(chars: string[]): number {
  let write = 0;
  let read = 0;
  while (read < chars.length) {
    const char = chars[read];
    const start = read;
    while (read < chars.length && chars[read] === char) read++;
    chars[write++] = char;
    if (read - start > 1) {
      for (const digit of String(read - start)) chars[write++] = digit;
    }
  }
  return write;
}
