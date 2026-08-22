/**
 * Search in a Binary Search Tree
 * https://leetcode.com/problems/search-in-a-binary-search-tree/
 * Topics: Tree, Binary Search Tree, Binary Tree
 * Level: Easy
 *
 * Description:
 *
 * You are given the root of a binary search tree (BST) and an integer val.
 *
 * Find the node in the BST that the node's value equals val and return the subtree rooted with that node.
 * If such a node does not exist, return null.
 *
 * Examples:
 * 1/
 * Input: root = [4,2,7,1,3], val = 2
 * Output: [2,1,3]
 * 2/
 * Input: root = [4,2,7,1,3], val = 5
 * Output: []
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

export function searchBST(root: TreeNode | null, val: number): TreeNode | null {
  // Edge cases: 
  // 1. If the root is null, return null
  // 2. If the root's value is equal to val, return the root
  if (!root) {
    return null;
  }
  
  if (root.val === val) {
    return root;
  }

  // If the val is less than the root's value, search the left subtree
  if (val < root.val) {
    return searchBST(root.left, val);
  }

  // If the val is greater than the root's value, search the right subtree
  if (val > root.val) {
    return searchBST(root.right, val);
  }

  return null;
}
