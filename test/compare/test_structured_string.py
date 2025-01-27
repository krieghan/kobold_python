import base64
import json
import re
import unittest

import kobold


class TestStructuredString(unittest.TestCase):
    def test_payload_match(self):
        expected_token_string = kobold.compare.StructuredString(
            regex=re.compile(r'XBL3.0 x=(.*);(.*)'),
            arguments=[
                'expected_uhs',
                'expected_payload'
            ])
        actual_token_string = 'XBL3.0 x=expected_uhs;expected_payload'
        diff = kobold.compare.compare(
            expected_token_string,
            actual_token_string)
        kobold.assertions.assert_match(
            'match',
            diff)

    def test_payload_mismatch(self):
        expected_token_string = kobold.compare.StructuredString(
            regex=re.compile(r'XBL3.0 x=(.*);(.*)'),
            arguments=[
                'expected_uhs',
                'expected_payload'
            ])
        actual_token_string = 'XBL3.0 x=actual_uhs;actual_payload'
        diff = kobold.compare.compare(
            expected_token_string,
            actual_token_string)
        kobold.assertions.assert_match(
            (['expected_uhs', 'expected_payload'],
             ['actual_uhs', 'actual_payload']),
            diff)


class TestStructuredStringWithBase64Payload(unittest.TestCase):
    def test_full_payload_match(self):
        # When the encoded payloads are a perfect match,
        # of course kobold should identify that as a match
        uhs = 'uhs'
        expected_token_string = kobold.compare.StructuredString(
            regex=re.compile(r'XBL3.0 x=(.*);(.*)'),
            arguments=[
                uhs,
                kobold.compare.hints.Base64Hint(
                    kobold.compare.hints.JSONParsingHint(
                        {'env': 'prod',
                         'account_id': 1}
                    )
                )
            ])

        token_payload = {
            'env': 'prod',
            'account_id': 1}
        encoded_payload = base64.b64encode(
            json.dumps(token_payload).encode()).decode()

        actual_token_string = 'XBL3.0 x={};{}'.format(
            uhs,
            encoded_payload)

        diff = kobold.compare.compare(
            expected_token_string,
            actual_token_string)
        kobold.assertions.assert_match(
            'match',
            diff)


    def test_partial_payload_match(self):
        # When the encoded payloads are not a match,
        # but the payloads themselves match under the 
        # "existing" rule, kobold should identify this as a match
        # (provided the comparison itself is run as "existing")
        uhs = 'uhs'
        expected_token_string = kobold.compare.StructuredString(
            regex=re.compile(r'XBL3.0 x=(.*);(.*)'),
            arguments=[
                uhs,
                kobold.compare.hints.Base64Hint(
                    kobold.compare.hints.JSONParsingHint(
                        {'env': 'prod'}
                    )
                )
            ])

        token_payload = {
            'env': 'prod',
            'account_id': 1}
        encoded_payload = base64.b64encode(
            json.dumps(token_payload).encode()).decode()

        actual_token_string = 'XBL3.0 x={};{}'.format(
            uhs,
            encoded_payload)

        diff = kobold.compare.compare(
            expected_token_string,
            actual_token_string,
            type_compare='existing')
        kobold.assertions.assert_match(
            'match',
            diff)

    def test_wrong_payload_mismatch(self):
        # When the encoded payloads are a mismatch, 
        # and the decoded payloads mismatch on an attribute,
        # kobold should identify that as a mismatch and report
        # the attributes as the diff.

        uhs = 'uhs'
        expected_token_string = kobold.compare.StructuredString(
            regex=re.compile(r'XBL3.0 x=(.*);(.*)'),
            arguments=[
                uhs,
                kobold.compare.hints.Base64Hint(
                    kobold.compare.hints.JSONParsingHint(
                        {'env': 'prod',
                         'account_id': 2}
                    )
                )
            ])

        token_payload = {
            'env': 'prod',
            'account_id': 1}
        encoded_payload = base64.b64encode(
            json.dumps(token_payload).encode()).decode()

        actual_token_string = 'XBL3.0 x={};{}'.format(
            uhs,
            encoded_payload)

        diff = kobold.compare.compare(
            expected_token_string,
            actual_token_string)
        kobold.assertions.assert_match(
            (['_', {'account_id': 2}], ['_', {'account_id': 1}]),
            diff)


