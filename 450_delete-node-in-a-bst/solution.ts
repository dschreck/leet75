/**
 * 450. Delete Node in a BST
 * https://leetcode.com/problems/delete-node-in-a-bst/
 * Difficulty: Medium
 * Category: Binary Search Tree
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

export function deleteNode(
  root: TreeNode | null,
  key: number,
): TreeNode | null {
  throw new Error('Not implemented: deleteNode');
}
