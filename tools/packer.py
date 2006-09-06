import re


class KeywordMapper:
    def __init__(self, regexp, encoder):
        if isinstance(regexp, (str, unicode)):
            self.regexp = re.compile(regexp)
        else:
            self.regexp = regexp
        self.encoder = encoder
        self.mapping = {}

    def analyseKeywords(self, input):
        matches = self.regexp.findall(input)

        protected = {}
        keyword_count = {}
        index = 0
        for match in matches:
            if match not in keyword_count:
                keyword_count[match] = 0
                protected[self.encoder(index)] = index
                index = index + 1
            keyword_count[match] = keyword_count[match] + 1

        for match in matches:
            if match in protected and keyword_count[match]:
                keyword_count[match] = 0

        protected = {}
        for match in keyword_count:
            if not keyword_count[match]:
                protected[match] = None

        ## sorted_matches = [(c,len(v),v) for v,c in keyword_count.iteritems()]
        # the above line implements the original behaviour, the code below
        # removes keywords which have not enough weight to be encoded, in total
        # this saves some bytes, because the total length of the generated
        # codes is a bit smaller. This needs corresponding code in the
        # fast_decode javascript function of the decoder, see comment there
        sorted_matches = []
        for value, count in keyword_count.iteritems():
            weight = count * len(value)
            if len(value) >= weight:
                keyword_count[value] = 0
                sorted_matches.append((0, value))
            else:
                sorted_matches.append((weight, value))
        sorted_matches.sort()
        sorted_matches.reverse()
        sorted_matches = [x[-1] for x in sorted_matches]

        index = 0
        mapping = {}
        for match in sorted_matches:
            if not keyword_count[match]:
                if match not in protected:
                    mapping[match] = (-1, match)
                continue
            while 1:
                encoded = self.encoder(index)
                index = index + 1
                if encoded in protected:
                    mapping[encoded] = (index-1, encoded)
                    continue
                else:
                    break
            mapping[match] = (index-1, encoded)

        return mapping

    def analyse(self, input):
        self.mapping = self.analyseKeywords(input)

    def getKeywords(self):
        sorted = zip(self.mapping.itervalues(), self.mapping.iterkeys())
        sorted.sort()
        keywords = []
        for (index, encoded), value in sorted:
            if index >= 0:
                if encoded != value:
                    keywords.append(value)
                else:
                    keywords.append('')
        return keywords

    def sub(self, input):
        def repl(m):
            return self.mapping.get(m.group(0), ('', m.group(0)))[1]
        return self.regexp.sub(repl, input)


class JavascriptKeywordMapper(KeywordMapper):
    def __init__(self, regexp=None, encoder=None):
        if regexp is None:
            self.regexp = re.compile(r'\w+')
        elif isinstance(regexp, (str, unicode)):
            self.regexp = re.compile(regexp)
        else:
            self.regexp = regexp
        if encoder is None:
            self.encoder = self._encode
        else:
            self.encoder = encoder
        self.mapping = {}

    def _encode(self, charCode,
                mapping="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        result = []
        quotient = charCode
        while quotient or not len(result):
            quotient, remainder = divmod(quotient, 62)
            result.append(mapping[remainder])
        result.reverse()
        return "".join(result)

    def getDecodeFunction(self, fast=True, name=None):
        jspacker = JavascriptPacker('full')

        # fast boot function
        fast_decoder = r"""
            // does the browser support String.replace where the
            //  replacement value is a function?
            if (!''.replace(/^/, String)) {
                // decode all the values we need
                // we have to add the dollar prefix, because $encoded can be
                // any keyword in the decode function below. For example
                // 'constructor' is an attribute of any object and it would
                // return a false positive match in that case.
                while ($count--) $decode["$"+$encode($count)] = $keywords[$count] || $encode($count);
                // global replacement function
                $keywords = [function($encoded){$result = $decode["$"+$encoded]; return $result!=undefined?$result:$encoded}];
                // generic match
                $encode = function(){return'\\w+'};
                // reset the loop counter -  we are now doing a global replace
                $count = 1;
            };"""

        if name is None:
            # boot function
            decoder = r"""
                function($packed, $ascii, $count, $keywords, $encode, $decode) {
                    $encode = function($charCode) {
                        return ($charCode < $ascii ? "" : $encode(parseInt($charCode / $ascii))) +
                            (($charCode = $charCode % $ascii) > 35 ? String.fromCharCode($charCode + 29) : $charCode.toString(36));
                    };
                    // fastDecodePlaceholder
                    while ($count--)
                        if ($keywords[$count])
                            $packed = $packed.replace(new RegExp("\\b" + $encode($count) + "\\b", "g"), $keywords[$count]);
                    return $packed;
                }"""

            if fast:
                decoder = decoder.replace('// fastDecodePlaceholder', fast_decoder)

            decoder = jspacker.pack(decoder)

        else:
            decoder = r"""
                var %s = function($ascii, $count, $keywords, $encode, $decode) {
                    $encode = function($charCode) {
                        return ($charCode < $ascii ? "" : $encode(parseInt($charCode / $ascii))) +
                            (($charCode = $charCode %% $ascii) > 35 ? String.fromCharCode($charCode + 29) : $charCode.toString(36));
                    };
                    // fastDecodePlaceholder
                    var decoder = function($packed, $ascii1, $count1, $keywords1, $encode1, $decode1) {
                        $count1 = $count;
                        while ($count1--)
                            if ($keywords[$count1])
                                $packed = $packed.replace(new RegExp("\\b" + $encode($count1) + "\\b", "g"), $keywords[$count1]);
                        return $packed;
                    };
                    return decoder;
                }""" % name

            if fast:
                decoder = decoder.replace('// fastDecodePlaceholder', fast_decoder)

            decoder = jspacker.pack(decoder)

            keywords = self.getKeywords()
            decoder = "%s(62, %i, '%s'.split('|'), 0, {});" % (decoder, len(keywords), "|".join(keywords))

        return decoder

    def getDecoder(self, input, keyword_var=None, decode_func=None):
        if keyword_var is None:
            keywords = self.getKeywords()
            num_keywords = len(keywords)
            keywords = "|".join(keywords)
            keywords = "'%s'.split('|')" % keywords
        else:
            keywords = keyword_var
            num_keywords = len(self.getKeywords())

        if decode_func is None:
            decode_func = self.getDecodeFunction()

        escaped_single = input.replace("\\","\\\\").replace("'","\\'").replace('\n','\\n')
        escaped_double = input.replace("\\","\\\\").replace('"','\\"').replace('\n','\\n')
        if len(escaped_single) < len(escaped_double):
            script = "'%s'" % escaped_single
        else:
            script = '"%s"' % escaped_double
        return "eval(%s(%s,62,%i,%s,0,{}))" % (decode_func, script,
                                               num_keywords,
                                               keywords)


class Packer:
    def __init__(self):
        self.patterns = []

    def copy(self):
        result = Packer()
        result.patterns = self.patterns[:]
        return result

    def _repl(self, match):
        # store protected part
        self.replacelist.append(match.group(1))
        # return escaped index
        return "\x00%i" % len(self.replacelist)

    def pack(self, input):
        # list of protected parts
        self.replacelist = []
        # escape the escapechar
        output = input.replace('\x00','\x00\x00')
        for regexp, replacement, keyword_encoder in self.patterns:
            if replacement is None:
                if keyword_encoder is None:
                    # protect the matched parts
                    output = regexp.sub(self._repl, output)
                else:
                    mapper = KeywordMapper(regexp=regexp,
                                           encoder=keyword_encoder)
                    # get keywords
                    mapper.analyse(output)
                    # replace keywords
                    output = mapper.sub(output)
            else:
                # substitute
                output = regexp.sub(replacement, output)
        # restore protected parts
        replacelist = list(enumerate(self.replacelist))
        replacelist.reverse() # from back to front, so 1 doesn't break 10 etc.
        for index, replacement in replacelist:
            # we use lambda in here, so the real string is used and no escaping
            # is done on it
            before = len(output)
            regexp = re.compile('(?<!\x00)\x00%i' % (index+1))
            output = regexp.sub(lambda m:replacement, output)
        # unescape
        output = output.replace('\x00\x00','\x00')
        # done
        return output

    def protect(self, pattern, flags=None):
        self.keywordSub(pattern, None, flags)

    def sub(self, pattern, replacement, flags=None):
        if flags is None:
            self.patterns.append((re.compile(pattern), replacement, None))
        else:
            self.patterns.append((re.compile(pattern, flags), replacement, None))

    def keywordSub(self, pattern, keyword_encoder, flags=None):
        if flags is None:
            self.patterns.append((re.compile(pattern), None, keyword_encoder))
        else:
            self.patterns.append((re.compile(pattern, flags), None, keyword_encoder))


class JavascriptPacker(Packer):
    def __init__(self, level='safe'):
        Packer.__init__(self)
        if level == 'full':
            # encode local variables. those are preceeded by dollar signs
            # the amount of dollar signs says how many characters are preserved
            # any trailing digits are preserved as well
            # $name -> n, $$name -> na, $top1 -> t1, $top2 -> t2
            def _dollar_replacement(match):
                length = len(match.group(2))
                start = length - max(length - len(match.group(3)), 0)
                result = match.group(1)[start:start+length] + match.group(4)
                return result
            self.sub(r"""((\$+)([a-zA-Z\$_]+))(\d*)\b""", _dollar_replacement)
            
            self.keywordSub(r"""\b_[A-Za-z\d]\w*""", lambda i: "_%i" % i)
    
            # protect strings
            # this is more correct, but needs more testing
            # it has to be more accurate because of the more aggresive packing later
            self.protect(r"""(?<=return|..case|.....[=\[|(,?:+])\s*((?P<quote>['"])(?:\\(?P=quote)|\\\n|.)*?(?P=quote))""", re.DOTALL)
        else:
            # protect strings
            # these sometimes catch to much, but in safe mode this doesn't hurt
            self.protect(r"""('(?:\\'|\\\n|.)*?')""")
            self.protect(r'''("(?:\\"|\\\n|.)*?")''')
        # protect regular expressions
        self.protect(r"""\s+(\/[^\/\n\r\*][^\/\n\r]*\/g?i?)""")
        self.protect(r"""([^\w\$\/'"*)\?:]\/[^\/\n\r\*][^\/\n\r]*\/g?i?)""")
        # multiline comments
        self.sub(r'/\*(?!@).*?\*/', '', re.DOTALL)
        # one line comments
        self.sub(r'\s*//.*$', '', re.MULTILINE)
        # strip whitespace at the beginning and end of each line
        self.sub(r'^[ \t\r\f\v]*(.*?)[ \t\r\f\v]*$', r'\1', re.MULTILINE)
        # whitespace after some special chars but not
        # before function declaration
        self.sub(r'([{;\[(,=&|\?:<>%!/])\s+(?!function)', r'\1')
        # after an equal sign a function definition is ok
        self.sub(r'=\s+(?=function)', r'=')
        if level == 'full':
            # whitespace after some more special chars
            self.sub(r'([};\):,])\s+', r'\1')
        # whitespace before some special chars
        self.sub(r'\s+([={},&|\?:\.()<>%!/\]])', r'\1')
        # whitespace before plus chars if no other plus char before it
        self.sub(r'(?<!\+)\s+\+', '+')
        # whitespace after plus chars if no other plus char after it
        self.sub(r'\+\s+(?!\+)', '+')
        # whitespace before minus chars if no other minus char before it
        self.sub(r'(?<!-)\s+-', '-')
        # whitespace after minus chars if no other minus char after it
        self.sub(r'-\s+(?!-)', '-')
        # remove redundant semi-colons
        self.sub(r';+\s*([};])', r'\1')
        # remove any excessive whitespace left except newlines
        self.sub(r'[ \t\r\f\v]+', ' ')
        # excessive newlines
        self.sub(r'\n+', '\n')
        # first newline
        self.sub(r'^\n', '')


class CSSPacker(Packer):
    def __init__(self, level='safe'):
        Packer.__init__(self)
        # protect strings
        # these sometimes catch to much, but in safe mode this doesn't hurt
        self.protect(r"""('(?:\\'|\\\n|.)*?')""")
        self.protect(r'''("(?:\\"|\\\n|.)*?")''')
        # strip whitespace
        self.sub(r'^[ \t\r\f\v]*(.*?)[ \t\r\f\v]*$', r'\1', re.MULTILINE)
        # remove comment contents
        self.sub(r'/\*.*?( ?[\\/*]*\*/)', r'/*\1', re.DOTALL)
        # remove lines with comments only (consisting of stars only)
        self.sub(r'^/\*+\*/$', '', re.MULTILINE)
        # excessive newlines
        self.sub(r'\n+', '\n')
        # first newline
        self.sub(r'^\n', '')

        if level == 'full':
            #remove more whitespace
            self.sub(r'([{,;])\s+', r'\1')


## jspacker = JavascriptPacker('safe')
## jspacker_full = JavascriptPacker('full')

## def run():
    ## script = open('cssQuery.js').read()
    ## script = jspacker_full.pack(script)
    ## open('output.js','w').write(script)
    ## mapper = JavascriptKeywordMapper()
    ## mapper.analyse(script)
    ## keywords = mapper.getKeywords()
    ## script = mapper.sub(script)
    ## f = open('output1.js','w')
    ## #f.write("keywords='%s'.split('|');\n" % "|".join(keywords))
    ## #f.write(mapper.getDecodeFunction(name='__dEcOdE'))
    ## f.write(mapper.getDecoder(script))
    ## for index, keyword in enumerate(keywords):
        ## encoded = mapper._encode(index)
        ## if keyword == '':
            ## replacement = encoded
        ## else:
            ## replacement = keyword
        ## regexp = re.compile(r'\b%s\b' % encoded)
        ## script = regexp.sub(lambda m: replacement, script)
    ## open('output2.js','w').write(script)

## if __name__=='__main__':
    ## run()
