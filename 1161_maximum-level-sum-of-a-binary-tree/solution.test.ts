import { maxLevelSum, TreeNode } from './solution';

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

describe('1161. Maximum Level Sum of a Binary Tree', () => {
  it('exports maxLevelSum', () => {
    expect(maxLevelSum).toBeInstanceOf(Function);
  });

  it('example 1: level 2 sums to 7', () => {
    expect(maxLevelSum(buildTree([1, 7, 0, 7, -8, null, null]))).toBe(2);
  });

  it('example 2: level 2 wins despite deeper levels', () => {
    expect(
      maxLevelSum(
        buildTree([989, null, 10250, 98693, -89388, null, null, null, -32127]),
      ),
    ).toBe(2);
  });
});
