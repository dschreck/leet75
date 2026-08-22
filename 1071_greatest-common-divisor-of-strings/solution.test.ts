import { gcdOfStrings } from './solution';

describe('1071. Greatest Common Divisor of Strings', () => {
  it('exports gcdOfStrings', () => {
    expect(gcdOfStrings).toBeInstanceOf(Function);
  });

  it('example 1: str2 divides str1', () => {
    expect(gcdOfStrings('ABCABC', 'ABC')).toBe('ABC');
  });

  it('example 2: common divisor is shorter than both', () => {
    expect(gcdOfStrings('ABABAB', 'ABAB')).toBe('AB');
  });

  it('example 3: no common divisor', () => {
    expect(gcdOfStrings('LEET', 'CODE')).toBe('');
  });

  it('example 4: shared prefix but no common divisor', () => {
    expect(gcdOfStrings('AAAAAB', 'AAA')).toBe('');
  });
});
