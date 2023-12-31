import { reverseVowels } from './reverse_vowels_string';

describe('LeetCode #345: Reverse Vowels of a String', () => {
  test('should return the string with vowels reversed', () => {
    expect(reverseVowels('hello')).toBe('holle');
    expect(reverseVowels('leetcode')).toBe('leotcede');
    expect(reverseVowels('aA')).toBe('Aa');
  });
});
