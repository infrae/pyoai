import unittest
from oaipmh import validation

class ArgumentValidatorTestCase(unittest.TestCase):
    def test_optional(self):
        spec = {
            'foo': 'optional',
            'bar': 'optional'
            }
        self.assertEquals(
            None,
            validation.validate(spec, {'foo': 'Foo', 'bar': 'Bar'}))
        # an extra argument gives an error
        self.assertRaises(
            validation.BadArgumentError,
            validation.validate,
            spec, {'hoi': 'Hoi', 'foo': 'Foo', 'bar': 'Bar'})
        # a missing optional argument is fine
        self.assertEquals(
            None,
            validation.validate(spec, {'foo': 'Foo'}))
        self.assertEquals(
            None,
            validation.validate(spec, {}))

    def test_required(self):
        spec = {
            'foo': 'required',
            'bar': 'optional'}
        self.assertEquals(
            None,
            validation.validate(spec, {'foo': 'Foo', 'bar': 'Bar'}))
        self.assertEquals(
            None,
            validation.validate(spec, {'foo': 'Foo'}))
        self.assertRaises(
            validation.BadArgumentError,
            validation.validate, spec, {'bar': 'Bar'})

    def test_exclusive(self):
        spec = {
            'foo': 'required',
            'bar': 'required',
            'hoi': 'exclusive'}
        self.assertEquals(
            None,
            validation.validate(spec, {'foo': 'Foo', 'bar': 'Bar'}))
        self.assertRaises(
            validation.BadArgumentError,
            validation.validate, spec, {'foo': 'Foo'})
        self.assertRaises(
            validation.BadArgumentError,
            validation.validate, spec, {'bar': 'Bar'})
        # or a single exclusive argument
        self.assertEquals(
            None,
            validation.validate(spec, {'hoi': 'Hoi'}))
        self.assertRaises(
            validation.BadArgumentError,
            validation.validate, spec, {'foo': 'Foo', 'hoi': 'Hoi'})
        
def test_suite():
    return unittest.TestSuite([unittest.makeSuite(ArgumentValidatorTestCase)])

if __name__=='__main__':
    main(defaultTest='test_suite')
