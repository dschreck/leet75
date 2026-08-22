import { canVisitAllRooms } from './solution';

describe('841. Keys and Rooms', () => {
  it('exports canVisitAllRooms', () => {
    expect(canVisitAllRooms).toBeInstanceOf(Function);
  });

  it('example 1: each room unlocks the next', () => {
    expect(canVisitAllRooms([[1], [2], [3], []])).toBe(true);
  });

  it('example 2: room 2 holds its own only key', () => {
    expect(canVisitAllRooms([[1, 3], [3, 0, 1], [2], [0]])).toBe(false);
  });
});
