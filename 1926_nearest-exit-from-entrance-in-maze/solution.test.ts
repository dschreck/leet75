import { nearestExit } from './solution';

describe('1926. Nearest Exit from Entrance in Maze', () => {
  it('exports nearestExit', () => {
    expect(nearestExit).toBeInstanceOf(Function);
  });

  it('example 1: nearest exit is one step up', () => {
    expect(
      nearestExit(
        [
          ['+', '+', '.', '+'],
          ['.', '.', '.', '+'],
          ['+', '+', '+', '.'],
        ],
        [1, 2],
      ),
    ).toBe(1);
  });

  it('example 2: the entrance itself does not count as an exit', () => {
    expect(
      nearestExit(
        [
          ['+', '+', '+'],
          ['.', '.', '.'],
          ['+', '+', '+'],
        ],
        [1, 0],
      ),
    ).toBe(2);
  });

  it('example 3: no exit reachable', () => {
    expect(nearestExit([['.', '+']], [0, 0])).toBe(-1);
  });
});
