export class TreeNode {
  val: number;
  left: TreeNode | null;
  right: TreeNode | null;
  constructor(val?: number, left?: TreeNode | null, right?: TreeNode | null) {
    this.val = val ?? 0;
    this.left = left ?? null;
    this.right = right ?? null;
  }
}

export function searchBST(root: TreeNode | null, val: number): TreeNode | null {
  while (root !== null && root.val !== val) {
    root = val < root.val ? root.left : root.right;
  }
  return root;
}
