#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


__description__ = """\
Parser for e-vsmu.by and do.vsmu.by Moodle HTML test pages. Mediafiles like
images are not supported.

    Pereat tristitia,
    Pereant osores.
    Pereat diabolus,
    Quivis antiburschius
    Atque irrisores.
"""

import os
import io
import re
import itertools
import argparse
from collections import OrderedDict
from operator import attrgetter
import lxml.html


class Question(object):
    """An quiz."""

    def __init__(self, question):
        super(Question, self).__init__()
        self.question = question
        self.answers = OrderedDict()
        self.image_path = None

    def add_multiple_answers(self, variants, correct):
        """Add bunch of answer-corect_or_none pairs.

        :param list variants: An test variant
        :param list correct: '+' or '-'
        """
        assert(isinstance(variants, list) and isinstance(correct, list))
        for v, c in zip(variants, correct):
            self.answers[v] = c

    def add_one_answer(self, variant, correct):
        """Add one answer-corect_or_none pair.

        :param unicode variants: An answer
        :param unicode correct: '+' or '-'
        """
        self.answers[variant] = correct

    def add_image_path(self, im_path):
        """Add link to image file.

        :param str im_path: Path to image file.
        """
        self.image_path = im_path

    def correct(self):
        """Return only correct answers.
        """
        correct = list()
        for v, c in self.answers.items():
            if c == '+':
                correct.append(v)
        return correct

    def __unicode__(self):
        """Formatted representation in human-readable format (MyTextX style).

        There are general functions for exporting quiz in specific formats
        named 'to_mytestx', 'to_anki' etc.

        It's convenient for reading too:
            # An Question
            + Right answer
            - False answer
            + Another right answer
            - Another false-marked answer
            *An empty string between tests.*
        """
        info = '# {}\n'.format(self.question)
        if self.image_path:
            info += '@ {}\n'.format(self.image_path)
        for v, c in self.answers.items():
            info += '{} {}\n'.format(c, v)
        return info

    def __str__(self):
        data = self.__unicode__().encode('utf-8')
        # Python3 compatibility
        if isinstance(data, str):
            return data
        else:
            return self.__unicode__()

    def __hash__(self):
        return hash((self.question, self.image_path,
            tuple(sorted(self.answers.items()))))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise AttributeError("Comparison with other object type")
        if not self.question == other.question:
            return False
        if not self.image_path == other.image_path:
            return False
        return dict(self.answers) == dict(other.answers)  # Order-insensitive

    def __ne__(self, other):
        return not self == other


def clear(strlist):
    """Remove empty strings and spaces from sequence.

    >>> clear(['123', '12', '', '2', '1', ''])
    ['123', '12', '2', '1']
    """
    return filter(None, map(lambda x: x.strip(), strlist))


def short(text, count_stripped=False):
    """
    >>> short('Something wrong with compatibility regressions.'.split())
    u'Som-ng wrong with com-ty reg-s.'
    >>> short('Something wrong with compatibility regressions.'.split(), True)
    u'Som4ng wrong with com8ty reg7s.'
    """
    def sh(word):
        l = len(word)
        if l > 7:
            if count_stripped:
                return "{}{}{}".format(word[:3], l - 5, word[-2:])
            else:
                return "{}-{}".format(word[:3], word[-2:])
        else:
            return word
    return " ".join(map(sh, text))


def min_diff(strlist):
    """Return maximum shortened but distinguishable string list.

    Strings must be sorted already.
    >>> min_diff(sorted(
    ...     ['Clinical notes is the same way',
    ...      'Clinical symptoms of lupus',
    ...      'Clinical symptoms of lupus or something sophisticated']))
    [u'Cli-al notes is the same way', u'Cli-al sym-ms of lupus', u'Cli-al sym-ms of lupus or']
    """
    questions = list()
    while len(strlist) > 1:
        if strlist[-2] in strlist[-1]:
            prelast = strlist[-2].split()
            last = strlist.pop().split()
            prelast_word_plus = last[:len(prelast) + 1]  # + 1 different word
            questions.append(short(prelast_word_plus))
        else:
            questions.append(short(strlist.pop().split()))
    questions.append(short(strlist.pop().split()))
    return questions[::-1]


def duplicates(tests):
    """Return question duplicates.
    """
    dup = set()
    seen = set()
    for q in tests:
        if q in seen:
            dup.add(q)
        else:
            seen.add(q)
    return dup


def parse_do(filename, correct_presented=True):
    """do.vsmu.by Moodle tests parser.

    TODO:
    * Добавить +- к вопросам с ниспадающим списком.
    * Скорректировать текст вопросов.

    Question containers
    .//*[@id='content']/div[@class='que multichoice clearfix'] radiobutton, checkbox, input
    .//*[@id='content']/div[@class='que match clearfix'] сопоставление
    .//*[@id='content']/div[@class='que multianswer clearfix'] выбрать из ниспадающего меню
    """
    doc = lxml.html.parse(filename).getroot()
    questions = list()

    multichoice = doc.find_class('que multichoice clearfix')
    for test in multichoice:
        test_question = ' '.join(clear(test.xpath("./div[@class='content']/div[@class='qtext']//text()")))
        Q = Question(test_question)
        img = test.xpath(".//div[@class='content']/div[@class='qtext']//img")
        if img:
            # absolute path to image
            # abs_im_path = os.path.join(
            #     os.path.dirname(os.path.abspath(filename)),
            #     img[0].get('src'))
            # if os.path.exists(abs_im_path) and os.path.isfile(abs_im_path):
            #     Q.add_image_path(abs_im_path.decode('utf-8'))
            # else:
            #     raise ValueError("Image not exists: {}".format(im_path))
            Q.add_image_path(img[0].get('src'))
        ## Answers
        choices = test.xpath("./div[@class='content']/div[@class='ablock clearfix']/table[@class='answer']//tr/td/label/text()")
        test_choices = clear(choices)
        correct = test.xpath("./div[@class='content']/div[@class='ablock clearfix']/table[@class='answer']//tr/td/label/img[@class='icon']")
        if correct_presented:
            if len(test_choices) != len(correct):
                print(unicode(Q))
                raise ValueError(
                    "Number of variants does not match with number of correct answers.\n"
                    "If correct answers are not provided by test page, use `--na` option.")
        for C, A in itertools.izip_longest(correct, test_choices):
            # `C` is None if correct answer is not provided by page
            if C is not None:
                if C.attrib['alt'] == 'Верно':
                    Q.add_one_answer(A, '+')
                else:
                    Q.add_one_answer(A, '-')
            else:
                Q.add_one_answer(A, '-')
        questions.append(Q)

    ###########################################################################
    multianswer = doc.find_class('que multianswer clearfix')
    for test in multianswer:
        raise NotImplementedError("No export. Testing needed.")
        # Название теста
        test_question = ' {?} '.join(clear(test.xpath("./div[@class='content']/div[@class='ablock clearfix']//text()")))
        # print('# %s' % test_question.encode('utf-8'))
        Q = Question(test_question)

        # Варианты ответа (несколько label).
        # Этот элемент изначально был написан но закомментирован.
        # Показывает варианта ответа к вопросам с картинками. Были ошибки?
        test_choices = test.xpath("./div[@class='content']/div[@class='ablock clearfix']//label//option//text()")
        for t in test_choices:
            print(t.encode('utf-8'))

        # Правильный ответ (ниспадающее меню)
        answer2 = test.xpath("./div[@class='content']/div[@class='ablock clearfix']//*[@onmouseover]")
        for answ in answer2:
            this = answ.get('onmouseover')
            # print(this.encode('UTF-8'))
            rp = re.compile('Правильный ответ: (.+?)<\/div>', re.UNICODE)
            test_correct = re.search(rp, this).group(1)
            print("Правильно: '%s'" % test_correct.encode('UTF-8'))

        # Обоснование ответа
        # theory = '\n'.join(test.xpath("./div[@class='content']/div[@class='generalfeedback']//text()")).strip()
        # print(theory.encode('utf-8'))

        print('')

    ###########################################################################
    match = doc.find_class('que match clearfix')
    for test in match:
        raise NotImplementedError("Testing needed")
        # Название теста
        test_question = ''.join(clear(test.xpath("./div[@class='content']/div[@class='qtext']//text()")))
        print('# %s' % test_question.encode('utf-8'))
        print('*Match не готов (выводим теорию)*')

        # Пункты
        # tvars = test.xpath("./div[@class='content']/div[@class='ablock clearfix']/table[@class='answer']/tr/td/text()")
        # test_vars = clear(tvars)
        # for t in test_vars:
        #     print(t.encode('utf-8'))

        # Не могу найти ответы, так что выведем теорию.

        # Обоснование ответа
        theory = ' '.join(clear(test.xpath("./div[@class='content']/div[@class='generalfeedback']//text()")))
        print(theory.encode('utf-8'))

        print('')

    return questions


def parse_evsmu(filename, correct_presented=True):
    """e-vsmu.by Moodle tests parser.
    """
    doc = lxml.html.parse(filename).getroot()

    questions = list()
    content = doc.find_class('content')
    for test in content:
        ## Question
        qwe = test.xpath('child::div[attribute::class="qtext22"]')
        textQuestion = qwe[0].text_content().strip()
        Q = Question(' '.join(textQuestion.split()))
        ## Answers
        correct = test.xpath('child::div[attribute::class="ablock clearfix"]/table/tr/td/label/div/img[attribute::class="icon"]')
        answ_divs = test.xpath('child::div[attribute::class="ablock clearfix"]/table/tr/td/label/div')
        answers = [a.text_content().strip()[3:] for a in answ_divs]
        if correct_presented:
            if len(answers) != len(correct):
                print(unicode(Q))
                raise ValueError(
                    "Number of variants does not match with number of correct answers.\n"
                    "If correct answers is not provided by test page, use `--na` option.")
        for C, A in itertools.izip_longest(correct, answers):
            # `C` is None if correct answer is not provided by page
            if C is not None:
                if C.attrib['alt'] == 'Верно':
                    Q.add_one_answer(A, '+')
                else:
                    Q.add_one_answer(A, '-')
            else:
                Q.add_one_answer(A, '-')
        questions.append(Q)
    return questions


def parse_mytestx(filename):
    """Read text file in MyTestX format.

    Encoding must be cp1251.
    """
    # q = re.compile("(?<=^#).+(?=\s*$)")
    # i = re.compile("^(?<=^@).+(?=\s*$)")
    # v = re.compile("^[+-].+(?=\s*$)")
    questions = list()
    first_question = True
    with io.open(filename, mode='r', encoding='cp1251') as f:
        for line in f:
            if line.startswith("#"):
                if not first_question:
                    questions.append(Q)
                first_question = False
                Q = Question(line[1:].strip())
            elif line.startswith("@"):
                Q.add_image_path(line[1:].strip())
            elif line.startswith("+"):
                Q.add_one_answer(line[1:].strip(), "+")
            elif line.startswith("-"):
                Q.add_one_answer(line[1:].strip(), "-")
        questions.append(Q)
        return questions


def to_mytestx(tests):
    """Export to MyTestX format; fine for printing.
    """
    out = '\n'.join([unicode(k) for k in tests])
    out = out.replace('α', 'альфа')
    out = out.replace('β', 'бета')
    out = out.replace('γ', 'гамма')
    return out


def to_anki(tests):
    """Export to Anki http://ankisrs.net importable format.
    """
    strlst = list()
    for q in tests:
        all_answ = '<div style="text-align:left">'
        cor_answ = '<div style="text-align:left">'
        for n, (v, c) in enumerate(q.answers.items(), 1):
            all_answ += '{}. {}<br>'.format(n, v)
            if c == '+':
                # html ol li wasn't used to allow usage of arbitrary
                # answer number in correct answers list.
                cor_answ += '{}. {}<br>'.format(n, v)
        all_answ += '</div>'
        cor_answ += '</div>'
        # Don't use trailing tab: it's needed only for tags.
        strlst.append("{}<br>{}\t{}\n".format(q.question, all_answ, cor_answ))
    out = ''.join(strlst)
    return out


def to_crib(tests):
    """Shorten tests for crib.
    """
    questions = min_diff(map(attrgetter('question'), tests))
    result = list()
    for question, test in zip(questions, tests):
        result.append(
            "{}: {}".format(
                question,
                ', '.join(min_diff(sorted(test.correct())))))
    return "\n".join(result)


def main(args):
    """Define parser, collect questions.
    """
    # Define test source & parse to Question class instances
    tests = list()
    for filename in args.input:
        if args.target == "evsmu":
            test_part = parse_evsmu(filename, correct_presented=args.na)
        elif args.target == "do":
            test_part = parse_do(filename, correct_presented=args.na)
        elif args.target == "mytestx":
            test_part = parse_mytestx(filename)
        tests.extend(test_part)

    print("{} questions total".format(len(tests)))

    # Questions filtering
    if args.unify:
        nofiltered = len(tests)
        tests = list(set(tests))
        print('{} / {} unique tests'.format(len(tests), nofiltered))
    if args.duplicates:
        dup = duplicates(tests)
        print('{} duplicates'.format(len(dup)))
        print('\n'.join([unicode(k) for k in dup]))

    # Sorting important for crib shortener!
    tests.sort(key=lambda q: str(q).lower())

    # Output
    if args.p:
        print('\n'.join([unicode(k) for k in tests]))
    if args.to_mytestx:
        with io.open(args.to_mytestx, mode='w', encoding='cp1251',
            errors='ignore', newline='\r\n') as f:
            f.write(to_mytestx(tests))
    if args.to_anki:
        with io.open(args.to_anki, mode='w', encoding='utf-8',
            errors='ignore') as f:
            f.write(to_anki(tests))
    if args.to_crib:
        with io.open(args.to_crib, mode='w', encoding='utf-8',
            errors='ignore', newline='\r\n') as f:
            f.write(to_crib(tests))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('target', choices=('evsmu', 'do', 'mytestx'), help="Parse e-vsmu.by or do.vsmu.by tests")
    parser.add_argument("input", nargs="+", help="An *.htm file (or files) for parsing. Multiple files will be concatenated.")
    parser.add_argument("--na", action='store_false', help="Do not raise an exception if page doesn't have question answers.")
    parser.add_argument("-u", "--unify", action='store_true', help="Remove equal tests. Case-sensitive.")
    parser.add_argument("-d", "--duplicates", action='store_true', help="Print duplicates.")
    parser.add_argument("-p", action='store_true', help="Print parsed tests in STDOUT.")
    parser.add_argument("--to-mytestx", help="Save formatted text into *.txt Windows-1251 encoded file. Fine for printing (file is human-readable) or importing in http://mytest.klyaksa.net")
    parser.add_argument("--to-anki", help="Save to tab-formatted text file for import in Anki cards http://ankisrs.net")
    parser.add_argument("--to-crib", help="Save in crib-like text.")
    args = parser.parse_args()
    main(args)
