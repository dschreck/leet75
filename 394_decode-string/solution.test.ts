import { decodeString } from './solution';

describe('394. Decode String', () => {
  it('exports decodeString', () => {
    expect(decodeString).toBeInstanceOf(Function);
  });

  it('example 1: two sibling groups', () => {
    expect(decodeString('3[a]2[bc]')).toBe('aaabcbc');
  });

  it('example 2: nested groups', () => {
    expect(decodeString('3[a2[c]]')).toBe('accaccacc');
  });

  it('example 3: trailing literal characters', () => {
    expect(decodeString('2[abc]3[cd]ef')).toBe('abcabccdcdcdef');
  });
});
