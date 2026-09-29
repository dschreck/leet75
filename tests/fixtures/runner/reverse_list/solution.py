class Solution:
    def reverseList(self, head):
        previous = None
        while head is not None:
            head.next, previous, head = previous, head, head.next
        return previous
