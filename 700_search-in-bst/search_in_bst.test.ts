import { searchBST, TreeNode } from './search_in_bst';

describe('700. Search in Binary Search Tree', () => {
  it('searchBST', () => {
    expect(
      searchBST(
        new TreeNode(
          4,
          new TreeNode(2, new TreeNode(1), new TreeNode(3)),
          new TreeNode(7),
        ),
        2,
      ),
    ).toStrictEqual(new TreeNode(2, new TreeNode(1), new TreeNode(3)));
    expect(
      searchBST(
        new TreeNode(
          4,
          new TreeNode(2, new TreeNode(1), new TreeNode(3)),
          new TreeNode(7),
        ),
        5,
      ),
    ).toStrictEqual(null);
  });
});
