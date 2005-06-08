import unittest
from oaipmh import common

class ArgumentValidatorTestCase(unittest.TestCase):
    def test_optional(self):
        v = common.ArgumentValidator({
            'foo': 'optional',
            'bar': 'optional'})
        self.assertEquals(
            {},
            v.validate({'foo': 'Foo', 'bar': 'Bar'}))
        # an extra argument gives an error
        self.assertRaises(
            common.ArgumentValidationError,
            v.validate, {'hoi': 'Hoi', 'foo': 'Foo', 'bar': 'Bar'})
        # a missing optional argument is fine
        self.assertEquals(
            {},
            v.validate({'foo': 'Foo'}))
        self.assertEquals(
            {},
            v.validate({}))

    def test_required(self):
        v = common.ArgumentValidator({
            'foo': 'required',
            'bar': 'optional'})
        self.assertEquals(
            {},
            v.validate({'foo': 'Foo', 'bar': 'Bar'}))
        self.assertEquals(
            {},
            v.validate({'foo': 'Foo'}))
        self.assertRaises(
            common.ArgumentValidationError,
            v.validate, {'bar': 'Bar'})

    def test_exclusive(self):
        v = common.ArgumentValidator({
            'foo': 'required',
            'bar': 'required',
            'hoi': 'exclusive'})
        self.assertEquals(
            {},
            v.validate({'foo': 'Foo', 'bar': 'Bar'}))
        self.assertRaises(
            common.ArgumentValidationError,
            v.validate, {'foo': 'Foo'})
        self.assertRaises(
            common.ArgumentValidationError,
            v.validate, {'bar': 'Bar'})
        # or a single exclusive argument
        self.assertEquals(
            {},
            v.validate({'hoi': 'Hoi'}))
        self.assertRaises(
            common.ArgumentValidationError,
            v.validate, {'foo': 'Foo', 'hoi': 'Hoi'})

    def test_local(self):
        v = common.ArgumentValidator({
            'foo': 'required',
            'bar': 'local'})
        self.assertEquals(
            {'bar': 'Bar'},
            v.validate({'foo': 'Foo', 'bar': 'Bar'}))
        
def test_suite():
    return unittest.TestSuite([unittest.makeSuite(ArgumentValidatorTestCase)])

if __name__=='__main__':
    main(defaultTest='test_suite')
