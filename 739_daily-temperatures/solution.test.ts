import { dailyTemperatures } from './solution';

describe('739. Daily Temperatures', () => {
  it('exports dailyTemperatures', () => {
    expect(dailyTemperatures).toBeInstanceOf(Function);
  });

  it('example 1: mixed rises and falls', () => {
    expect(dailyTemperatures([73, 74, 75, 71, 69, 72, 76, 73])).toEqual([
      1, 1, 4, 2, 1, 1, 0, 0,
    ]);
  });

  it('example 2: strictly increasing', () => {
    expect(dailyTemperatures([30, 40, 50, 60])).toEqual([1, 1, 1, 0]);
  });

  it('example 3: three rising days', () => {
    expect(dailyTemperatures([30, 60, 90])).toEqual([1, 1, 0]);
  });
});
