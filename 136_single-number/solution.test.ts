import { singleNumber } from './solution';

describe('136. Single Number', () => {
  it('exports singleNumber', () => {
    expect(singleNumber).toBeInstanceOf(Function);
  });

  it('example 1: [2,2,1]', () => {
    expect(singleNumber([2, 2, 1])).toBe(1);
  });

  it('example 2: [4,1,2,1,2]', () => {
    expect(singleNumber([4, 1, 2, 1, 2])).toBe(4);
  });

  it('example 3: single element', () => {
    expect(singleNumber([1])).toBe(1);
  });
});
