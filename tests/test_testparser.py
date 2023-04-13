#!/usr/bin/env python

import doctest
import os
import pathlib
import unittest

from testparser import __main__ as main

curdir = os.path.dirname(os.path.abspath(__file__))


class TestEvsmu(unittest.TestCase):
    def setUp(self):
        """Sorting inconsistent if there are equal questions text but
        different answers.
        """
        self.quiz_evsmu = main.parse_evsmu(os.path.join(curdir, "evsmu/g495.htm"))
        self.quiz_evsmu.sort(key=lambda q: q.question.casefold())

    def test_evsmu_to_mytestx_output(self):
        for a, b in zip(
            pathlib.Path(os.path.join(curdir, "evsmu/g495_mytestx.txt"))
            .read_text()
            .split(),
            "\n".join([str(k) for k in self.quiz_evsmu]).split(),
        ):
            try:
                self.assertEqual(a, b)
            except AssertionError:
                print(a)
                print(b)
                raise

    def test_evsmu_to_anki_output(self):
        self.assertEqual(
            main.to_anki(self.quiz_evsmu),
            pathlib.Path(os.path.join(curdir, "evsmu/g495_anki.csv")).read_text(),
        )

    def test_evsmu_to_crib_output(self):
        self.assertEqual(
            main.to_crib(self.quiz_evsmu),
            pathlib.Path(os.path.join(curdir, "evsmu/g495_crib.txt")).read_text(),
        )


class TestDo(unittest.TestCase):
    def setUp(self):
        self.quiz_do = main.parse_do(os.path.join(curdir, "do/g100_do_pic.htm"))
        self.quiz_do.sort(key=lambda q: q.question.casefold())

    def test_do_to_mytestx(self):
        s1 = set(main.parse_mytestx(os.path.join(curdir, "do/g100_do_pic.txt")))
        s2 = set(self.quiz_do)
        self.assertEqual(s1, s2)


class TestMytestx(unittest.TestCase):
    def setUp(self):
        self.quiz_mytestx = main.parse_mytestx(
            os.path.join(curdir, "mytestx/quiz_sorted.txt")
        )
        self.quiz_mytestx.sort(key=lambda q: q.question.casefold())

        # Case with equal questions but different answers
        # Similar questions for shortener test
        self.quiz_mytestx_guileful = list(
            set(main.parse_mytestx(os.path.join(curdir, "mytestx/quiz_guileful.txt")))
        )
        self.quiz_mytestx_guileful.sort(key=lambda q: q.question.casefold())

    def test_mytestx_parser(self):
        mytestx = main.parse_mytestx(os.path.join(curdir, "mytestx/quiz_unsorted.txt"))
        self.assertEqual(set(self.quiz_mytestx), set(mytestx))

    def test_mytestx_parser_duplicates(self):
        mytestx = main.parse_mytestx(
            os.path.join(curdir, "mytestx/quiz_unsorted_duplicates.txt")
        )
        self.assertEqual(set(self.quiz_mytestx), set(mytestx))

        # Assertion make sense only if total questions > 1
        self.assertNotEqual(
            sorted(list(set(self.quiz_mytestx)), key=lambda q: q.question.casefold()),
            sorted(
                list(set(mytestx)), key=lambda q: q.question.casefold(), reverse=True
            ),
        )

    def test_to_mytestx_output(self):
        self.assertEqual(
            "\n".join([str(k) for k in self.quiz_mytestx]),
            pathlib.Path(os.path.join(curdir, "mytestx/quiz_sorted.txt")).read_text(),
        )


class TestRaw(unittest.TestCase):
    def setUp(self):
        self.quiz = main.parse_raw(os.path.join(curdir, "raw/raw.txt"))

    def test_to_mytestx_output(self):
        self.assertEqual(
            "\n".join([str(k) for k in self.quiz]),
            pathlib.Path(os.path.join(curdir, "raw/raw.mytestx.txt")).read_text(),
        )


class TestImsQti(unittest.TestCase):
    def test_imsqti(self):
        self.assertEqual(
            main.parse_mytestx(
                os.path.join(curdir, "imsqti/imsqti_v2p1_question_TQ670105.mytestx.txt")
            ),
            main.parse_imsqti_v2p1(
                os.path.join(curdir, "imsqti/imsqti_v2p1_question_TQ670105.xml")
            ),
        )
        self.assertEqual(
            main.parse_mytestx(
                os.path.join(curdir, "imsqti/imsqti_v2p2_multichoise2.mytestx.txt")
            ),
            main.parse_imsqti_v2p1(
                os.path.join(curdir, "imsqti/imsqti_v2p2_multichoise2.xml")
            ),
        )


class TestGift(unittest.TestCase):
    @unittest.skip("Parser doesn't currently comply spec")
    def test_gift_parser(self):
        self.assertEqual(
            main.parse_gift(os.path.join(curdir, "gift/moodle_gift.txt")),
            main.parse_mytestx(os.path.join(curdir, "gift/moodle_mytestx.txt")),
        )

    def test_gift_export(self):
        tests = main.parse_mytestx(os.path.join(curdir, "gift/moodle_mytestx.txt"))

        self.assertEqual(
            main.to_gift(tests),
            pathlib.Path(os.path.join(curdir, "gift/moodle_gift.txt")).read_text(),
        )


def load_tests(loader: unittest.TestLoader, tests, pattern) -> unittest.TestSuite:
    """Callback to load doctests from modules."""
    tests.addTests(doctest.DocTestSuite(main))
    return tests


if __name__ == "__main__":
    unittest.main()
