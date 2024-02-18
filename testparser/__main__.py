#!/usr/bin/env python

__description__ = "Multiple choice test parser, converter, deduplicator"

import argparse
import html
import json
import re
import warnings
import zipfile
from itertools import zip_longest

import lxml.html
from lxml import etree  # Expected to be compatible with xml.etree.ElementTree

import testparser.parsers
from testparser.parsers import Question, clear


def rmsp(s: str) -> str:
    """Replace multiple spaces with one, strip from ends."""
    return re.sub(r"\ +", " ", s.strip())


def rmspall(s: str) -> str:
    r"""Remove all duplicate \s in string, strip from ends."""
    return re.sub(r"\s+", " ", s.strip())


def short(text: list[str], count_stripped: bool = False) -> str:
    """Shorten str for crib.

    >>> short('Something wrong with compatibility regressions.'.split())
    'Som-ng wrong with com-ty reg-s.'
    >>> short('Something wrong with compatibility regressions.'.split(), True)
    'Som4ng wrong with com8ty reg7s.'
    """

    def sh(word):
        wl = len(word)
        if wl > 7:
            if count_stripped:
                return "{}{}{}".format(word[:3], wl - 5, word[-2:])
            else:
                return "{}-{}".format(word[:3], word[-2:])
        else:
            return word

    return " ".join(map(sh, text))


def min_diff(strlist: list[str]) -> list[str]:
    """Return maximum shortened but distinguishable string list.

    Strings must be sorted already.
    >>> min_diff(sorted(
    ...     ['Clinical notes is the same way',
    ...      'Clinical symptoms of lupus',
    ...      'Clinical symptoms of lupus or something sophisticated']))
    ['Cli-al notes is the same way', 'Cli-al sym-ms of lupus', 'Cli-al sym-ms of lupus or']
    """
    questions = list()
    while len(strlist) > 1:
        if strlist[-2] in strlist[-1]:
            prelast = strlist[-2].split()
            last = strlist.pop().split()
            prelast_word_plus = last[: len(prelast) + 1]  # + 1 different word
            questions.append(short(prelast_word_plus))
        else:
            questions.append(short(strlist.pop().split()))
    questions.append(short(strlist.pop().split()))
    return questions[::-1]


def duplicates(tests):
    """Return question duplicates."""
    dup = set()
    seen = set()
    for q in tests:
        if q in seen:
            dup.add(q)
        else:
            seen.add(q)
    return dup


def parse_gift(filename: str) -> list[Question | None]:
    """Parse limited subset of Moodle GIFT format.

    * Each choice on newline
    * Remove integer at the beginning of the question

    https://docs.moodle.org/en/GIFT_format

    180. СУТОЧНАЯ ДОЗА ЛИДОКАИНА НЕ ДОЛЖНА ПРЕВЫШАТЬ:{
    = 2000 мг
    ~ 1500 мг
    ~ 750 мг
    ~ 500 мг
    ~ 250 мг}
    """
    test = re.compile(r"^(\d+\.\s*)(.+?)(\{.+?\})", flags=re.MULTILINE | re.DOTALL)

    # Parser ignores newlines and splits only at =/~
    # Before =/~ must be space or newline (otherwise it split string in the middle)
    # split_choiсes = re.compile(r"[\{\s](\~|\=)(.+?)(?=[\n\~\=\}])", flags=re.MULTILINE | re.DOTALL)

    # Off spec parser - newlines not a part of the Moodle GIFT syntax
    split_choiсes = re.compile(r"(\~|\=)(.+)[\n|\}]")

    Q = None
    questions = list()
    with open(filename) as f:
        for match in re.finditer(test, f.read()):
            if Q is not None:
                questions.append(Q)
            Q = Question(match.group(2).strip())
            for choice in re.finditer(split_choiсes, match.group(3)):
                answer = choice.group(2).strip()
                valid = choice.group(1).strip() == "="
                Q.add_one_answer(answer, valid)
        questions.append(Q)
    return questions


def parse_do(filename: str) -> list[Question | None]:
    """Parse Moodle HTML tests from do.vsmu.by.

    Todo:
    * Добавить +- к вопросам с ниспадающим списком.
    * Скорректировать текст вопросов.

    Question containers
    .//*[@id='content']/div[@class='que multichoice clearfix'] radiobutton, checkbox, input
    .//*[@id='content']/div[@class='que match clearfix'] сопоставление
    .//*[@id='content']/div[@class='que multianswer clearfix'] выбрать из ниспадающего меню
    """
    doc = lxml.html.parse(filename).getroot()
    questions: list[Question | None] = list()

    multichoice = doc.xpath(".//div[@class='que multichoice clearfix']")
    for test in multichoice:
        test_question = " ".join(
            clear(test.xpath("./div[@class='content']/div[@class='qtext']//text()"))
        )
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
            Q.add_image_path(img[0].get("src"))
        # Answers
        choices = test.xpath(
            "./div[@class='content']/div[@class='ablock clearfix']/table[@class='answer']//tr/td/label/text()"
        )
        test_choices = clear(choices)
        correct = test.xpath(
            "./div[@class='content']/div[@class='ablock clearfix']/table[@class='answer']//tr/td/label/img[@class='icon']"
        )
        if len(test_choices) != len(correct):
            warnings.warn(
                f"Number of variants does not match with number of correct answers '{Q}'"
            )
        for C, A in zip_longest(correct, test_choices):
            # `C` is None if correct answer is not provided by page
            if C is not None:
                Q.add_one_answer(A, C.attrib["alt"] == "Верно")
            else:
                Q.add_one_answer(A, False)
        questions.append(Q)

    ###########################################################################
    multianswer = doc.xpath(".//div[@class='que multianswer clearfix']")
    for test in multianswer:
        raise NotImplementedError("No export. Testing needed.")
        # Название теста
        test_question = " {?} ".join(
            clear(
                test.xpath(
                    "./div[@class='content']/div[@class='ablock clearfix']//text()"
                )
            )
        )
        # print('# %s' % test_question.encode('utf-8'))
        Q = Question(test_question)

        # Варианты ответа (несколько label).
        # Этот элемент изначально был написан но закомментирован.
        # Показывает варианта ответа к вопросам с картинками. Были ошибки?
        test_choices = test.xpath(
            "./div[@class='content']/div[@class='ablock clearfix']//label//option//text()"
        )
        for t in test_choices:
            print(t.encode("utf-8"))

        # Правильный ответ (ниспадающее меню)
        answer2 = test.xpath(
            "./div[@class='content']/div[@class='ablock clearfix']//*[@onmouseover]"
        )
        for answ in answer2:
            this = answ.get("onmouseover")
            # print(this.encode('UTF-8'))
            rp = re.compile(r"Правильный ответ: (.+?)<\/div>", re.UNICODE)
            test_correct = re.search(rp, this).group(1)
            print("Правильно: '%s'" % test_correct.encode("UTF-8"))

        # Обоснование ответа
        # theory = '\n'.join(test.xpath("./div[@class='content']/div[@class='generalfeedback']//text()")).strip()
        # print(theory.encode('utf-8'))

        print("")

    ###########################################################################
    match = doc.xpath(".//div[@class='que match clearfix']")
    for test in match:
        raise NotImplementedError("Testing needed")
        # Название теста
        test_question = "".join(
            clear(test.xpath("./div[@class='content']/div[@class='qtext']//text()"))
        )
        print("# %s" % test_question.encode("utf-8"))
        print("*Match не готов (выводим теорию)*")

        # Пункты
        # tvars = test.xpath("./div[@class='content']/div[@class='ablock clearfix']/table[@class='answer']/tr/td/text()")
        # test_vars = clear(tvars)
        # for t in test_vars:
        #     print(t.encode('utf-8'))

        # Не могу найти ответы, так что выведем теорию.

        # Обоснование ответа
        theory = " ".join(
            clear(
                test.xpath(
                    "./div[@class='content']/div[@class='generalfeedback']//text()"
                )
            )
        )
        print(theory.encode("utf-8"))

        print("")

    return questions


def parse_evsmu(filename: str) -> list[Question | None]:
    """Parse Moodle HTML tests from e-vsmu.by."""
    doc = lxml.html.parse(filename).getroot()

    questions: list[Question | None] = list()
    content = doc.xpath(".//div[@class='que multichoice clearfix']")
    for test in content:
        # Question
        qwe = test.xpath('.//div[@class="qtext22"]')
        textQuestion = qwe[0].text_content().strip()
        Q = Question(" ".join(textQuestion.split()))
        # Answers
        correct = test.xpath(
            './/div[@class="ablock clearfix"]/table/tr/td/label/div/img[attribute::class="icon"]'
        )
        answ_divs = test.xpath('.//div[@class="ablock clearfix"]/table/tr/td/label/div')
        answers = [a.text_content().strip()[3:] for a in answ_divs]
        if len(answers) != len(correct):
            warnings.warn(
                f"Number of variants does not match with number of correct answers '{Q}'"
            )
        for C, A in zip_longest(correct, answers):
            # `C` is None if correct answer is not provided by page
            if C is not None:
                Q.add_one_answer(A, C.attrib["alt"] == "Верно")
            else:
                Q.add_one_answer(A, False)
        questions.append(Q)
    # These questions don't contain correct answers, so we skip them
    content = doc.xpath(".//div[@class='que match clearfix']")
    if content:
        print(
            "Warning: {} 'que match clearfix' tests couldn't be parsed.".format(
                len(content)
            )
        )
    return questions


def parse_mytestx(filename: str) -> list[Question | None]:
    """Read text file in MyTestX format.

    Similar, but not compatible with Iren format https://irenproject.ru/konverter_testov_iz_tekstovyx_fajlov

        // Comment
        # Question in one line
        @image_path.jpg
        + Valid
        - Invalid
        Invalid too
        # Next question
    """
    # q = re.compile("(?<=^#).+(?=\s*$)")
    # i = re.compile("^(?<=^@).+(?=\s*$)")
    # v = re.compile("^[+-].+(?=\s*$)")
    questions = list()
    Q = None
    with open(filename) as f:
        for line in f:
            line = line.replace("\t", " ").strip()
            if not line or line.startswith("//"):  # Ignore empty and comments
                continue
            if line.startswith("#"):
                if Q is not None:
                    questions.append(Q)
                Q = Question(line[1:].strip())
            elif line.startswith("@"):
                Q.add_image_path(line[1:].strip())  # type: ignore
            elif line.startswith("+"):
                Q.add_one_answer(line[1:].strip(), True)  # type: ignore
            elif line.startswith("-"):
                Q.add_one_answer(line[1:].strip(), False)  # type: ignore
            else:  # Interpret lines without markup as False choice
                Q.add_one_answer(line, False)  # type: ignore
        questions.append(Q)
    return questions


def parse_rmanpo(filename: str) -> list[Question | None]:
    """Reformat original RMANPO ICU test text 2019-03-12.

    Note that in the case of 'д' answer fifth choice will always be
    set to True, if exists.
    """

    def iterate_stripped(iter):
        for line in iter:
            yield rmsp(line)

    # Матрица ответов (кому это вообще в голову пришло?)
    corr_matrix_bool = {
        "а": [True, True, True],  # 1, 2 и 3
        "б": [True, False, True],  # 1 и 3
        "в": [False, True, False, True],  # 2 и 4
        "г": [False, False, False, True],  # 4
        "д": [True, True, True, True],  # 1,2,3,4 up to 5, see appending below
    }
    # corr_matrix = {
    #     "а": "1, 2, 3",
    #     "б": "1 и 3",
    #     "в": "2 и 4",
    #     "г": "4",
    #     "д": "1,2,3,4,5 или 1,2,3,4",
    # }

    questions: list[Question | None] = list()
    with open(filename) as f:
        istrip = iterate_stripped(f)
        for line in istrip:
            if "@@" in line:  # First question line
                num_answer, postfix = line.split("@@")
                # Postfix contains text 'Задача@' or empty
                cor_letter = num_answer.split("@")[-1].strip().casefold()
                if len(cor_letter) != 1:
                    # questions.append(Question(next(istrip).strip('@')))
                    warnings.warn(
                        f"Unsupported question type: associative question {line}"
                    )
                    continue
                valid = corr_matrix_bool[cor_letter]
                line = next(istrip)  # Goto first question line

                # Parse question
                question = ""
                while not line[0].isdigit():
                    question += line
                    line = next(istrip)
                # В тестах @ после условия
                # В задачах @ перед условием
                Q = Question(question.strip("@ "))

                # Parse choices
                choices = list()
                i = 0
                while line and line[0].isdigit():
                    i += 1
                    if int(line[0]) != i:
                        raise ValueError(
                            f"Wrong choice enumeration in question '{question}'"
                        )
                    choices.append(line[2:].strip())
                    line = next(istrip)

                # As 'д' question can have 4 or 5 choices, corr_matrix_bool
                # contains 4 by default.
                # Appending fifth True for questions with 5 choices here.
                if cor_letter == "д" and len(valid) < 5:
                    valid.append(True)

                if len(choices) < len(valid):
                    warnings.warn("Question has more answers than choices, skipping")
                    continue

                Q.add_multiple_answers(choices, valid)
                questions.append(Q)
    return questions


def parse_raw(filename):
    """Multichoice human-written format.

    Question starts with number with dot.
    Answers must have plus sign for valid and separator '.' or ')'.

    # Comment
    1. Question:
    -1. answer
    2. answer
    +3. etc
    """
    ptn_question = re.compile(r"^(\d+\.\s*)(.*)")
    ptn_answer = re.compile(r"^(.*?(?:\.|\))\s*)(.*)")
    Q = None
    questions = list()
    with open(filename) as f:
        for line in f:
            try:
                if line.isspace() or line.startswith("#"):
                    continue
                elif line[0].isdigit():
                    if Q is not None:
                        questions.append(Q)
                    Q = Question(
                        re.search(ptn_question, line).group(2)
                    )  # typing: ignore
                elif line.startswith("+"):
                    Q.add_one_answer(
                        re.search(ptn_answer, line).group(2), True
                    )  # typing: ignore
                else:
                    Q.add_one_answer(
                        re.search(ptn_answer, line).group(2), False
                    )  # typing: ignore
            except Exception:
                print(f"'{line}'")
                raise

        if Q is not None:
            questions.append(Q)
    return questions


def parse_raw2(filename):
    """Single choice format for specific pdf to plain text case.

    4 При ОРДС в основе нарушения газообмена в легких лежит:
    Г
    А. Снижение ФОЕ
    Б. Рост мертвого пространства
    В. Нарушение элиминации СО2
    Г. Внутрилегочное шунтирование крови
    Д. Нарушение утилизации кислорода в тканях
    """
    # ^(\d+)\ +(.+?)\n(^\D)\n((?:^\D\..+\n)+)(?=\n)  # Stricter regexp for validation in text editor
    # ^(\d+)\.*\ +(.+?)\n((?:^[+-]*\D\..+\n)+)  # Same for +/- choice marks
    pattern = re.compile(r"^(\d+)\ +(.+?)\n(^\D)\n((?:.+\n)+)", flags=re.MULTILINE)
    letters = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

    with open(filename) as f:
        text = f.read()

    questions = list()
    for match in re.finditer(pattern, text):
        Q = Question(match.group(2).strip())
        valid = match.group(3).strip()
        choices = match.group(4).strip().split("\n")
        for letter, choice in zip(letters, choices):
            # Catch missing choices by АБВГДЕ increment at string beginning
            if not letter == choice[0]:
                warnings.warn(
                    f"Invalid АБВГДЕ increment, check newlines '{match.group(0)}'"
                )
            if not choice[1:].startswith(". "):
                warnings.warn(f"Choice not starts with '<letter>. ' '{match.group(0)}'")
            Q.add_one_answer(choice[3:], valid == choice[0])
        if not Q:
            warnings.warn(f"No valid answer for a question '{match.group(0)}'")
        if Q is not None:
            questions.append(Q)
    return questions


def parse_raw3(filename):
    """Test from human-readable Word document with answers at the appndix.

    http://minzdravrd.ru/vrachi

    Convert to plain text:

        libreoffice --headless --convert-to txt *

    002. В 1986 г. наиболее высокие дозы облучения щитовидной железы чаще всего встречались у следующих контингентов
     а) дошкольники
     б) школьники
     в) подростки
     г) взрослое население
     д) ликвидаторы

    001-Б
    002-А
    003-В
    004-А
    """
    pattern_question = re.compile(r"^(\d+)\.\ +(.+?)\n((?:.+\n)+)", flags=re.MULTILINE)
    pattern_valid = re.compile(r"^(\d+)-(\D)", flags=re.MULTILINE)  # A
    letters = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

    with open(filename) as f:
        text = f.read()

    # Iterate in parallel by questions and valid answers
    questions = list()
    for match_question, match_answer in zip(
        re.finditer(pattern_question, text), re.finditer(pattern_valid, text)
    ):
        Q = Question(match_question.group(2).strip())
        assert match_question.group(1) == match_answer.group(1)  # Question number
        valid = match_answer.group(2).casefold()
        choices = match_question.group(3).strip().split("\n")
        for letter, choice in zip(letters, choices):
            choice = choice.strip()
            # Catch missing choices by АБВГДЕ increment at string beginning
            if not letter == choice[0]:
                warnings.warn(
                    f"Invalid АБВГДЕ increment, check newlines '{match_question.group(0)}'"
                )
            if not choice[1:].startswith(") "):
                warnings.warn(
                    f"Choice not begging with '<letter>) ' '{match_question.group(0)}'"
                )
            Q.add_one_answer(choice[3:], valid == choice[0])
        # if not Q:
        #     warnings.warn(f"No valid answer for a question '{match_question.group(0)}'")
        if Q is not None:
            questions.append(Q)
    return questions


def parse_blocks(filename):
    """Text consists of question and choices blocks separated by newline.

    Quiz represented as sequence of multiline blocks (questions and
    choices), separated by newline. First block assumed as a question.

    This has been used for a text layer from an PDF file.
    """

    def resplit(sequence: list[str], delimiter: str = ";") -> list[str]:
        """Join strings and split them again at given delimiter.

        For multiline text block with excessive newlines, but each
        real line ends with semicolon.

        Args:
            sequence: List of strings
            delimiter:

        Returns:
            List of strings, split at delimiter places
        """
        out = list()
        parts = list()
        for string in sequence:
            parts.append(string)
            if string.endswith(delimiter):
                out.append(" ".join(parts)[:-1])
                parts = list()
        return out

    with open(filename) as f:
        text = f.read().splitlines()
    questions = list()
    previous_empty = False
    even = False
    parts = list()
    for line in text:
        current_empty = not line.strip()  # True if empty line
        if not current_empty:
            if previous_empty:  # Start of the new text block
                if even:
                    Q.add_multiple_answers(  # noqa: F821
                        resplit(parts),
                        [
                            False,
                        ],
                    )
                    questions.append(Q)  # noqa: F821
                else:
                    Q = Question(" ".join(parts))
                parts = list()
                even = not even
            parts.append(line)
        previous_empty = current_empty
    Q.add_multiple_answers(
        resplit(parts),
        [
            False,
        ],
    )
    questions.append(Q)
    return questions


def parse_geetest_epub(filename: str) -> list[Question | None]:
    """https://geetest.ru/ parser.

    XML export from website is broken, so parsing epub instead.
    """
    zcontent = zipfile.ZipFile(filename)
    xhtml = zcontent.read("OEBPS/0.html")
    ns = {"": "http://www.w3.org/1999/xhtml"}
    tree = etree.fromstring(xhtml)

    strip_num = re.compile(r"^\d+\.\s*")
    Q = None
    questions = list()
    for p in tree.iterfind(".//body/p", ns):
        if p.attrib:
            if p.attrib["class"] == "question":
                if Q is not None:
                    questions.append(Q)
                Q = Question(re.sub(strip_num, "", p.text))
            elif p.attrib["class"] == "false":
                Q.add_one_answer(p.text[7:], False)  # type: ignore
            elif p.attrib["class"] == "":
                Q.add_one_answer(p.text[7:], True)  # type: ignore
    questions.append(Q)
    return questions


def parse_imsqti_v2p1(filename: str) -> list[Question | None]:
    """Parser for IMS QTI XML tests.

    Support is partial. Tested with imsqti_v2p1, imsqti_v2p2.

    Developed for Mirapolis LMS imsqti_v2p1 https://hr-dzm.mos.ru (тесты "Московский врач")

    c2123 - probably test id
    https://hr-dzm.mos.ru/mirads/lmscontent/c2123/103887-070b1d9b0-7962-4d40-9d3c-599fd7ecd7b6.jpg
        103887 question 'title'
        TQ$1670105 'identifier', monotone increment or test kind name "choiceMultiple"
    https://hr-dzm.mos.ru/mirads/lmscontent/c2123/question_TQ$1670085.xml - first existing
    https://hr-dzm.mos.ru/mirads/lmscontent/c2123/question_TQ$1670134.xml - last

    References:
        IMS QTI test format https://en.wikipedia.org/wiki/QTI
        http://www.imsglobal.org/question/index.html
        pyslet https://gist.github.com/lsloan/1ba7539d097f9c622054c8e83a241297
    """

    def strip(s):
        return s.replace(" ", " ").replace("  ", " ").replace("<!--2-->", "").strip()

    questions: list[Question | None] = list()

    # ElementTree (unlike Element) knows about namespace
    tree = etree.ElementTree(file=filename).getroot()
    if "imsqti_v2p" in tree.tag:  # imsqti_v2p1, imsqti_v2p2
        ns = {"": tree.tag[1:].split("}")[0]}  # Extract exact namespace
    else:
        print(f"Skipping XML '{filename}' due to namespace mismatch")
        return questions

    if tree.find(".//responseDeclaration", ns) is None:
        print(f"Skipping XML '{filename}': test content not found")
        return questions
    valid = [
        k.text
        for k in tree.findall(
            ".//responseDeclaration/correctResponse/value",
            ns,
        )
    ]
    question = html.unescape(tree.find(".//choiceInteraction/prompt", ns).text)
    image_src = tree.find(".//choiceInteraction/img", ns)

    # Both question and variant 'identifier' increase monotonically
    title = strip(lxml.html.fromstring(tree.get("title")).text_content())
    question = strip(lxml.html.fromstring(question).text_content())

    # Q = Question(f"{tree.get('identifier')} {tree.get('title')} {question}")
    if title == question:
        Q = Question(question)
    else:
        Q = Question(f"{title} {question}")
    if image_src is not None:
        Q.add_image_path(image_src.get("src"))

    for choice in tree.iterfind(".//choiceInteraction/simpleChoice", ns):
        # c = f"{choice.get('index')} {choice.get('identifier')} {html.unescape(choice.text.strip())}"
        # c = f"{choice.get('index')} {strip(html.unescape(choice.text))}"
        c = strip(html.unescape(choice.text))
        Q.add_one_answer(c, choice.get("identifier") in valid)
    Q.sort_answers()
    questions.append(Q)
    return questions


def parse_pt_minzdrav_gov_ru(filename: str) -> list[Question | None]:
    """Parse JSON tests from https://pt.minzdrav.gov.ru.

    Демонстрационная версия онлайн аттестации специалистов Министерства здравоохранения РФ
        https://pt.minzdrav.gov.ru/proftest/testing_v2/demo
        curl 'https://pt.minzdrav.gov.ru/api/proftest/me_tests_v2/demo' -X POST --data-raw 'cat_id=641'
        https://pt.minzdrav.gov.ru/storage/help/guide_applicant_demo.pdf

    Facts:
        Service found 2023-04-26. Help PDF denotes 2018 year.
        No info about real world usage of this tests.
        Every attempt returns 30 multichoice tests with answers (JSON).
        Maintained by ПИК «ПрофТест»
    """
    with open(filename) as f:
        test = json.load(f)

    questions: list[Question | None] = list()
    for question in test["data"]["questions"]:
        Q = Question(rmspall(question["description"]))
        for choice in question["answers"]:
            Q.add_one_answer(
                rmspall(choice["description"]), float(choice["fraction"]) > 0
            )
        questions.append(Q)
    return questions


def to_anki(tests: list[Question]) -> str:
    """Export to Anki TSV format (UTF-8, tab delimiter, HTML).

    Most reliable way to generate multichoice quiz flashcards for Anki:
    1. Uses "Basic" flashcard template (no JS, CSS, custom fields)
    2. One flashcard per text line

    https://docs.ankiweb.net/importing.html#importing
    """
    tsv = list()
    for q in tests:
        all_answ = '<div style="text-align:left">'
        cor_answ = '<div style="text-align:left">'
        for n, (v, c) in enumerate(q.answers.items(), 1):
            all_answ += f"{n}. {v}<br>"
            if c:
                # html ol li wasn't used to allow usage of arbitrary
                # answer number in correct answers list.
                cor_answ += f"{n}. {v}<br>"
        all_answ += "</div>"
        cor_answ += "</div>"
        # Anki autodetects separator in first line
        # Newlines must be replaced with <br> tag
        # Don't use trailing tab: it's needed only for tags.
        tsv.append(f"{q.question}<br>{all_answ}\t{cor_answ}\n")
    return "".join(tsv)


def to_crib(tests: list[Question]) -> str:
    """Shorten tests for crib."""
    questions = min_diff([t.question for t in tests])
    result = list()
    for question, test in zip(questions, tests):
        result.append(
            "{}: {}".format(question, ", ".join(min_diff(sorted(test.correct()))))
        )
    return "\n".join(result) + "\n"


def to_gift(tests: list[Question]) -> str:
    """Export to Moodle GIFT test format.

    https://docs.moodle.org/en/GIFT_format
    """

    def escape_gift(s):
        """Escape symbols restricted in GIFT format."""
        escaped = s
        for symbol in r"~=#{}:":
            if symbol in escaped:
                escaped = escaped.replace(symbol, "\\" + symbol)
        return escaped

    result = list()
    for q in tests:
        answers = list()
        if q.image_path:  # Pluging required for image import
            img_html = rf"""<img src="@@PLUGINFILE@@{q.image_path}" />"""
        else:
            img_html = ""
        for v, c in q.answers.items():
            answers.append(f"{'=' if c else '~'}{escape_gift(v)}")
        result.append(
            "{}{}{{\n{}\n}}\n".format(
                escape_gift(q.question), escape_gift(img_html), "\n".join(answers)
            )
        )
    return "\n".join(result)


def load_files(files: list[str]) -> list[Question | None]:
    """Parse all files from a list."""
    tests = list()
    for filename in files:
        if filename.endswith("gift.txt"):
            parse = parse_gift
        elif filename.endswith("evsmu.htm"):
            parse = parse_evsmu
        elif filename.endswith("do.htm"):
            parse = parse_do
        elif filename.endswith("mytestx.txt"):
            parse = parse_mytestx
        elif filename.endswith("rmanpo.txt"):
            parse = parse_rmanpo
        elif filename.endswith("raw.txt"):
            parse = parse_raw
        elif filename.endswith("raw2.txt"):
            parse = parse_raw2
        elif filename.endswith("raw3.txt"):
            parse = parse_raw3
        elif filename.endswith("blocks.txt"):
            parse = parse_blocks
        elif filename.endswith("geetest.epub"):
            parse = parse_geetest_epub
        elif filename.endswith(".xml"):
            parse = parse_imsqti_v2p1
        elif filename.endswith("pt.minzdrav.gov.ru.json"):
            parse = parse_pt_minzdrav_gov_ru
        elif filename.endswith("palms.json"):
            parse = testparser.parsers.parse_palms
        elif filename.endswith("lms_prometey.htm"):
            parse = testparser.parsers.parse_lms_prometey
        else:
            continue
        tests.extend(parse(filename))
    return tests


def solve(answered_list: list[Question], to_solve: list[Question]) -> list[Question]:
    """Search unknown tests in collection of answered."""
    answered_unique = set(filter(None, answered_list))  # Remove unanswered tests
    unsolved_unique = set(to_solve)
    unsolved_count = len([k for k in unsolved_unique if not k])
    print(
        f"Solving: {len(to_solve)}, unique {len(unsolved_unique)}, without answer {unsolved_count}"
    )

    solved = list()
    for unsolved in to_solve:
        if unsolved:  # Keep already solved tests
            solved.append(unsolved)
            continue
        for answered in answered_unique:
            if (
                unsolved.question_generalized == answered.question_generalized
                and unsolved.answers_generalized.keys()
                == answered.answers_generalized.keys()
            ):
                solved.append(answered)
                break
    print(f"{len(solved)}/{unsolved_count} tests found")
    return solved


def main():
    """Define parser, collect questions."""
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="Files to parse. Parser will be chosen by filename extension ('gift.txt', 'evsmu.htm', 'do.htm', 'mytestx.txt', 'rmanpo.txt', 'raw.txt', 'raw2.txt', 'blocks.txt', 'geetest.epub'). Multiple files will be concatenated.",
    )
    parser.add_argument("-u", "--unify", action="store_true", help="Remove duplicates")
    parser.add_argument(
        "-d", "--duplicates", action="store_true", help="Print duplicates"
    )
    parser.add_argument(
        "-p", action="store_true", help="Print parsed tests in STDOUT in MyTestX format"
    )
    parser.add_argument("-s", "--sort", action="store_true", help="Sort tests")
    parser.add_argument(
        "--solve", nargs="+", help="Populate this file with answers from 'input'"
    )
    parser.add_argument(
        "--has-answer", action="store_true", help="Remove questions without answer"
    )
    parser.add_argument(
        "--to-mytestx",
        help="Save human-readable plain text with \\r\\n. Can be imported in http://mytest.klyaksa.net https://irenproject.ru (*mytestx.txt)",
    )
    parser.add_argument(
        "--to-anki",
        help="Save as tab-formatted text file for import in Anki cards https://apps.ankiweb.net/",
    )
    parser.add_argument("--to-crib", help="Save as sorted shortened cheat sheet text.")
    parser.add_argument("--to-gift", help="Export to Moodle GIFT format (*gift.txt).")
    args = parser.parse_args()

    tests = load_files(args.input)
    tests_unique = set(tests)
    dup = duplicates(tests)
    print(
        f"Total parsed: {len(tests)}, unique {len(tests_unique)}, appears multiple times: {len(dup)}"
    )

    if args.duplicates:
        print("\n".join([str(k) for k in dup]))

    if args.solve:
        print("Output will contain only tests, passed to '--solve'")
        tests = solve(tests, load_files(args.solve))

    if args.has_answer:
        tests = [k for k in tests if k]

    if args.unify:  # Must be after parsing and 'solve'
        tests = list(tests_unique)

    if args.sort or args.to_crib:
        tests.sort(key=lambda q: str(q).casefold())

    # Output
    if args.p:
        print("\n".join([str(k) for k in tests]))
    if args.to_mytestx:
        with open(args.to_mytestx, mode="w", encoding="utf-8", newline="\r\n") as f:
            f.write("\n".join([str(k) for k in tests]))
    if args.to_crib:
        with open(args.to_crib, mode="w", encoding="utf-8", newline="\r\n") as f:
            f.write(to_crib(tests))
    if args.to_anki:
        with open(args.to_anki, mode="w", encoding="utf-8") as f:
            f.write(to_anki(tests))
    if args.to_gift:
        with open(args.to_gift, mode="w", encoding="utf-8") as f:
            f.write(to_gift(tests))


if __name__ == "__main__":
    main()
