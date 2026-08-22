import { minDistance } from './solution';

describe('72. Edit Distance', () => {
  it('exports minDistance', () => {
    expect(minDistance).toBeInstanceOf(Function);
  });

  it('example 1: replace then two removals', () => {
    expect(minDistance('horse', 'ros')).toBe(3);
  });

  it('example 2: mixed removals, replacements and an insert', () => {
    expect(minDistance('intention', 'execution')).toBe(5);
  });
});
