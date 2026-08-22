import { moveZeroes } from './solution';

describe('283. Move Zeroes', () => {
  it('exports moveZeroes', () => {
    expect(moveZeroes).toBeInstanceOf(Function);
  });

  it('example 1: zeroes move to the end in place', () => {
    const nums = [0, 1, 0, 3, 12];
    moveZeroes(nums);
    expect(nums).toEqual([1, 3, 12, 0, 0]);
  });

  it('example 2: single zero', () => {
    const nums = [0];
    moveZeroes(nums);
    expect(nums).toEqual([0]);
  });
});
