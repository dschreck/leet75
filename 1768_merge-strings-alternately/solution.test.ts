import { mergeAlternately } from './solution';

describe('1768. Merge Strings Alternately', () => {
  it('exports mergeAlternately', () => {
    expect(mergeAlternately).toBeInstanceOf(Function);
  });

  it('example 1: equal lengths', () => {
    expect(mergeAlternately('abc', 'pqr')).toBe('apbqcr');
  });

  it('example 2: word2 is longer, remainder appended', () => {
    expect(mergeAlternately('ab', 'pqrs')).toBe('apbqrs');
  });

  it('example 3: word1 is longer, remainder appended', () => {
    expect(mergeAlternately('abcd', 'pq')).toBe('apbqcd');
  });
});
