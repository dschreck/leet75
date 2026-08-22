import { letterCombinations } from './solution';

describe('17. Letter Combinations of a Phone Number', () => {
  it('exports letterCombinations', () => {
    expect(letterCombinations).toBeInstanceOf(Function);
  });

  it('example 1: two digits', () => {
    expect(letterCombinations('23')).toEqual([
      'ad',
      'ae',
      'af',
      'bd',
      'be',
      'bf',
      'cd',
      'ce',
      'cf',
    ]);
  });

  it('example 2: single digit', () => {
    expect(letterCombinations('2')).toEqual(['a', 'b', 'c']);
  });
});
