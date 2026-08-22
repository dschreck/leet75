import { maxVowels } from './solution';

describe('1456. Maximum Number of Vowels in a Substring of Given Length', () => {
  it('exports maxVowels', () => {
    expect(maxVowels).toBeInstanceOf(Function);
  });

  it('example 1: substring "iii"', () => {
    expect(maxVowels('abciiidef', 3)).toBe(3);
  });

  it('example 2: every window is all vowels', () => {
    expect(maxVowels('aeiou', 2)).toBe(2);
  });

  it('example 3: best window holds 2 vowels', () => {
    expect(maxVowels('leetcode', 3)).toBe(2);
  });
});
