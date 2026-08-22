/**
 * 872. Leaf-Similar Trees
 * https://leetcode.com/problems/leaf-similar-trees/
 * Difficulty: Easy
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

export function leafSimilar(
  root1: TreeNode | null,
  root2: TreeNode | null,
): boolean {
  throw new Error('Not implemented: leafSimilar');
}
