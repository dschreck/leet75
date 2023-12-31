/**
 * Kids With the Greatest Number of Candies
 * https://leetcode.com/problems/kids-with-the-greatest-number-of-candies/
 * Topics: Array
 * Level: Easy
 *
 * Description:
 *
 * There are n kids with candies. You are given an integer array candies, where each candies[i]
 * represents the number of candies the ith kid has, and an integer extraCandies, denoting
 * the number of extra candies that you have.
 *
 * Return a boolean array result of length n, where result[i] is true if, after giving the ith
 * kid all the extraCandies, they will have the greatest number of candies among all the kids,
 * or false otherwise.
 *
 * Note that multiple kids can have the greatest number of candies.
 */

export function kidsWithCandies(candies: number[], extraCandies: number): boolean[] {
    const output: boolean[] = [];
    for (let i = 0; i < candies.length; i++) {
      const max = candies[i] + extraCandies;
      output[i] = true;
      for (let j = 0; j < candies.length; j++) {
        if (j === i) continue;
        if (candies[j] > max) output[i] = false;
      }
    } 
    return output;
};