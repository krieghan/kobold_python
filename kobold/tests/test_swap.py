import re
import unittest

from kobold import swap

class Host(object):
    def subject(self, arg, kwarg=None):
        return "original subject"

class TestSwap(unittest.TestCase):
    def setUp(self):
        self.safe_swap = swap.SafeSwap()

    def tearDown(self):
        self.safe_swap.rollback()

    def test_swap_and_rollback(self):
        stub = swap.RoutableStub(
                default_route=('value', None))
        self.safe_swap.swap(
                Host,
                'subject',
                stub)
        host = Host()
        self.assertEqual(None, host.subject(arg=1, kwarg=1))
        
        self.safe_swap.rollback()

        self.assertEqual('original subject', host.subject(arg=1, kwarg=1))

    def test_kwarg_routing(self):
        stub = swap.RoutableStub()
        self.safe_swap.swap(
                Host,
                'subject',
                stub)
        stub.add_route(
            condition={'kwarg' : 1},
            stub_type='value',
            stub_value=2)
        stub.add_route(
            condition={'kwarg' : 3},
            stub_type='value',
            stub_value=4)

        host = Host()
        self.assertEqual(2, host.subject(arg=1, kwarg=1))
        self.assertEqual(4, host.subject(arg=1, kwarg=3))

    def test_arg_routing(self):
        stub = swap.RoutableStub()
        self.safe_swap.swap(
                Host,
                'subject',
                stub)
        stub.add_route(
            condition=(1,),
            stub_type='value',
            stub_value=2)
        stub.add_route(
            condition=(3,),
            stub_type='value',
            stub_value=4)

        host = Host()
        self.assertEqual(2, host.subject(1))
        self.assertEqual(4, host.subject(3))

    def test_arg_and_kwarg_routing(self):
        stub = swap.RoutableStub()
        self.safe_swap.swap(
                Host,
                'subject',
                stub)
        stub.add_route(
            condition={'args' : (1,),
                       'kwargs' : {'kwarg' : 1}},
            stub_type='value',
            stub_value=2)
        stub.add_route(
            condition={'args' : (3,),
                       'kwargs' : {'kwarg' : 3}},
            stub_type='value',
            stub_value=4)

        host = Host()
        self.assertEqual(2, host.subject(1, kwarg=1))
        self.assertEqual(4, host.subject(3, kwarg=3))


    def test_kwarg_with_pattern(self):
        stub = swap.RoutableStub()
        self.safe_swap.swap(
                Host,
                'subject',
                stub)
        stub.add_route(
            condition={'kwarg' : re.compile('.*pattern1.*')},
            stub_type='value',
            stub_value=1)

        host = Host()
        self.assertEqual(1, host.subject(arg='_', kwarg='something_with_pattern1'))
        self.assertRaises(
                swap.StubRoutingException,
                host.subject,
                arg='_',
                kwarg='something_without_the_pattern')

    def test_arg_with_pattern(self):
        stub = swap.RoutableStub()
        self.safe_swap.swap(
                Host,
                'subject',
                stub)
        stub.add_route(
            condition=(re.compile('.*pattern1.*'),),
            stub_type='value',
            stub_value=1)

        host = Host()
        self.assertEqual(1, host.subject('something_with_pattern1', kwarg='_'))
        self.assertRaises(
                swap.StubRoutingException,
                host.subject,
                'something_without_the_pattern',
                kwarg='_')
        


