import unittest

from Products.ResourceRegistries.utils import applyPrefix

class AbsolutePrefixTest(unittest.TestCase):
    
    def setUp(self):
        self.cssSource = """\
@import url(common.css);

#foo {
    background-image: url ( 'spacer.jpg' );
}

.bar {
    background-image: url('../images/test.jpg' );
}

p {
    background: url("./test.jpg") repeat-x;
}

table {
    background: url("/absolute.jpg") repeat-x;
}

table p {
    background: url("http://example.org/absolute.jpg") repeat-x;
}
"""
    
    def test_simple_prefix(self):
        self.assertEquals("""\
@import url(/prefix/common.css);

#foo {
    background-image: url ( '/prefix/spacer.jpg' );
}

.bar {
    background-image: url('/images/test.jpg' );
}

p {
    background: url("/prefix/test.jpg") repeat-x;
}

table {
    background: url("/absolute.jpg") repeat-x;
}

table p {
    background: url("http://example.org/absolute.jpg") repeat-x;
}
""", applyPrefix(self.cssSource, '/prefix'))

    def test_trailing_slash(self):
        self.assertEquals("""\
@import url(/prefix/common.css);

#foo {
    background-image: url ( '/prefix/spacer.jpg' );
}

.bar {
    background-image: url('/images/test.jpg' );
}

p {
    background: url("/prefix/test.jpg") repeat-x;
}

table {
    background: url("/absolute.jpg") repeat-x;
}

table p {
    background: url("http://example.org/absolute.jpg") repeat-x;
}
""", applyPrefix(self.cssSource, '/prefix/'))

    def test_deep_prefix(self):
        self.assertEquals("""\
@import url(/some/prefix/common.css);

#foo {
    background-image: url ( '/some/prefix/spacer.jpg' );
}

.bar {
    background-image: url('/some/images/test.jpg' );
}

p {
    background: url("/some/prefix/test.jpg") repeat-x;
}

table {
    background: url("/absolute.jpg") repeat-x;
}

table p {
    background: url("http://example.org/absolute.jpg") repeat-x;
}
""", applyPrefix(self.cssSource, '/some/prefix'))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AbsolutePrefixTest))
    return suite
