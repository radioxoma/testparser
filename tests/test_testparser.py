#!/usr/bin/env python

import os
import pathlib
import unittest

from testparser import __main__ as testparser

curdir = os.path.dirname(os.path.abspath(__file__))


class TestEvsmu(unittest.TestCase):
    def setUp(self):
        """Sorting inconsistent if there are equal questions text but
        different answers.
        """
        self.quiz_evsmu = testparser.parse_evsmu(os.path.join(curdir, "evsmu/g495.htm"))
        self.quiz_evsmu.sort(key=lambda q: q.question.casefold())

    def test_evsmu_to_mytestx_output(self):
        with open(os.path.join(curdir, "evsmu/g495_mytestx.txt")) as f:
            for a, b in zip(
                f.read().split(), "\n".join([str(k) for k in self.quiz_evsmu]).split()
            ):
                try:
                    self.assertEqual(a, b)
                except AssertionError:
                    print(a)
                    print(b)
                    raise

    def test_evsmu_to_anki_output(self):
        with open(os.path.join(curdir, "evsmu/g495_anki.csv"), encoding="utf-8") as f:
            self.assertEqual(f.read(), testparser.to_anki(self.quiz_evsmu))

    def test_evsmu_to_crib_output(self):
        with open(os.path.join(curdir, "evsmu/g495_crib.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), testparser.to_crib(self.quiz_evsmu))


class TestDo(unittest.TestCase):
    def setUp(self):
        self.quiz_do = testparser.parse_do(os.path.join(curdir, "do/g100_do_pic.htm"))
        self.quiz_do.sort(key=lambda q: q.question.casefold())

    def test_do_to_mytestx(self):
        s1 = set(testparser.parse_mytestx(os.path.join(curdir, "do/g100_do_pic.txt")))
        s2 = set(self.quiz_do)
        self.assertEqual(s1, s2)


class TestMytestx(unittest.TestCase):
    def setUp(self):
        self.quiz_mytestx = testparser.parse_mytestx(
            os.path.join(curdir, "mytestx/quiz_sorted.txt")
        )
        self.quiz_mytestx.sort(key=lambda q: q.question.casefold())

        # Case with equal questions but different answers
        # Similar questions for shortener test
        self.quiz_mytestx_guileful = list(
            set(
                testparser.parse_mytestx(
                    os.path.join(curdir, "mytestx/quiz_guileful.txt")
                )
            )
        )
        self.quiz_mytestx_guileful.sort(key=lambda q: q.question.casefold())

    def test_mytestx_parser(self):
        mytestx = testparser.parse_mytestx(
            os.path.join(curdir, "mytestx/quiz_unsorted.txt")
        )
        self.assertEqual(set(self.quiz_mytestx), set(mytestx))

    def test_mytestx_parser_duplicates(self):
        mytestx = testparser.parse_mytestx(
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
        with open(os.path.join(curdir, "mytestx/quiz_sorted.txt")) as f:
            self.assertEqual(f.read(), "\n".join([str(k) for k in self.quiz_mytestx]))


class TestRaw(unittest.TestCase):
    def setUp(self):
        self.quiz = testparser.parse_raw(os.path.join(curdir, "raw/raw.txt"))

    def test_to_mytestx_output(self):
        with open(os.path.join(curdir, "raw/raw.mytestx.txt")) as f:
            self.assertEqual(f.read(), "\n".join([str(k) for k in self.quiz]))


class TestImsQti(unittest.TestCase):
    def test_imsqti(self):
        self.assertEqual(
            testparser.parse_mytestx(
                os.path.join(curdir, "imsqti/imsqti_v2p1_question_TQ670105.mytestx.txt")
            ),
            testparser.parse_imsqti_v2p1(
                os.path.join(curdir, "imsqti/imsqti_v2p1_question_TQ670105.xml")
            ),
        )
        self.assertEqual(
            testparser.parse_mytestx(
                os.path.join(curdir, "imsqti/imsqti_v2p2_multichoise2.mytestx.txt")
            ),
            testparser.parse_imsqti_v2p1(
                os.path.join(curdir, "imsqti/imsqti_v2p2_multichoise2.xml")
            ),
        )


class TestGift(unittest.TestCase):
    def test_gift(self):
        tests = testparser.parse_mytestx(
            os.path.join(curdir, "gift/moodle_mytestx.txt")
        )

        self.assertEqual(
            testparser.to_gift(tests),
            pathlib.Path(os.path.join(curdir, "gift/moodle_gift.txt")).read_text(),
        )


if __name__ == "__main__":
    unittest.main()
