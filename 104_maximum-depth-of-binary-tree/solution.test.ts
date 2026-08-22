import { maxDepth, TreeNode } from './solution';

function buildTree(values: (number | null)[]): TreeNode | null {
  if (values.length === 0 || values[0] === null) return null;
  const root = new TreeNode(values[0]);
  const queue: TreeNode[] = [root];
  let i = 1;
  while (queue.length > 0 && i < values.length) {
    const node = queue.shift() as TreeNode;
    const left = values[i++];
    if (left !== null && left !== undefined) {
      node.left = new TreeNode(left);
      queue.push(node.left);
    }
    const right = values[i++];
    if (right !== null && right !== undefined) {
      node.right = new TreeNode(right);
      queue.push(node.right);
    }
  }
  return root;
}

describe('104. Maximum Depth of Binary Tree', () => {
  it('exports maxDepth', () => {
    expect(maxDepth).toBeInstanceOf(Function);
  });

  it('example 1: three levels', () => {
    expect(maxDepth(buildTree([3, 9, 20, null, null, 15, 7]))).toBe(3);
  });

  it('example 2: right-leaning chain', () => {
    expect(maxDepth(buildTree([1, null, 2]))).toBe(2);
  });
});
