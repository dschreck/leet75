import { RecentCounter } from './solution';

describe('933. Number of Recent Calls', () => {
  it('exports RecentCounter', () => {
    expect(RecentCounter).toBeInstanceOf(Function);
  });

  it('example 1: the documented call sequence', () => {
    const counter = new RecentCounter();
    expect(counter.ping(1)).toBe(1);
    expect(counter.ping(100)).toBe(2);
    expect(counter.ping(3001)).toBe(3);
    expect(counter.ping(3002)).toBe(3);
  });
});
