import { Trie } from './solution';

describe('208. Implement Trie (Prefix Tree)', () => {
  it('exports Trie', () => {
    expect(Trie).toBeInstanceOf(Function);
  });

  it('example 1: the documented call sequence', () => {
    const trie = new Trie();
    trie.insert('apple');
    expect(trie.search('apple')).toBe(true);
    expect(trie.search('app')).toBe(false);
    expect(trie.startsWith('app')).toBe(true);
    trie.insert('app');
    expect(trie.search('app')).toBe(true);
  });
});
