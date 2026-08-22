import { compress } from './solution';

describe('443. String Compression', () => {
  it('exports compress', () => {
    expect(compress).toBeInstanceOf(Function);
  });

  it('example 1: groups of 2, 2 and 3', () => {
    const chars = ['a', 'a', 'b', 'b', 'c', 'c', 'c'];
    expect(compress(chars)).toBe(6);
    expect(chars.slice(0, 6)).toEqual(['a', '2', 'b', '2', 'c', '3']);
  });

  it('example 2: a single character is left uncompressed', () => {
    const chars = ['a'];
    expect(compress(chars)).toBe(1);
    expect(chars.slice(0, 1)).toEqual(['a']);
  });

  it('example 3: a count of 12 takes two slots', () => {
    const chars = [
      'a',
      'b',
      'b',
      'b',
      'b',
      'b',
      'b',
      'b',
      'b',
      'b',
      'b',
      'b',
      'b',
    ];
    expect(compress(chars)).toBe(4);
    expect(chars.slice(0, 4)).toEqual(['a', 'b', '1', '2']);
  });
});
