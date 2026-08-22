import { goodNodes, TreeNode } from './solution';

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

describe('1448. Count Good Nodes in Binary Tree', () => {
  it('exports goodNodes', () => {
    expect(goodNodes).toBeInstanceOf(Function);
  });

  it('example 1: four good nodes', () => {
    expect(goodNodes(buildTree([3, 1, 4, 3, null, 1, 5]))).toBe(4);
  });

  it('example 2: node 2 is shadowed by an ancestor', () => {
    expect(goodNodes(buildTree([3, 3, null, 4, 2]))).toBe(3);
  });

  it('example 3: the root is always good', () => {
    expect(goodNodes(buildTree([1]))).toBe(1);
  });
});
