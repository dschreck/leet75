class Solution:
    def compress(self, chars: list[str]) -> int:
        write = read = 0
        while read < len(chars):
            char, start = chars[read], read
            while read < len(chars) and chars[read] == char:
                read += 1
            chars[write] = char
            write += 1
            if read - start > 1:
                for digit in str(read - start):
                    chars[write] = digit
                    write += 1
        return write
