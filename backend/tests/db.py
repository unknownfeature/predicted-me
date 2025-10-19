import unittest

from backend.lib.db import normalize_identifier


class Test(unittest.TestCase):

    def test_normalize_identifier(self):
            assert normalize_identifier("A Normal Title") ==  "a_normal_title"

            assert normalize_identifier("Some METRIC wITh MiXeD CaSe") ==  "some_metric_with_mixed_case"

            assert normalize_identifier("A String with % & * # !") ==  "a_string_with"

            assert normalize_identifier("  trim these spaces  ") ==  "trim_these_spaces"

            assert normalize_identifier("Too   many --- spaces --- here") ==  "too_many_spaces_here"

            assert normalize_identifier("Test for version 2.0") ==  "test_for_version_2_0"

            assert normalize_identifier("Café Müller & Niño") ==  "cafe_muller_nino"
            with self.assertRaises(Exception):
                normalize_identifier("!@#$%^&*()")

            assert normalize_identifier("Don't stop the test!") ==  "don_t_stop_the_test"

            assert normalize_identifier("Final Test (Round 1) - GO!") ==  "final_test_round_1_go"

