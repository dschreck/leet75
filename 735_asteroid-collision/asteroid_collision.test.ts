import { asteroidCollision } from './asteroid_collision';

describe('735. Asteroid Collision', () => {
  it('asteroidCollision', () => {
    expect(asteroidCollision([5, 10, -5])).toStrictEqual([5, 10]);
    expect(asteroidCollision([8, -8])).toStrictEqual([]);
    expect(asteroidCollision([10, 2, -5])).toStrictEqual([10]);
    expect(asteroidCollision([-2, -1, 1, 2])).toStrictEqual([-2, -1, 1, 2]);
  });
});
