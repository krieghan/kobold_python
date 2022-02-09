import unittest

import kobold
from kobold import compare

class TestMultiMatch(unittest.TestCase):
    def test_ordered_basic(self):
        # We can use a MultiMatch to match against multiple
        # elements of a list
        actual = [
            {'color': 'blue',
             'shape': 'square'},
            {'color': 'blue',
             'shape': 'triangle'},
            {'color': 'blue',
             'shape': 'circle'}]
        diff = compare.compare(
            [compare.MultiMatch(
                {'color': 'blue'})],
            actual,
            type_compare={
                'hash': 'existing',
                'ordered': True})
        kobold.assertions.assert_match(
            'match',
            diff)

    def test_ordered_normal_element_and_multi_match(self):
        actual = [
            {'color': 'blue',
             'shape': 'square'},
            {'color': 'blue',
             'shape': 'triangle'},
            {'color': 'blue',
             'shape': 'circle'}]
        # Don't let a MultiMatch prevent a non-MultiMatch element
        # from being matched, simply because it's first in the list
        diff = compare.compare(
            [compare.MultiMatch(
                {'color': 'blue'}),
             {'shape': 'circle'}],
            actual,
            type_compare={
                'hash': 'existing',
                'ordered': True})
        kobold.assertions.assert_match(
            'match',
            diff)

    def test_ordered_two_multimatches(self):
        actual = [
            {'color': 'blue',
             'shape': 'square'},
            {'color': 'blue',
             'shape': 'triangle'},
            {'color': 'blue',
             'shape': 'circle'}]
        # Don't let a MultiMatch consume all the matches from another
        # MultiMatch, simply becuase it's first in the list
        diff = compare.compare(
            [compare.MultiMatch(
                {'color': 'blue'}),
             compare.MultiMatch(
                {'shape': 'circle'})],
            actual,
            type_compare={
                'hash': 'existing',
                'ordered': True})
        kobold.assertions.assert_match(
            'match',
            diff)

    # Unordered
    def test_unordered_basic(self):
        # We can use a MultiMatch to match against multiple
        # elements of a list
        actual = [
            {'color': 'blue',
             'shape': 'square'},
            {'color': 'blue',
             'shape': 'triangle'},
            {'color': 'blue',
             'shape': 'circle'}]
        diff = compare.compare(
            [compare.MultiMatch(
                {'color': 'blue'})],
            actual,
            type_compare={
                'hash': 'existing',
                'ordered': False})
        kobold.assertions.assert_match(
            'match',
            diff)

    def test_unordered_normal_element_and_multi_match(self):
        actual = [
            {'color': 'blue',
             'shape': 'square'},
            {'color': 'blue',
             'shape': 'triangle'},
            {'color': 'blue',
             'shape': 'circle'}]
        # Don't let a MultiMatch prevent a non-MultiMatch element
        # from being matched, simply because it's first in the list
        diff = compare.compare(
            [compare.MultiMatch(
                {'color': 'blue'}),
             {'shape': 'circle'}],
            actual,
            type_compare={
                'hash': 'existing',
                'ordered': False})
        kobold.assertions.assert_match(
            'match',
            diff)

    def test_unordered_two_matches(self):
        actual = [
            {'color': 'blue',
             'shape': 'square'},
            {'color': 'blue',
             'shape': 'triangle'},
            {'color': 'blue',
             'shape': 'circle'}]
        # Don't let a MultiMatch consume all the matches from another
        # MultiMatch, simply becuase it's first in the list
        diff = compare.compare(
            [compare.MultiMatch(
                {'color': 'blue'}),
             compare.MultiMatch(
                {'shape': 'circle'})],
            actual,
            type_compare={
                'hash': 'existing',
                'ordered': False})
        kobold.assertions.assert_match(
            'match',
            diff)
