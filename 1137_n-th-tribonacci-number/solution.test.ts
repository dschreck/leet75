import { tribonacci } from './solution';

describe('1137. N-th Tribonacci Number', () => {
  it('exports tribonacci', () => {
    expect(tribonacci).toBeInstanceOf(Function);
  });

  it('example 1: n = 4', () => {
    expect(tribonacci(4)).toBe(4);
  });

  it('example 2: n = 25', () => {
    expect(tribonacci(25)).toBe(1389537);
  });
});
