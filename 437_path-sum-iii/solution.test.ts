import { pathSum, TreeNode } from './solution';

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

describe('437. Path Sum III', () => {
  it('exports pathSum', () => {
    expect(pathSum).toBeInstanceOf(Function);
  });

  it('example 1: three downward paths sum to 8', () => {
    expect(
      pathSum(buildTree([10, 5, -3, 3, 2, null, 11, 3, -2, null, 1]), 8),
    ).toBe(3);
  });

  it('example 2: three downward paths sum to 22', () => {
    expect(
      pathSum(
        buildTree([5, 4, 8, 11, null, 13, 4, 7, 2, null, null, 5, 1]),
        22,
      ),
    ).toBe(3);
  });
});
