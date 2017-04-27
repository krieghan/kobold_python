Comparison
==========

Compare
-------

Code
^^^^

.. autofunction:: kobold.compare.compare
.. autoclass:: kobold.compare.Compare
   :members:
.. autoclass:: kobold.compare.DontCare
.. autoclass:: kobold.compare.NotPresent

class JSONParsingHint(payload)
   If a JSONParsingHint is supplied as the first argument (expected) to 
   the compare function, it means the second argument is JSON-parseable
   text.  Compare will parse that argument into whatever data structure 
   it is, and compare it against the payload argument to the 
   JSONParsingHint constructor

class ObjectDictParsingHint(payload)
   If an ObjectDictParsingHint is supplied as the first argument (expected)
   to the compare function, the payload of this ParsingHint is a dict,
   and the second argument is an object.  Compare the second argument's
   __dict__ to the payload argument

Comparison Process
^^^^^^^^^^^^^^^^^^

Comparison (which occurs in the Compare.compare function)
involves examining two arguments to see if they match.  If they match,
we return the word "match".  If we don't, we return a tuple with two
elements - describing the differences between the two arguments.
An optional "type_compare" argument is accepted which describes
how the comparison is to be performend. The process occurs as follows:

If both arguments are lists and the comparison is ordered,
recursively call compare with each element of the first list
along with its corresponding argument in the second list.
At the end of this process, if both lists consist entirely
of matched elements, return "match".  Otherwise, return
a tuple of two lists.  Each list has underscores for the 
elements that matched, and the mismatched values from each list
for the elements that didn't.

If both arguments are lists and the comparison is unordered,
try recursively comparing each element of the first list
against each element of the second list.  At the end of this
process, if both lists consist entirely of matched elements,
return "match".  Otherwise, return a tuple of lists as above.
 
If both arguments are dictionaries and type_compare is 
full, we get the set of unique keys in both dictionaries.
We iterate over that set, recursively comparing the value 
from the first dictionary to the second dictionary.  If 
all the keys match by value, the dictionaries are considered
matching, and we return "match".  Otherwise, we return a 
diff.  For dictionaries, diffs are represented as a tuple
of two dictionaries - the first with the mismatched values 
from the first argument, the second with the mismatched values
from the second argument.

If both arguments are dictionaries and type_compare is 
existing, we take the keys from the first dictionary.  We
iterate over those keys, recursively, comparing the value
from the first dictionary to the second dictionary.  We never
consider the keys in the second dictionary that aren't
in the first.  The rest of the comparison proceeds as above.

If the first argument (expected) is a DontCare, then we 
check the second argument according to the rules of the 
DontCare.  If the rules are met, we return "match".  If 
they don't, we return a tuple.  The first argument is the
DontCare (represented by the string "dontcare: rule").
The second argument is the thing that didn't match.

If the first argument is a regex pattern (and the 
second argument is a string), we see if the pattern
matches the string.  If it does, we return "match".  
If it does not, we return a tuple.  The first element
of the tuple is a representation of the regex, the second
is the string that it didn't match.

If the first argument is a JSONParsingHint, it has a 
payload associated with it, and the second argument
is expected to be a JSON-parseable string.  We parse
the second argument as JSON and recursively compare it
against the payload of the JSONParsingHint.

If the first argument is an ObjectDictParsingHint, it
has a dict payload associated to it.  We recursively
compare it against the second argument's __dict__.

If none of the above circumstances hold, this is the
base of the recursion.  Do not do a recursive compare - 
compare the two arguments with ==.  If they match, 
return 'match'.  Otherwise, return a tuple of the two
arguments


Examples
^^^^^^^^

Two Hashes
""""""""""
::

  from kobold import compare

  expected = {'a': 1, 'b': 2}
  actual = {'a': 1, 'b': 3}
  compare.compare(
     expected,
     actual)

  # the result is ({'b': 2}, {'b': 3})

As you can see, the diff includes the mismatched keys

Two Hashes in Full Mode
"""""""""""""""""""""""
::

  from kobold import compare

  expected = {'a': 1}
  actual = {'a': 1, 'b': 3, 'c': 4}

  # full is the default
  compare.compare(
     expected,
     actual,
     type_compare='full')

  # the result is 
  # ({'c': <class 'kobold.compare.NotPresent'>, 
  #   'b': <class 'kobold.compare.NotPresent'>}, 
  #  {'c': 4, 
  #   'b': 3}) 

type_compare "full" is the default.  Since the first hash doesn't have
the keys "b" and "c", they're returned as "NotPresent", which is a special
value that we use to distinguish them from being explicitly set to "None"

Two Hashes in Existing Mode
"""""""""""""""""""""""""""
::

  from kobold import compare

  expected = {'a': 1}
  actual = {'a': 1, 'b': 3, 'c': 4}
  compare.compare(
     expected,
     actual,
     type_compare='existing')

  # the result is "match"

Even though actual has other keys, in existing mode we only care
about the keys that are in the "expected" hash.

Two Lists in Ordered Mode
"""""""""""""""""""""""""
::

  from kobold import compare

  expected = [1, 3, 2]
  actual = [2, 3, 1]
  compare.compare(
     expected,
     actual,
     type_compare={'ordered': True})

  # the result is ([1, '_', 2], [2, '_', 1]) 

For lists, ordered comparisons are the default.  Only the second element,
"3", is in the same position in both lists, and so it is represented by the
match character in the diff (_).  

Two Lists in Unordered Mode
"""""""""""""""""""""""""""
::

  from kobold import compare

  expected = [1, 3, 2]
  actual = [2, 3, 1]
  compare.compare(
     expected,
     actual,
     type_compare={'ordered': False})

  # the result is "match"

Since we're comparing two lists that have the same elements in different
orders, and since we're in unordered mode, the lists match

JSONParsingHint
"""""""""""""""
::

  from kobold import compare

  expected = compare.JSONParsingHint({'a': 1})
  actual = '{"a": 1}'
  compare.compare(
     expected,
     actual)

  # the result is "match"

JSONParsingHint tells us that the thing we're comparing is a string
that needs to be parsed from JSON into a data structure, and then
compared against the parsing hint's payload

ObjectDictParsingHint
"""""""""""""""""""""
::

  from kobold import compare

  class ObjectThing(object):
      def __init__(self, kwargs):
          for key, value in kwargs.items():
              setattr(self, key, value)

  expected = compare.ObjectDictParsingHint({'a': 1})
  actual = ObjectThing({'a': 1})
  compare.compare(
     expected,
     actual)

  # the result is "match"

ObjectDictParsingHint tells us that the thing we're comparing is an object.
In order to perform the comparison, compare the object's __dict__ with the
parsing hint's payload


Response
--------

.. autofunction:: kobold.response.response_matches

Assertions
----------

.. autofunction:: kobold.assertions.assert_response_matches
.. autofunction:: kobold.assertions.assert_equal

  




