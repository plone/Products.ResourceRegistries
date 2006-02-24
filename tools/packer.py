import re

class Packer:
    def __init__(self):
        self.patterns = []

    def copy(self):
        result = Packer()
        result.patterns = self.patterns[:]
        return result

    def _repl(self, match):
        # store protected part
        self.replacelist.append(match.group(0))
        # return escaped index
        return "\x00%i" % len(self.replacelist)

    def pack(self, input):
        # list of protected parts
        self.replacelist = []
        # escape the escapechar
        output = input.replace('\x00','\x00\x00')
        for regexp, replacement in self.patterns:
            if replacement is None:
                # protect the matched parts
                output = regexp.sub(self._repl, output)
            else:
                output = regexp.sub(replacement, output)
        # restore protected parts
        replacelist = list(enumerate(self.replacelist))
        replacelist.reverse() # from back to front, so 1 doesn't break 10 etc.
        for index, replacement in replacelist:
            # we use lambda in here, so the real string is used and no escaping
            # is done on it
            output = re.sub('(?<!\x00)\x00%i' % (index+1), lambda m:replacement, output)
        # unescape
        output = output.replace('\x00\x00','\x00')
        # done
        return output

    def protect(self, pattern, flags=None):
        self.sub(pattern, None, flags)

    def sub(self, pattern, replacement, flags=None):
        if flags is None:
            self.patterns.append((re.compile(pattern), replacement))
        else:
            self.patterns.append((re.compile(pattern, flags), replacement))
