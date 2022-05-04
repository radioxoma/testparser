#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import io
import unittest
from vsmu import main as testparser

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curdir + '/../')
sys.path.insert(0, curdir + '/../vsmu')


class TestEvsmu(unittest.TestCase):
    def setUp(self):
        """Sorting inconsistent if there are equal questions text but
        different answers.
        """
        self.quiz_evsmu = testparser.parse_evsmu(os.path.join(curdir, "evsmu/g495.htm"))
        self.quiz_evsmu.sort(key=lambda q: q.question.lower())

    def test_evsmu_to_mytestx_output(self):
        with io.open(os.path.join(curdir, 'evsmu/g495_mytestx.txt'), encoding='cp1251') as f:
            for a, b in zip(f.read().split(), testparser.to_mytestx(self.quiz_evsmu).split()):
                try:
                    self.assertEqual(a, b)
                except:
                    print(a)
                    print(b)
                    raise

    def test_evsmu_to_anki_output(self):
        with io.open(os.path.join(curdir, 'evsmu/g495_anki.csv'), encoding='utf-8') as f:
            self.assertEqual(f.read(), testparser.to_anki(self.quiz_evsmu))

    def test_evsmu_to_crib_output(self):
        with io.open(os.path.join(curdir, 'evsmu/g495_crib.txt'), encoding='utf-8') as f:
            self.assertEqual(f.read(), testparser.to_crib(self.quiz_evsmu))


class TestDo(unittest.TestCase):
    def setUp(self):
        self.quiz_do = testparser.parse_do(os.path.join(curdir, "do/g100_do_pic.htm"))
        self.quiz_do.sort(key=lambda q: q.question.lower())

    def test_do_to_mytestx(self):
        s1 = set(testparser.parse_mytestx(os.path.join(curdir, "do/g100_do_pic.txt")))
        s2 = set(self.quiz_do)
        self.assertEqual(s1, s2)


class TestMytestx(unittest.TestCase):
    def setUp(self):
        self.quiz_mytestx = testparser.parse_mytestx(os.path.join(curdir, "mytestx/quiz_sorted.txt"))
        self.quiz_mytestx.sort(key=lambda q: q.question.lower())

        # Case with equal questions but different answers
        # Similar questions for shortener test
        self.quiz_mytestx_guileful = list(set(testparser.parse_mytestx(os.path.join(curdir, "mytestx/quiz_guileful.txt"))))
        self.quiz_mytestx_guileful.sort(key=lambda q: q.question.lower())

    def test_mytestx_parser(self):
        mytestx = testparser.parse_mytestx(os.path.join(curdir, "mytestx/quiz_unsorted.txt"))
        self.assertEqual(set(self.quiz_mytestx), set(mytestx))

    def test_mytestx_parser_duplicates(self):
        mytestx = testparser.parse_mytestx(os.path.join(curdir, "mytestx/quiz_unsorted_duplicates.txt"))
        self.assertEqual(set(self.quiz_mytestx), set(mytestx))

        # Assertion make sense only if total questions > 1
        self.assertNotEqual(
            sorted(list(set(self.quiz_mytestx)),
                key=lambda q: q.question.lower()),
            sorted(list(set(mytestx)),
                key=lambda q: q.question.lower(), reverse=True))

    def test_to_mytestx_output(self):
        with io.open(os.path.join(curdir, 'mytestx/quiz_sorted.txt'), encoding='cp1251') as f:
            self.assertEqual(f.read(), testparser.to_mytestx(self.quiz_mytestx))


class TestRaw(unittest.TestCase):
    def setUp(self):
        self.quiz = testparser.parse_raw(os.path.join(curdir, "raw/raw.txt"))

    def test_to_mytestx_output(self):
        with io.open(os.path.join(curdir, 'raw/raw.mytestx.txt'), encoding='cp1251') as f:
            self.assertEqual(f.read(), testparser.to_mytestx(self.quiz))

if __name__ == '__main__':
    unittest.main()
