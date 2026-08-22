import { longestZigZag, TreeNode } from './solution';

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

describe('1372. Longest ZigZag Path in a Binary Tree', () => {
  it('exports longestZigZag', () => {
    expect(longestZigZag).toBeInstanceOf(Function);
  });

  it('example 1: right -> left -> right', () => {
    expect(
      longestZigZag(
        buildTree([
          1,
          null,
          1,
          1,
          1,
          null,
          null,
          1,
          1,
          null,
          1,
          null,
          null,
          null,
          1,
        ]),
      ),
    ).toBe(3);
  });

  it('example 2: left -> right -> left -> right', () => {
    expect(
      longestZigZag(buildTree([1, 1, 1, null, 1, null, null, 1, 1, null, 1])),
    ).toBe(4);
  });

  it('example 3: a lone root has no edges', () => {
    expect(longestZigZag(buildTree([1]))).toBe(0);
  });
});
