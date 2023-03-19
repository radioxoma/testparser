# [Multiple choice](https://en.wikipedia.org/wiki/Multiple_choice) test parser, converter, deduplicator

## Installation

    $ pip install https://github.com/radioxoma/vsmu-scripts/archive/refs/heads/master.zip
    $ testparser --help

## Usage

### Acquiring tests

From Moodle: Complete test and save HTML-page to `*.htm` file (for Firefox: *File > Save as..., 'Web-page, HTML only'*). To show all questions and answers press corresponding button or append parameter `&showall=true` to the link, e.g.: `http://e-vsmu.by/mod/quiz/review.php?attempt=111111&showall=true`. You can save multiple pages with overlapping questions and deduplicate them later. If page doesn't contains answers, they all are assumed as false.

### Parsing

Check `testparser --help` for available formats and file extensions. See source code for format examples. As there is no standard test syntax, finding out what format do you have and how to parse it is tricky. Usually it much faster to write your own parser. Program applies specific parser automatically by file extension, so user have to rename input files. Multiple files can be parsed, sorted and deduplicated at one run.

    * `*do.htm` [Moodle](https://ru.wikipedia.org/wiki/Moodle) tests from do.vsmu.by
    * `*evsmu.htm` [Moodle](https://ru.wikipedia.org/wiki/Moodle) tests from e-vsmu.by
    * `*mytestx.txt` human-readable format for russian program called "MyTestX 10.2". windows-1251, '\r' newlines. Now swithed to utf-8.

    testparser *evsmu.htm --to-mytestx mytestx.txt  # Filter evsmu html pages
    testparser testdir/* --to-mytestx mytestx.txt  # Parse all tests in directory

### Export

* `-p` print tests to stdout
* `--to-mytestx` Use parser *TextToMyTestX.exe* from it's website ([example](https://github.com/radioxoma/vsmu-scripts/blob/master/tests/evsmu/g495_mytestx.txt)).
* `--to-anki` Install desktop [Anki](https://en.wikipedia.org/wiki/Anki_(software)) version, *File > Import*. Type Basic. Fields separated by Tab. Import even if existing note has same first field. Check "*Allow HTML in fields*" (HTML required for test alignment to left), [example](https://github.com/radioxoma/vsmu-scripts/blob/master/tests/evsmu/g495_anki.csv). Standard fields "Question" and "Answer" are used.
*  `--to-crib` short text for printing ([example](https://github.com/radioxoma/vsmu-scripts/blob/master/tests/evsmu/g495_crib.txt)).


### Anki

Default preset (20 new, 200 reviews/day, 8 leech threshold) exists for **short cards** you **don't know**. E.g. simplest atomic fact like a single foreign word.
If you learn **bunch of tests** which you **should already know**, you need other preset. Deck preset for a multiple choice tests:

* New cards per day 20 (default)
* Maximum reviews/day 100 (200 by default). Question review takes more time than review of a single word
* Leech threshold 3 (8 by default). Suspend cards you keep on forgetting and don't waste time on them. If you keep forgetting things you already know, probably there is a problem with test itself


## Known issues

* Internal data structure supports only plain text. HTML-tags during import will be skipped, so CO<sub>2</sub> will be shown as CO2
* No image support
* Unescaped chars `<`, `>` breaks parser
* `--to-crib` will have duplicates in case: same question, same right answers, different wrong answers


## Test formats

> tl;dr: for this program use MyTestX as storage/review format, export to Anki when necessary. UTF-8 is encoding by default. Images/media not supported.

There are plenty _similar-but-not-the-same_ formats like Aiken, MyTestX, Iren. Search [Moodle Category:Questions](https://docs.moodle.org/401/en/Category:Questions) for widely accepted formats.

#### Aiken

https://docs.moodle.org/401/en/Aiken_format
https://moodleanswers.com/index.php/quizzes/importing-aiken-formatted-questions

    What colour are strawberries?
    A. green
    B. yellow
    C. black
    D. red
    ANSWER: D

    What does the A stand for in ACU?
    A) Australian
    B) Antarctic
    C) Australasian
    D) Angola
    ANSWER: A


#### MyTestX 10.2 (supported)
Russian shareware. https://mytest.klyaksa.net/wiki/Импорт_тестов_MyTestXPro_из_других_форматов
http://mytest.klyaksa.net

    # An question
    + Right answer
    - False answer
    + Another right answer
    - Another false answer

    # Second question
    + Right answer
    - False answer
    + Another right answer
    - Another false answer

#### Iren

Russian freeware
https://irenproject.ru/konverter_testov_iz_tekstovyx_fajlov
https://irenproject.ru

    #
    В центнерах измеряется:
    + масса
    - площадь
    - объем
    - давление

    #
    К единицам длины относится:
    + метр
    + миля
    + дюйм
    + ярд
    - унция
    - гектар

    #
    Килограмм сокращенно обозначается ***.
    + кг

#### Anki compatible CSV (supported, export only)

#### Moodle import/[export](https://docs.moodle.org/401/en/Export_questions)

    GIFT format (plain text)
        https://en.wikipedia.org/wiki/GIFT_(file_format)
    Moodle XML format

#### Moodle [import](https://docs.moodle.org/401/en/Import_questions)
    Blackboard (*.dat, *.zip) POOL, QTI
    Embedded answers (Cloze)
    Examview
    Missing word format
    WebCT format

#### etc

* IMS Question and Test Interoperability specification (QTI)
    * XML-based format
    * https://en.wikipedia.org/wiki/QTI
    * https://www.imsglobal.org/activity/qtiapip
    * https://pyslet.readthedocs.io/en/latest/imsqtiv2p1.html

* pyslet https://readthedocs.org/projects/pyslet/
* Yaml-based https://github.com/robbert-harms/ybe


## Command line tips

    $ libreoffice --headless --convert-to txt *  # Batch conversion to plaintext
    $ pdftotext in.pdf out.txt  # From package poppler-utils or python-pdftotext
    $ iconv -c -f utf-8 -t windows-1251 > win.txt

If encoding is messed, try visual tool https://2cyr.com/decode/ E.g. source encoding cp1251 displayed as cp1252:

    $ iconv -c -f utf-8 -t cp1252 tests.txt | iconv -c -f cp1251 -t utf-8

### Some sed magic from my wild youth

Strip whitespace:

    ^[\ \t]+(?=\S)  # Trim start
    [\ \t]+$  # Trim end

Search latin letter at the beginning of the string. When choices enumerated by russian letters АБВГД, А В can be replaces with latin A, B.

    ^\s*[A-Za-z]

Replace

    ^\s*\*

Search for redundant newlines due to hyphenation:

    -\n\d  # First check for hyphens before numbers to save them
    -\n

Remove duplicates:

    sort -u file.txt  # Sorted unique
    awk '!x[$0]++' file.txt  # Preserve order


Выделить текстовые блоки с заданным в `{}` числом строк, отделённые друг от друга хотя бы одной пустой строкой `(^.+?\n){7}`.
Удалить двойные переносы строк `^$`.

    $ sed -r -e "s/^[0-9]{1,3}. /#/g" test.txt | sed -r -e "s/^.\+[0-9]. /+ /g" | sed -r -e "s/^.\-[0-9]. /- /g"
    Идеальный код:
    $ sed -r -e "s/^[0-9]{1,3}. /#/g; s/^.\+[0-9]. /+ /g; s/^.\-[0-9]. /- /g" test.txt
    Код, соответствующий нашим реалиям:
    # Удалим лишние пробелы в тексте
    $ sed -r -e "s/ {1,9}/ /g" test.txt
    # Заменим номер вопроса на октоторп
    $ sed -r -e "s/^ *[0-9]{1,3}. /#/g"
    # Оставим только "+" и "-".
    $ sed -r -e "s/^ *\+[0-9] */+ /g"

    # Топографическая анатомия, дерматовенерология (удаляет также и лишние номера вопросов)
    $ cat in.txt | sed -r -e "s/ {1,9}/ /g; s/^ *[0-9]{1,3}.[0-9]*/#/g; s/^ *\+[0-9][. ]*/+ /g; s/^ *\-[0-9][. ]*/- /g; /^\s*$/d; /#/{x;p;x;}" > out.txt

    # Без удаления номеров вопросов
    $ cat in.txt | sed -r -e "s/ {1,9}/ /g; s/^ *[0-9]{1,3}. /#/g; s/^ *\+[0-9][. ]*/+ /g; s/^ *\-[0-9][. ]*/- /g; /^\s*$/d; /#/{x;p;x;}" > out.txt

## TODO

* Группировка тестов по количеству правильных ответов
* В скольки тестах "всё верно" является правильным ответом
* В скольки тестах самый длинный ответ является правильным ответом

*Оценка генеральной совокупности по набору выборок*

* Генеральная совокупность числом K.
* Все элементы разные и их можно сравнивать.
* Можно получить произвольное количество выборок объёмом 100.

Цель: определить размер K генеральной совокупности.
