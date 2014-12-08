#!/usr/bin/env python2
# -*- coding: utf-8 -*-

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
        assert(isinstance(variant, unicode) or isinstance(variant, str))
        assert(isinstance(correct, unicode) or isinstance(correct, str))
        self.answers[variant] = correct

    def add_image_path(self, im_path):
        """Add link to image file.

        :param str im_path: Path to image file.
        """
        self.image_path = im_path

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
        info = u'# {}\n'.format(self.question)
        if self.image_path:
            info += u'@ {}\n'.format(self.image_path)
        for v, c in self.answers.items():
            info += u'{} {}\n'.format(c, v)
        return info

    def __str__(self):
        data = self.__unicode__().encode('utf-8')
        # Python3 compatibility
        if isinstance(data, str):
            return data
        else:
            return self.__unicode__()


def clear(strlist):
    """Remove empty strings and spaces from sequence.
    """
    return filter(None, map(lambda x: x.strip(), strlist))


def unify(seq):
    """Remove duplicate tests basing on just question.

    This method is verbose.
    """
    seen = set()
    seen_add = seen.add
    # [x for x in seq if x.question not in seen and not seen_add(x.question)]

    uniq = list()
    for k in seq:
        if k.question not in seen and not seen_add(k.question):
            uniq.append(k)
        else:
            print("Next question was skipped:\n{}".format(k))
    return uniq


def parse_do(filename):
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
        test_question = u' '.join(clear(test.xpath("./div[@class='content']/div[@class='qtext']//text()")))
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
        if not args.na:
            if len(test_choices) != len(correct):
                print(Q)
                raise ValueError(
                    "Number of variants does not match with number of correct answers.\n"
                    "If correct answers is not provided by test page, use `--na` option.")
        for C, A in itertools.izip_longest(correct, test_choices):
            # `C` is None if correct answer is not provided by page
            if C is not None:
                if C.attrib['alt'] == u'Верно':
                    Q.add_one_answer(A, u'+')
                else:
                    Q.add_one_answer(A, u'-')
            else:
                Q.add_one_answer(A, u'-')
        questions.append(Q)

    ###########################################################################
    multianswer = doc.find_class('que multianswer clearfix')
    for test in multianswer:
        raise NotImplementedError("No export. Testing needed.")
        # Название теста
        test_question = u' {?} '.join(clear(test.xpath("./div[@class='content']/div[@class='ablock clearfix']//text()")))
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
            rp = re.compile(u'Правильный ответ: (.+?)<\/div>', re.UNICODE)
            test_correct = re.search(rp, this).group(1)
            print("Правильно: '%s'" % test_correct.encode('UTF-8'))

        # Обоснование ответа
        # theory = u'\n'.join(test.xpath("./div[@class='content']/div[@class='generalfeedback']//text()")).strip()
        # print(theory.encode('utf-8'))

        print(u'')

    ###########################################################################
    match = doc.find_class('que match clearfix')
    for test in match:
        raise NotImplementedError("Testing needed")
        # Название теста
        test_question = u''.join(clear(test.xpath("./div[@class='content']/div[@class='qtext']//text()")))
        print('# %s' % test_question.encode('utf-8'))
        print('*Match не готов (выводим теорию)*')

        # Пункты
        # tvars = test.xpath("./div[@class='content']/div[@class='ablock clearfix']/table[@class='answer']/tr/td/text()")
        # test_vars = clear(tvars)
        # for t in test_vars:
        #     print(t.encode('utf-8'))

        # Не могу найти ответы, так что выведем теорию.

        # Обоснование ответа
        theory = u' '.join(clear(test.xpath("./div[@class='content']/div[@class='generalfeedback']//text()")))
        print(theory.encode('utf-8'))

        print(u'')

    return questions


def parse_evsmu(filename):
    """e-vsmu.by Moodle tests parser.
    """
    doc = lxml.html.parse(filename).getroot()

    questions = list()
    content = doc.find_class('content')
    for test in content:
        ## Question
        qwe = test.xpath('child::div[attribute::class="qtext22"]')
        textQuestion = qwe[0].text_content().strip()
        Q = Question(u' '.join(textQuestion.split()))
        ## Answers
        correct = test.xpath('child::div[attribute::class="ablock clearfix"]/table/tr/td/label/div/img[attribute::class="icon"]')
        answers = clear(test.xpath('child::div[attribute::class="ablock clearfix"]/table/tr/td/label/div/text()'))
        if not args.na:
            if len(answers) != len(correct):
                print(Q)
                raise ValueError(
                    "Number of variants does not match with number of correct answers.\n"
                    "If correct answers is not provided by test page, use `--na` option.")
        for C, A in itertools.izip_longest(correct, answers):
            # `C` is None if correct answer is not provided by page
            if C is not None:
                if C.attrib['alt'] == u'Верно':
                    Q.add_one_answer(A, u'+')
                else:
                    Q.add_one_answer(A, u'-')
            else:
                Q.add_one_answer(A, u'-')
        questions.append(Q)
    return questions


def parse_parsed(doc):
    """Do something with tests in parsed format, e.g. analysis.
    """
    raise NotImplementedError


def to_mytestx(tests):
    """Export to MyTestX format; fine for printing.
    """
    out = u'\n'.join([unicode(k) for k in tests])
    out = out.replace(u'α', u'альфа')
    out = out.replace(u'β', u'бета')
    out = out.replace(u'γ', u'гамма')
    assert isinstance(out, unicode)
    return out


def to_anki(tests):
    """Export to Anki http://ankisrs.net importable format.
    """
    strlst = list()
    for q in tests:
        all_answ = u'<div style="text-align:left">'
        cor_answ = u'<div style="text-align:left">'
        for n, (v, c) in enumerate(q.answers.iteritems(), 1):
            all_answ += u'{}. {}<br>'.format(n, v)
            if c == u'+':
                # html ol li wasn't used to allow usage of arbitrary
                # answer number in correct answers list.
                cor_answ += u'{}. {}<br>'.format(n, v)
        all_answ += u'</div>'
        cor_answ += u'</div>'
        # Don't use trailing tab: it's needed only for tags.
        strlst.append(u"{}<br>{}\t{}\n".format(q.question, all_answ, cor_answ))
    out = u''.join(strlst)
    assert isinstance(out, unicode)
    return out


def main(args):
    """Define parser, collect questions.
    """
    # Choose parser
    if args.target == "evsmu":
        selected_parser = parse_evsmu
    elif args.target == "do":
        selected_parser = parse_do

    # Define test source & parse to Question class instances
    tests = list()
    for filename in args.input:
        if filename.endswith('.htm'):
            tests.extend(selected_parser(filename))

    print("{} questions total".format(len(tests)))

    # Questions filtering
    tests.sort(key=attrgetter('question'))
    if args.unify:
        nofiltered = len(tests)
        tests = unify(tests)
        print('{} / {} uniq tests'.format(len(tests), nofiltered))

    # Output
    if args.p:
        print('\n'.join([str(k) for k in tests]))
    if args.to_mytestx:
        with io.open(args.to_mytestx, mode='w', encoding='cp1251',
            errors='ignore', newline='\r\n') as f:
            f.write(to_mytestx(tests))
    if args.to_anki:
        with io.open(args.to_anki, mode='w', encoding='utf-8',
            errors='ignore') as f:
            f.write(to_anki(tests))
    if args.to_crib:
        print(to_crib(tests))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('target', choices=('evsmu', 'do'), help="Parse e-vsmu.by or do.vsmu.by tests")
    parser.add_argument("input", nargs="+", help="An *.htm file (or files) for parsing. Multiple files will be concatenated.")
    parser.add_argument("--na", action='store_true', help="Do not raise an exception if page doesn't have question answers.")
    parser.add_argument("-u", "--unify", action='store_true', help="Remove tests with equal question texts. Use it with care.")
    parser.add_argument("-p", action='store_true', help="Print parsed tests in STDOUT")
    parser.add_argument("--to-mytestx", help="Save formatted text into *.txt Windows-1251 encoded file. Fine for printing (file is human-readable) or importing in http://mytest.klyaksa.net")
    parser.add_argument("--to-anki", help="Save to tab-formatted text file for import in Anki cards http://ankisrs.net")
    args = parser.parse_args()
    main(args)
