import { leafSimilar, TreeNode } from './solution';

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

describe('872. Leaf-Similar Trees', () => {
  it('exports leafSimilar', () => {
    expect(leafSimilar).toBeInstanceOf(Function);
  });

  it('example 1: same leaf sequence, different shapes', () => {
    expect(
      leafSimilar(
        buildTree([3, 5, 1, 6, 2, 9, 8, null, null, 7, 4]),
        buildTree([
          3,
          5,
          1,
          6,
          7,
          4,
          2,
          null,
          null,
          null,
          null,
          null,
          null,
          9,
          8,
        ]),
      ),
    ).toBe(true);
  });

  it('example 2: leaves in a different order', () => {
    expect(leafSimilar(buildTree([1, 2, 3]), buildTree([1, 3, 2]))).toBe(false);
  });
});
