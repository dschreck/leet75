import { deleteNode, TreeNode } from './solution';

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

function toArray(root: TreeNode | null): (number | null)[] {
  const out: (number | null)[] = [];
  const queue: (TreeNode | null)[] = [root];
  while (queue.length > 0) {
    const node = queue.shift() as TreeNode | null;
    if (node === null) {
      out.push(null);
      continue;
    }
    out.push(node.val);
    queue.push(node.left, node.right);
  }
  while (out.length > 0 && out[out.length - 1] === null) out.pop();
  return out;
}

describe('450. Delete Node in a BST', () => {
  it('exports deleteNode', () => {
    expect(deleteNode).toBeInstanceOf(Function);
  });

  it('example 1: deleting 3 has two accepted answers', () => {
    const result = toArray(deleteNode(buildTree([5, 3, 6, 2, 4, null, 7]), 3));
    expect([
      [5, 4, 6, 2, null, null, 7],
      [5, 2, 6, null, 4, null, 7],
    ]).toContainEqual(result);
  });

  it('example 2: key not present leaves the tree unchanged', () => {
    expect(toArray(deleteNode(buildTree([5, 3, 6, 2, 4, null, 7]), 0))).toEqual(
      [5, 3, 6, 2, 4, null, 7],
    );
  });

  it('example 3: empty tree', () => {
    expect(toArray(deleteNode(buildTree([]), 0))).toEqual([]);
  });
});
