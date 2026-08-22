import { uniqueOccurrences } from './solution';

describe('1207. Unique Number of Occurrences', () => {
  it('exports uniqueOccurrences', () => {
    expect(uniqueOccurrences).toBeInstanceOf(Function);
  });

  it('example 1: counts 3, 2 and 1 are all distinct', () => {
    expect(uniqueOccurrences([1, 2, 2, 1, 1, 3])).toBe(true);
  });

  it('example 2: both values occur once', () => {
    expect(uniqueOccurrences([1, 2])).toBe(false);
  });

  it('example 3: negative values', () => {
    expect(uniqueOccurrences([-3, 0, 1, -3, 1, 1, 1, -3, 10, 0])).toBe(true);
  });
});
