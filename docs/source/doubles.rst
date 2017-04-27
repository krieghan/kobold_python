Test Doubles
============

Doubles
-------

.. autoclass:: kobold.doubles.StubFunction
   :members:
   :member-order: bysource
.. autoclass:: kobold.doubles.SpyFunction
   :members:
   :member-order: bysource
.. autofunction:: kobold.doubles.get_stub_class
.. autoclass:: kobold.doubles.RoutableStubFunction
   :members:
   :member-order: bysource
.. autoclass:: kobold.doubles.StubRoutingException

Swap
----

.. autoclass:: kobold.swap.SafeSwap
   :members:
   :member-order: bysource

Examples
--------

Swapping and Rolling Back
^^^^^^^^^^^^^^^^^^^^^^^^^
::

  from kobold import (
      doubles,
      swap)

  class TestClass(object):
      @classmethod
      def function_a(cls):
          return "a"

  result = TestClass.function_a()
  # result is "a"

  safe_swap = swap.SafeSwap()
  safe_swap.swap(
      TestClass,
      "function_a",
      doubles.StubFunction(returns="b"))

  result = TestClass.function_a()
  # result is "b"

  safe_swap.rollback()

  result = TestClass.function_a()
  # result is "a"

Swapping allows us to replace a function with another function.  In testing,
we swap in "test doubles" to prevent certain functions from being run in the
test in question.

Swapping in a StubFunction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  import unittest

  import requests
  from kobold import (
     doubles,
     swap)

  class TestStubFunction(unittest.TestCase):
      def setUp(self):
          self.safe_swap = swap.SafeSwap()

      def tearDown(self):
          self.safe_swap.rollback()

      def test_replace_request_with_stub(self):
          self.safe_swap.swap(
              requests,
              'request',
              doubles.StubFunction(returns=None)

          response = requests.request(
              'GET',
              'http://api.host.com/endpoint')

          # response is None, as it has been stubbed to be
          self.assertEqual(
              None,
              response)


This demonstrates basic use of swap in a unit test.  The swapper is 
constructed in the setUp and rolled back in the teardown, thus ensuring
that any swaps that occur in the test are isolated (that is, that they
won't affect other tests).  requests.request is a function that requires 
network access, and the ability to route to the target host.  By stubbing
this function, we ensure that nothing requiring network access is ever
called, and that the function simply returns None.  In real life,
you would stub functions that were called in application code, rather than
in the test case itself.

Swapping in a SpyFunction
^^^^^^^^^^^^^^^^^^^^^^^^^
::

  import unittest

  import requests
  from kobold import (
     doubles,
     swap)

  class TestSpyFunction(unittest.TestCase):
      def setUp(self):
          self.safe_swap = swap.SafeSwap()

      def tearDown(self):
          self.safe_swap.rollback()

      def test_replace_request_with_spy(self):
          self.safe_swap.swap(
              requests,
              'request',
              doubles.SpyFunction(returns=None))

          response = requests.request(
              'GET',
              'http://api.host.com/endpoint')

          # response is None, as it has been stubbed to be
          self.assertEqual(
              None,
              response)

          # A spy remembers each time it's called
          self.assertEqual(
              [(('GET', 'http://api.host.com/endpoint'), {})],
              requests.request.calls)

If you want to make assertions about how requests.request is called,
you can replace it with a SpyFunction.  A SpyFunction is basically a stub
that remembers its arguments each time it is called.  In real life,
the call to requests.request would happen in the application code rather
than in the test case itself.

Using a RoutableStubFunction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  import unittest

  import requests
  from kobold import (
     doubles,
     swap)

  # Let's pretend that our project has a module that contains
  # all sorts of functions that create good default HTTP Responses.
  # The implementation of such functions is out of scope for this
  # demonstration

  from myproject.test.factories import (
    response as response_factories)

  class TestRoutableStubFunction(unittest.TestCase):
      def setUp(self):
          self.safe_swap = swap.SafeSwap()

      def tearDown(self):
          self.safe_swap.rollback()

      def test_replace_request_with_routable_stub(self):
          request_stub = doubles.RoutableStubFunction()

          # If requests is called with the URL for the 
          # "users" endpoint, return a user response
          # (whatever that is)
          stub_user_response = factories.make_user_response()
          request_stub.add_route(
              condition={
                'args': (
                    'GET',
                    re.compile('.*/users')),
                'kwargs': {}},
              stub_type='value',
              stub_value=stub_user_response)

          # If requests is called with the URL for the 
          # "projects" endpoint, return a projects response
          # (again, whatever that actually means)
          stub_project_response = factories.make_project_response()
          request_stub.add_route(
              condition={
                'args': (
                    'GET',
                    re.compile('.*/projects')),
                'kwargs': {}},
              stub_type='value',
              stub_value=stub_project_response)

          self.safe_swap.swap(
              requests,
              'request',
              request_stub)

          user_response = requests.request(
              'GET',
              'http://api.host.com/users')

          project_response = requests.request(
              'GET',
              'http://api.host.com/projects')

          # The RoutableStubFunction returns the appropriate
          # value based on the arguments for each call
          self.assertEqual(
              stub_user_response,
              user_response)
          self.assertEqual(
              stub_project_response,
              project_response)

As before, the calls to the stub function would normally be made in the
software under test.  They're made in the test case here for clarity.  
A common issue in testing is that a function for making HTTP requests
(such as requests.request) might be called multiple times in a single 
test, with different URLs, and with the expectation that a different result 
will be returned based on which URL is called.  RoutableStubFunction
allows us to set up different responses for different calls.

Configuring SpyFunction to be a "RoutableSpyFunction"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  import unittest

  import requests
  from kobold import (
     doubles,
     swap)

  from myproject.test.factories import (
    response as response_factories)

  class TestRoutableStubFunction(unittest.TestCase):
      def setUp(self):
          self.safe_swap = swap.SafeSwap()

      def tearDown(self):
          self.safe_swap.rollback()

      def test_replace_request_with_routable_spy(self):
          request_spy = doubles.SpyFunction(
             stub_function_factory=doubles.RoutableStubFunction)

          stub_user_response = factories.make_user_response()
          request_spy.add_route(
              condition={
                'args': (
                    'GET',
                    re.compile('.*/users')),
                'kwargs': {}},
              stub_type='value',
              stub_value=stub_user_response)

          self.safe_swap.swap(
              requests,
              'request',
              request_stub)

          user_response = requests.request(
              'GET',
              'http://api.host.com/users')

          self.assertEqual(
              [(('GET', re.compile('.*/users')), {})],
              request_spy.calls)

SpyFunction uses its stub function to determine what to return.  By default, 
its stub function is a StubFunction.  We can override that by providing the 
RoutableStubFunction constructor as the stub function factory that SpyFunction 
uses to construct an instance of its stub function

The spy has a stub_function instance that we could use to access add_route.  
However, SpyFunction also automatically delegates any access for an attribute
that it does not possess to its stub_function.  Consequently, we can call 
add_route (and any other method that the stub_function has) on the spy directly

In this way, we are able to combine the functionality of the RoutableStub
and the Spy.


Installing a Proxy
^^^^^^^^^^^^^^^^^^
::

  import unittest

  import requests
  from kobold import (
     doubles,
     swap)

  class TestProxy(unittest.TestCase):
      def setUp(self):
          self.safe_swap = swap.SafeSwap()

      def tearDown(self):
          self.safe_swap.rollback()

      def test_install_proxy_on_request(self):
          self.safe_swap.install_proxy(
              requests,
              'request')
              
          response = requests.request(
              'GET',
              'http://api.host.com/endpoint')

          # requests.request is actually called by the proxy.  
          # Response is what it returned

          # requests.request can be used as a spy
          self.assertEqual(
              [(('GET', 'http://api.host.com/endpoint'), {})],
              requests.request.calls)

If we want to inject a spy onto a function without it being stubbed
(ie. the original function still gets called), we can use install_proxy.

Stub Class
^^^^^^^^^^
::

  import unittest

  import requests
  from kobold import (
     doubles,
     swap)

  class TestStubClass(unittest.TestCase):
      def setUp(self):
          self.safe_swap = swap.SafeSwap()

      def tearDown(self):
          self.safe_swap.rollback()

      def test_install_proxy_on_request(self):
          stub_class = doubles.get_stub_class({
              'method_a': 'a',
              'method_b': 'b'})
          stub_instance = stub_class()
          result = stub_instance.method_a()

          # result is 'a'

          result = stub_instance.method_b()

          # result is 'b'

          # method_a and method_b are both spies.  Each, of course,
          # now has a record of exactly one call.

Sometimes, the best hope we have of injecting a spy is to make some factory
function return what we want it to, with any methods replaced with spies.  
The get_stub_class method can easily return a stub_class with the specified
spy methods returning the specified return values.

For instance, smtplib has a class SMTP - instances of which can be used to
send email.  Actually sending emails in a test is probably a bad idea.
There are three methods on SMTP that we need - starttls, login and sendmail.
We probably want to set up spies on all of these so that we can verify that
they're called.  We could replace all three with spies, or we could
replace SMTP itself with a class that we create with get_stub_class.  The 
latter is particularly useful if SMTP's constructor is particularly involved
or problematic (for instance, if it tried to make a connection).


  




    






          

 
