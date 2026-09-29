class Solution:
    def searchBST(self, root, val: int):
        while root is not None and root.val != val:
            root = root.left if val < root.val else root.right
        return root
