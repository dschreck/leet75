import { lowestCommonAncestor, TreeNode } from './solution';

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

function find(root: TreeNode | null, val: number): TreeNode {
  const stack: (TreeNode | null)[] = [root];
  while (stack.length > 0) {
    const node = stack.pop() as TreeNode | null;
    if (node === null) continue;
    if (node.val === val) return node;
    stack.push(node.left, node.right);
  }
  throw new Error(`No node with value ${val}`);
}

describe('236. Lowest Common Ancestor of a Binary Tree', () => {
  it('exports lowestCommonAncestor', () => {
    expect(lowestCommonAncestor).toBeInstanceOf(Function);
  });

  it('example 1: LCA of 5 and 1 is the root', () => {
    const root = buildTree([3, 5, 1, 6, 2, 0, 8, null, null, 7, 4]);
    const lca = lowestCommonAncestor(root, find(root, 5), find(root, 1));
    expect(lca?.val).toBe(3);
  });

  it('example 2: a node can be its own descendant', () => {
    const root = buildTree([3, 5, 1, 6, 2, 0, 8, null, null, 7, 4]);
    const lca = lowestCommonAncestor(root, find(root, 5), find(root, 4));
    expect(lca?.val).toBe(5);
  });

  it('example 3: two-node tree', () => {
    const root = buildTree([1, 2]);
    const lca = lowestCommonAncestor(root, find(root, 1), find(root, 2));
    expect(lca?.val).toBe(1);
  });
});
