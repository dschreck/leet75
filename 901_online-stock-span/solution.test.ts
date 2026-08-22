import { StockSpanner } from './solution';

describe('901. Online Stock Span', () => {
  it('exports StockSpanner', () => {
    expect(StockSpanner).toBeInstanceOf(Function);
  });

  it('example 1: the documented call sequence', () => {
    const spanner = new StockSpanner();
    expect(spanner.next(100)).toBe(1);
    expect(spanner.next(80)).toBe(1);
    expect(spanner.next(60)).toBe(1);
    expect(spanner.next(70)).toBe(2);
    expect(spanner.next(60)).toBe(1);
    expect(spanner.next(75)).toBe(4);
    expect(spanner.next(85)).toBe(6);
  });
});
