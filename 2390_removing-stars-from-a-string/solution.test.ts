import { removeStars } from './solution';

describe('2390. Removing Stars From a String', () => {
  it('exports removeStars', () => {
    expect(removeStars).toBeInstanceOf(Function);
  });

  it('example 1: three stars remove three characters', () => {
    expect(removeStars('leet**cod*e')).toBe('lecoe');
  });

  it('example 2: the whole string is removed', () => {
    expect(removeStars('erase*****')).toBe('');
  });
});
