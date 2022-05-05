EN: Moodle testpage parser and formatter. These things are for local use, but some pieces of code can be useful for broader masses (e.g. simple quiz test export to [Anki](http://ankisrs.net)).

RU: Парсер для тестов [Moodle](https://ru.wikipedia.org/wiki/Moodle). Ориентирован на студентов ВГМУ и позволяет извлекать тесты и ответы на них из HTML-страниц сайтов e-vsmu.by и do.vsmu.by. Приятные возможности:

* тесты можно вывести в человекочитаемом формате для печати, в том числе в сокращённом виде для шпаргалки.
* тесты можно импортировать в [Anki](http://ankisrs.net) и [MyTestX](http://mytest.klyaksa.net), чтобы проходить тестирование с обучением offline.
 
**Примеры результатов**: для [Anki](https://github.com/radioxoma/vsmu-scripts/blob/master/tests/evsmu/g495_anki.csv), для [MyTestX](https://github.com/radioxoma/vsmu-scripts/blob/master/tests/evsmu/g495_mytestx.txt) (человекочитаемый), для [шпаргалки](https://github.com/radioxoma/vsmu-scripts/blob/master/tests/evsmu/g495_crib.txt).


## Installation

    $ pip install https://github.com/radioxoma/vsmu-scripts/archive/master.zip
    $ testparser --help


## Usage

General workflow:

1. Acquiring tests from Moodle
2. Parsing
3. Exporting to another program like Anki

### Acquiring tests

From Moodle: Необходимо пройти тест на произвольное количество баллов и сохранить HTML-страницу с результатами в файл (для Firefox: *Файл > Сохранить как..., 'Веб-страница, только HTML'*). Чтобы отобразить все тесты на одной странице, следует нажать на соответствующую кнопку или добавить к ссылке на страницу с ответами параметр `&showall=true`, например:

    http://e-vsmu.by/mod/quiz/review.php?attempt=111111&showall=true

Если HTML-страница не содержит информации о правильных ответах, все варианты будут считаться неверными.

### Parsing

Program applies specific parser automatically by file extension, so user have to rename input files. Multiple files can be parsed at one run.

    testparser *evsmu.htm --to-mytestx mytestx.txt  # Filter evsmu html pages
    testparser testdir/* --to-mytestx mytestx.txt  # Parse all tests in directory


### Export

* `-p` print tests to stdout
* `--to-mytestx` human-readable format (windows-1251, '\r' newlines) for russian program called "MyTestX". Use parser *TextToMyTestX.exe* from it's website.
* `--to-anki` Install desktop [Anki](https://en.wikipedia.org/wiki/Anki_(software)) version, *File > Import* check "*Разрешить использование HTML в полях*" (HTML required for test alignment to left). Standard fields "Question" and "Answer" are used.


### Known issues

* В `--to-crib` появятся одинаковые строки, если существует несколько тестов с одинаковым вопросом и правильным ответом (неправильные ответы произвольные);
* Неэкранированные символы `<` и `>` в тексте приводят к падению парсера. В качестве временного решения, их можно заменить на словесные эквиваленты или escape-последовательности;
* Внутреннее HTML-форматирование не поддерживается (например над- и подстрочные знаки формул, таким образом CO<sub>2</sub> будет отображён как CO2);
* Нет поддержки иллюстраций.


## Command line tips

    $ libreoffice --headless --convert-to txt *  # Batch file conversion to plaintext with LibreOffice
    $ pdftotext  # From package poppler-utils
    $ iconv -c -f utf-8 -t windows-1251 > win.txt

### Some sed magic from my wild youth

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
