/**
 * Asteroid Collision
 * https://leetcode.com/problems/asteroid-collision
 * Topic: Array, Stack, Simulation
 * Level: Medium
 *
 * Description:
 *
 * We are given an array asteroids of integers representing asteroids in a row.
 *
 * For each asteroid, the absolute value represents its size, and the sign represents its direction (positive meaning right, negative meaning left).
 * Each asteroid moves at the same speed.
 *
 * Find out the state of the asteroids after all collisions. If two asteroids meet, the smaller one will explode.
 * If both are the same size, both will explode. Two asteroids moving in the same direction will never meet.
 *
 * Examples:
 * 1/
 * Input: asteroids = [5,10,-5]
 * Output: [5,10]
 * Explanation: The 10 and -5 collide resulting in 10. The 5 and 10 never collide.
 * 2/
 * Input: asteroids = [8,-8]
 * Output: []
 * Explanation: The 8 and -8 collide exploding each other.
 * 3/
 * Input: asteroids = [10,2,-5]
 * Output: [10]
 * Explanation: The 2 and -5 collide resulting in -5. The 10 and -5 collide resulting in 10.
 */

export function asteroidCollision(asteroids: number[]): number[] {
  // This is a Stack question, so we should use a stack to solve it
  // We don't have to build a Stack class:
  //  Stacks are LIFO (Last In First Out)
  //  So we can use the push/pop methods to simulate a stack with an array
  const stack: number[] = [];

  // Loop through the asteroids

  for (let rock of asteroids) {
    let hasExploded = false;

    // if the rock is negative, the stack isn't empty, and the last rock in the stack is positive
    while (
      !hasExploded &&
      rock < 0 &&
      stack.length > 0 &&
      stack[stack.length - 1] > 0
    ) {
      hasExploded = stack[stack.length - 1] >= -rock; // if the rock is bigger than the last positive asteroid, then it explodes
      if (stack[stack.length - 1] <= -rock) {
        stack.pop();
      }
    }

    // if we haven't exploded, then push the rock to the stack
    if (!hasExploded) {
      stack.push(rock);
    }
  }
  
  return stack;
}
