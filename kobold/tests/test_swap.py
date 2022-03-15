import asyncio
import unittest

from kobold import (
        assertions,
        compare,
        doubles,
        swap)

class Host(object):
    def subject(self, arg, kwarg=None):
        return "original subject"

    async def subject_cr(self, arg, kwarg=None):
        return "original subject"


class TestInstallProxy(unittest.TestCase):
    def setUp(self):
        self.safe_swap = swap.SafeSwap()

    def tearDown(self):
        self.safe_swap.rollback()

    def test_proxy(self):
        self.safe_swap.install_proxy(Host, 'subject')
        host = Host()
        returned = host.subject('some_arg', kwarg='some_kwarg')
        self.assertEqual('original subject', returned)
        self.assertEqual(
            [((host,
              'some_arg'),
              dict(kwarg='some_kwarg'),
              'original subject')],
            [x.as_tuple() for x in host.subject.calls])

    def test_coroutine_proxy(self):
        host = Host()
        proxy = self.safe_swap.install_proxy(
            Host,
            'subject_cr')

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
                host.subject_cr('1'))
        self.assertEqual(
                'original subject',
                result)
        assertions.assert_match(
            [[(compare.DontCare(), '1'), {}, 'original subject']],
            [x.as_tuple() for x in proxy.calls])



class TestSwap(unittest.TestCase):
    def setUp(self):
        self.safe_swap = swap.SafeSwap()

    def tearDown(self):
        self.safe_swap.rollback()

    def test_swap_and_rollback(self):
        stub_function = doubles.StubFunction(returns=1)
        self.safe_swap.swap(
                Host,
                'subject',
                stub_function)
        host = Host()
        self.assertEqual(1, host.subject(1, kwarg=2))
        
        self.safe_swap.rollback()

        self.assertEqual('original subject', host.subject(arg=1, kwarg=1))


    def test_default_original(self):
        routable_stub = doubles.RoutableStubFunction()
        routable_stub.add_route(
            {'kwarg': 1},
            stub_type='value',
            stub_value='new subject')
        self.safe_swap.swap(
            Host,
            'subject',
            routable_stub,
            default_original=True)
        host = Host()
        self.assertEqual(
            'new subject',
            host.subject('some_arg', kwarg=1))
        self.assertEqual(
            'original subject',
            host.subject('some_arg', kwarg=2))

    def test_default_original_coroutine(self):
        loop = asyncio.get_event_loop()
        routable_stub = doubles.RoutableStubCoroutine()
        routable_stub.add_route(
            {'kwarg': 1},
            stub_type='value',
            stub_value='new subject')
        self.safe_swap.swap(
            Host,
            'subject_cr',
            routable_stub,
            default_original=True)
        host = Host()
        self.assertEqual(
            'new subject',
            loop.run_until_complete(
                host.subject_cr('some_arg', kwarg=1)))
        self.assertEqual(
            'original subject',
            loop.run_until_complete(
                host.subject_cr('some_arg', kwarg=2)))



