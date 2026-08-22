import { closeStrings } from './solution';

describe('1657. Determine if Two Strings Are Close', () => {
  it('exports closeStrings', () => {
    expect(closeStrings).toBeInstanceOf(Function);
  });

  it('example 1: reachable by swapping characters', () => {
    expect(closeStrings('abc', 'bca')).toBe(true);
  });

  it('example 2: different lengths', () => {
    expect(closeStrings('a', 'aa')).toBe(false);
  });

  it('example 3: reachable by transforming characters', () => {
    expect(closeStrings('cabbba', 'abbccc')).toBe(true);
  });
});
