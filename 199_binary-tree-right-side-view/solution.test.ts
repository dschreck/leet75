import { rightSideView, TreeNode } from './solution';

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

describe('199. Binary Tree Right Side View', () => {
  it('exports rightSideView', () => {
    expect(rightSideView).toBeInstanceOf(Function);
  });

  it('example 1: rightmost node of each level', () => {
    expect(rightSideView(buildTree([1, 2, 3, null, 5, null, 4]))).toEqual([
      1, 3, 4,
    ]);
  });

  it('example 2: deepest level reached through a left child', () => {
    expect(rightSideView(buildTree([1, 2, 3, 4, null, null, null, 5]))).toEqual(
      [1, 3, 4, 5],
    );
  });

  it('example 3: right-leaning chain', () => {
    expect(rightSideView(buildTree([1, null, 3]))).toEqual([1, 3]);
  });

  it('example 4: empty tree', () => {
    expect(rightSideView(buildTree([]))).toEqual([]);
  });
});
