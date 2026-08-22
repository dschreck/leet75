/**
 * 1372. Longest ZigZag Path in a Binary Tree
 * https://leetcode.com/problems/longest-zigzag-path-in-a-binary-tree/
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

export function longestZigZag(root: TreeNode | null): number {
  throw new Error('Not implemented: longestZigZag');
}
