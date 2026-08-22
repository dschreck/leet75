import { calcEquation } from './solution';

describe('399. Evaluate Division', () => {
  it('exports calcEquation', () => {
    expect(calcEquation).toBeInstanceOf(Function);
  });

  it('example 1: unknown variables return -1', () => {
    const result = calcEquation(
      [
        ['a', 'b'],
        ['b', 'c'],
      ],
      [2.0, 3.0],
      [
        ['a', 'c'],
        ['b', 'a'],
        ['a', 'e'],
        ['a', 'a'],
        ['x', 'x'],
      ],
    );
    expect(result).toHaveLength(5);
    [6.0, 0.5, -1.0, 1.0, -1.0].forEach((expected, i) => {
      expect(result[i]).toBeCloseTo(expected, 5);
    });
  });

  it('example 2: multi-character variables', () => {
    const result = calcEquation(
      [
        ['a', 'b'],
        ['b', 'c'],
        ['bc', 'cd'],
      ],
      [1.5, 2.5, 5.0],
      [
        ['a', 'c'],
        ['c', 'b'],
        ['bc', 'cd'],
        ['cd', 'bc'],
      ],
    );
    expect(result).toHaveLength(4);
    [3.75, 0.4, 5.0, 0.2].forEach((expected, i) => {
      expect(result[i]).toBeCloseTo(expected, 5);
    });
  });

  it('example 3: a single equation', () => {
    const result = calcEquation(
      [['a', 'b']],
      [0.5],
      [
        ['a', 'b'],
        ['b', 'a'],
        ['a', 'c'],
        ['x', 'y'],
      ],
    );
    expect(result).toHaveLength(4);
    [0.5, 2.0, -1.0, -1.0].forEach((expected, i) => {
      expect(result[i]).toBeCloseTo(expected, 5);
    });
  });
});
