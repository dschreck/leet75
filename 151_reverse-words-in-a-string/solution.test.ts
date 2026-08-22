import { reverseWords } from './solution';

describe('151. Reverse Words in a String', () => {
  it('exports reverseWords', () => {
    expect(reverseWords).toBeInstanceOf(Function);
  });

  it('example 1: single spaces', () => {
    expect(reverseWords('the sky is blue')).toBe('blue is sky the');
  });

  it('example 2: leading and trailing spaces are dropped', () => {
    expect(reverseWords('  hello world  ')).toBe('world hello');
  });

  it('example 3: runs of spaces collapse to one', () => {
    expect(reverseWords('a good   example')).toBe('example good a');
  });
});
