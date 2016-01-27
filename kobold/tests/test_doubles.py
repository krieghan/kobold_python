import re
import unittest

from kobold import doubles

class TestException(Exception):
    pass

def test_function(*args, **kwargs):
    return 'test_function'

class TestRoutableStubFunction(unittest.TestCase):
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

class TestStubFunction(unittest.TestCase):
    def test_raises(self):
        e = TestException()
        stub_function = doubles.StubFunction(raises=e)
        self.assertRaises(
            TestException,
            stub_function)

    def test_calls(self):
        stub_function = doubles.StubFunction(calls=test_function)
        self.assertEquals('test_function', stub_function())

    def test_returns(self):
        stub_function = doubles.StubFunction(returns=1)
        self.assertEquals(1, stub_function())

class TestSpyFunction(unittest.TestCase):
    def test_reset(self):
        spy_function = doubles.SpyFunction(returns=1)
        self.assertEquals(1, spy_function(1))
        self.assertEquals(1, spy_function("apple"))
        self.assertEquals(1, spy_function(keyword="orange"))
        spy_function.reset()

        self.assertEquals([],
                          spy_function.calls)

    def test_spy(self):
        spy_function = doubles.SpyFunction(returns=1)
        self.assertEquals(1, spy_function(1))
        self.assertEquals(1, spy_function("apple"))
        self.assertEquals(1, spy_function(keyword="orange"))

        self.assertEquals([((1,), {}), (("apple",), {}), ((), {'keyword' : 'orange'})],
                          spy_function.calls)


class TestRoutableSpyFunction(unittest.TestCase):
    def test_delegation(self):
        spy_function = doubles.SpyFunction(
                stub_function_factory=doubles.RoutableStubFunction)
        spy_function.add_route(
                condition=(1, 1),
                stub_type='value',
                stub_value=1)
        self.assertEquals(1, spy_function(1, 1))
        self.assertRaises(doubles.StubRoutingException,
                          spy_function,
                          1, 2)
        self.assertEquals([((1, 1), {}), ((1, 2), {})], spy_function.calls)
