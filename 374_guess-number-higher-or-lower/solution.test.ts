import { guessNumber, setPick } from './solution';

describe('374. Guess Number Higher or Lower', () => {
  it('exports guessNumber', () => {
    expect(guessNumber).toBeInstanceOf(Function);
  });

  it('example 1: n = 10, pick = 6', () => {
    setPick(6);
    expect(guessNumber(10)).toBe(6);
  });

  it('example 2: n = 1, pick = 1', () => {
    setPick(1);
    expect(guessNumber(1)).toBe(1);
  });

  it('example 3: n = 2, pick = 1', () => {
    setPick(1);
    expect(guessNumber(2)).toBe(1);
  });
});
