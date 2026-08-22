/**
 * 437. Path Sum III
 * https://leetcode.com/problems/path-sum-iii/
 * Difficulty: Medium
 * Category: Binary Tree - DFS
 *
 * See README.md in this folder for the full problem statement.
 */

/**
 * Definition for a binary tree node.
 */
export class TreeNode {
  val: number;
  left: TreeNode | null;
  right: TreeNode | null;
  constructor(val?: number, left?: TreeNode | null, right?: TreeNode | null) {
    this.val = val === undefined ? 0 : val;
    this.left = left === undefined ? null : left;
    this.right = right === undefined ? null : right;
  }
}

export function pathSum(root: TreeNode | null, targetSum: number): number {
  throw new Error('Not implemented: pathSum');
}
