import asyncio
import re
import unittest

from kobold import (
        assertions,
        compare,
        doubles,
        swap)

class TestException(Exception):
    pass

def test_function(*args, **kwargs):
    return 'test_function'

class Host(object):
    def __init__(self, *args, **kwargs):
        for (name, value) in kwargs.items():
            setattr(self, name, value)

    def test(self, *args, **kwargs):
        return 'original'


class TestRoutableStubFunction(unittest.TestCase):
    def setUp(self):
        self.safe_swap = swap.SafeSwap()

    def tearDown(self):
        self.safe_swap.rollback()

    def test_kwarg_routing(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition={'kwarg' : 1},
            stub_type='value',
            stub_value=2)
        stub_function.add_route(
            condition={'kwarg' : 3},
            stub_type='value',
            stub_value=4)

        self.assertEqual(2, stub_function(arg=1, kwarg=1))
        self.assertEqual(4, stub_function(arg=1, kwarg=3))

    def test_arg_routing(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=(1,),
            stub_type='value',
            stub_value=2)
        stub_function.add_route(
            condition=(3,),
            stub_type='value',
            stub_value=4)

        self.assertEqual(2, stub_function(1))
        self.assertEqual(4, stub_function(3))

    def test_self_routing(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition={
                'self': {'a': 1}},
            stub_type='value',
            stub_value=1)
        stub_function.add_route(
            condition={
                'self': {'a': 2}},
            stub_type='value',
            stub_value=2)
        self.safe_swap.swap(
            Host,
            'test',
            stub_function,
            default_original=True)

        host1 = Host(a=1)
        host2 = Host(a=2)
        self.assertEqual(
                1,
                host1.test())
        self.assertEqual(
                2,
                host2.test())

    def test_arg_and_kwarg_routing(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition={'args' : (1,),
                       'kwargs' : {'kwarg' : 1}},
            stub_type='value',
            stub_value=2)
        stub_function.add_route(
            condition={'args' : (3,),
                       'kwargs' : {'kwarg' : 3}},
            stub_type='value',
            stub_value=4)

        self.assertEqual(2, stub_function(1, kwarg=1))
        self.assertEqual(4, stub_function(3, kwarg=3))

    def test_kwarg_with_pattern(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition={'kwarg' : re.compile('.*pattern1.*')},
            stub_type='value',
            stub_value=1)

        self.assertEqual(1, stub_function('_', kwarg='something_with_pattern1'))
        self.assertRaises(
                doubles.StubRoutingException,
                stub_function,
                arg='_',
                kwarg='something_without_the_pattern')

    def test_arg_with_pattern(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=(re.compile('.*pattern1.*'),),
            stub_type='value',
            stub_value=1)

        self.assertEqual(1, stub_function('something_with_pattern1', kwarg='_'))
        self.assertRaises(
            doubles.StubRoutingException,
            stub_function,
            'something_without_the_pattern',
            kwarg='_')

    def test_arg_is_dict(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=({'a': 1},),
            stub_type='value',
            stub_value=1)

        self.assertEqual(1, stub_function({'a': 1}))

    def test_rotate(self):
        stub_function = doubles.RoutableStubFunction()
        route = doubles.RotatingRoute(
                    condition=('a',),
                    routes=[
                     ('value', 1),
                     ('value', 2)])
                     
        stub_function.add_route(route=route)

        self.assertEqual(1, stub_function('a'))
        self.assertEqual(2, stub_function('a'))

class TestMixedRoutable(unittest.TestCase):
    def setUp(self):
        self.safe_swap = swap.SafeSwap()

    def tearDown(self):
        self.safe_swap.rollback()

    def test_args_match(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4},
                arg_names=('a', 'b', 'c', 'd')),
            stub_type='value',
            stub_value=1)
        self.assertEqual(1, stub_function(
            1,
            2,
            3,
            4))

    def test_missing_arg(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4},
                arg_names=('a', 'b', 'c', 'd')),
            stub_type='value',
            stub_value=1)
        with self.assertRaises(doubles.StubRoutingException):
            self.assertEqual(1, stub_function(
                1,
                2,
                4))

    def test_kwargs_match(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4},
                arg_names=('a', 'b', 'c', 'd')),
            stub_type='value',
            stub_value=1)
        self.assertEqual(1, stub_function(
            a=1,
            b=2,
            c=3,
            d=4))

    def test_missing_kwarg(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4},
                arg_names=('a', 'b', 'c', 'd')),
            stub_type='value',
            stub_value=1)
        with self.assertRaises(doubles.StubRoutingException):
            stub_function(
                a=1,
                c=3,
                d=4)

    def test_mixed_match(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4},
                arg_names=('a', 'b', 'c', 'd')),
            stub_type='value',
            stub_value=1)
        self.assertEqual(1, stub_function(
            1,
            2,
            c=3,
            d=4))

    def test_mixed_mismatch(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4},
                arg_names=('a', 'b', 'c', 'd')),
            stub_type='value',
            stub_value=1)
        with self.assertRaises(doubles.StubRoutingException):
            stub_function(
                1,
                7,
                c=3,
                d=4)

    def test_exclusive_arg_match(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4},
                exclusive_args={'e': 5},
                arg_names=('a', 'b', 'c', 'd', 'e')),
            stub_type='value',
            stub_value=1)
        self.assertEqual(1, stub_function(
            1,
            2,
            5,
            c=3,
            d=4))

    def test_exclusive_arg_mismatch(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4},
                exclusive_args={'e': 5},
                arg_names=('a', 'b', 'c', 'd', 'e')),
            stub_type='value',
            stub_value=1)
        with self.assertRaises(doubles.StubRoutingException):
            stub_function(
                1,
                2,
                7,
                c=3,
                d=4)

    def test_exclusive_arg_a_kwarg(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4},
                exclusive_args={'e': 5},
                arg_names=('a', 'b', 'c', 'd', 'e')),
            stub_type='value',
            stub_value=1)
        with self.assertRaises(doubles.StubRoutingException):
            stub_function(
                1,
                2,
                c=3,
                d=4,
                e=5)

    def test_exclusive_kwarg_match(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4,
                    'e': 5},
                arg_names=('a', 'b', 'c', 'd')),
            stub_type='value',
            stub_value=1)
        self.assertEqual(1, stub_function(
            1,
            2,
            c=3,
            d=4,
            e=5))

    def test_exclusive_kwarg_mismatch(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4,
                    'e': 5},
                arg_names=('a', 'b', 'c', 'd')),
            stub_type='value',
            stub_value=1)
        with self.assertRaises(doubles.StubRoutingException):
            stub_function(
                1,
                2,
                c=3,
                d=4,
                e=7)

    def test_exclusive_kwarg_an_arg(self):
        stub_function = doubles.RoutableStubFunction()
        stub_function.add_route(
            condition=doubles.Condition(
                kwargs={
                    'a': 1,
                    'b': 2,
                    'c': 3,
                    'd': 4,
                    'e': 5},
                arg_names=('a', 'b', 'c', 'd')),
            stub_type='value',
            stub_value=1)
        with self.assertRaises(doubles.StubRoutingException):
            stub_function(
                1,
                2,
                5,
                c=3,
                d=4)


class TestStubFunction(unittest.TestCase):
    def test_raises(self):
        e = TestException()
        stub_function = doubles.StubFunction(raises=e)
        self.assertRaises(
            TestException,
            stub_function)

    def test_calls(self):
        stub_function = doubles.StubFunction(calls=test_function)
        self.assertEqual('test_function', stub_function())

    def test_returns(self):
        stub_function = doubles.StubFunction(returns=1)
        self.assertEqual(1, stub_function())

class TestSpyFunction(unittest.TestCase):
    def test_reset(self):
        spy_function = doubles.SpyFunction(returns=1)
        self.assertEqual(1, spy_function(1))
        self.assertEqual(1, spy_function("apple"))
        self.assertEqual(1, spy_function(keyword="orange"))
        spy_function.reset()

        self.assertEqual([],
                          spy_function.calls)

    def test_spy(self):
        spy_function = doubles.SpyFunction(returns=1)
        self.assertEqual(1, spy_function(1))
        self.assertEqual(1, spy_function("apple"))
        self.assertEqual(1, spy_function(keyword="orange"))

        self.assertEqual(
            [((1,), {}, 1),
             (("apple",), {}, 1),
             ((), {'keyword' : 'orange'}, 1)],
            [x.as_tuple() for x in spy_function.calls])

class TestSpyCall(unittest.TestCase):
    def test_input(self):
        spy_function = doubles.SpyFunction(returns=1)
        spy_function('arg1', kwarg1='kwarg1_value')
        assertions.assert_match(
            (('arg1',), {'kwarg1': 'kwarg1_value'}),
            spy_function.calls[0].input())

    def test_as_tuple_return(self):
        spy_function = doubles.SpyFunction(returns=1)
        spy_function('arg1', kwarg1='kwarg1_value')
        assertions.assert_match(
            (('arg1',), {'kwarg1': 'kwarg1_value'}, 1),
            spy_function.calls[0].as_tuple())

    def test_as_tuple_raise(self):
        exception = LookupError()
        spy_function = doubles.SpyFunction(raises=exception)
        with self.assertRaises(LookupError):
            spy_function('arg1', kwarg1='kwarg1_value')
        assertions.assert_match(
            (('arg1',),
             {'kwarg1': 'kwarg1_value'},
             compare.NotPresent,
             exception),
            spy_function.calls[0].as_tuple())

    def test_as_dict_return(self):
        spy_function = doubles.SpyFunction(returns=1)
        spy_function('arg1', kwarg1='kwarg1_value')
        assertions.assert_match(
            {'args': ('arg1',),
             'kwargs': {'kwarg1': 'kwarg1_value'},
             'returned': 1,
             'raised': compare.NotPresent,
             'from_coroutine': False},
            spy_function.calls[0].as_dict())

    def test_as_dict_raise(self):
        exception = LookupError()
        spy_function = doubles.SpyFunction(raises=exception)
        with self.assertRaises(LookupError):
            spy_function('arg1', kwarg1='kwarg1_value')
        assertions.assert_match(
            {'args': ('arg1',),
             'kwargs': {'kwarg1': 'kwarg1_value'},
             'returned': compare.NotPresent,
             'raised': exception,
             'from_coroutine': False},
            spy_function.calls[0].as_dict())

    def test_as_dict_coroutine(self):
        spy_function = doubles.SpyFunction(returns=1, awaitable=True)
        asyncio.get_event_loop().run_until_complete(
            spy_function('arg1', kwarg1='kwarg1_value'))
        assertions.assert_match(
            {'args': ('arg1',),
             'kwargs': {'kwarg1': 'kwarg1_value'},
             'returned': 1,
             'raised': compare.NotPresent,
             'from_coroutine': True},
            spy_function.calls[0].as_dict())


class TestRoutableSpyFunction(unittest.TestCase):
    def test_delegation(self):
        spy_function = doubles.SpyFunction(
                stub_function_factory=doubles.RoutableStubFunction)
        spy_function.add_route(
                condition=(1, 1),
                stub_type='value',
                stub_value=1)
        self.assertEqual(1, spy_function(1, 1))
        self.assertRaises(doubles.StubRoutingException,
                          spy_function,
                          1,
                          2)
        assertions.assert_match(
            [((1, 1), 
              {},
              1),
             ((1, 2), 
              {},
              compare.NotPresent,
              compare.DontCare(
                  rule='isinstance',
                  of_class=doubles.StubRoutingException))],
            [x.as_tuple() for x in spy_function.calls])
