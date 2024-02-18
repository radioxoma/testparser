import functools
import json
import warnings
from itertools import zip_longest

import lxml.html


class Question:
    """Quiz question object containing plain text question and choices."""

    def __init__(self, question):
        super().__init__()
        self.__strip_compare: str = "\n\t :;.?"  # If None, act as defaut Python strip()
        self.question: str = question
        self.answers: dict = dict()
        self.image_path: str = ""
        if not self.question:
            warnings.warn("Empty question added")

    def __str__(self):
        """Print question in human-readable format (old MyTextX style).

            # An question
            @ image.jpg
            + Right answer
            - False answer
            + Another right answer
            - Another false-marked answer

        At least one empty string between tests must be preserved.
        """
        info = [f"# {self.question}"]
        if self.image_path:
            info.append(f"@ {self.image_path}")
        for v, c in self.answers.items():
            info.append(f"{'+' if c else '-'} {v}")
        return "\n".join(info) + "\n"

    def __hash__(self):
        """Mimic immutable type for ability to pack object in set."""
        return hash(
            (
                self.question_generalized,
                self.image_path,
                tuple(sorted(self.answers_generalized.items())),
            )
        )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise AttributeError("Comparison with other object type")
        if not self.question_generalized == other.question_generalized:
            return False
        if not self.image_path == other.image_path:
            return False
        # Answers with True/False mark
        if not self.answers_generalized == other.answers_generalized:
            return False
        return True

    def __bool__(self):
        """True if contains any choice marked as True.

        Test can contain all False choices if answer wasn't given.
        """
        return any(self.answers.values())

    def add_one_answer(self, variant: str, correct: bool) -> None:
        """Add one answer-corect_or_none pair.

        Args:
            variant: An answer.
            correct: True for correct, False for incorrect or unknown.
        """
        assert isinstance(variant, str)
        assert isinstance(correct, bool)
        variant = variant.strip(";,. ")
        if variant in self.answers:
            warnings.warn(
                f"Question '{self.question}' already has this variant: '{variant}'"
            )
            if self.answers[variant]:
                warnings.warn(
                    f"Duplicated variant marked as true previously, refuse to mark it as false: {self.question}"
                )
                return
        self.answers[variant] = correct

    def add_multiple_answers(self, variants, correct):
        """Add bunch of answer-corect_or_none pairs.

        :param list variants: An test variant
        :param bool correct: It's possible to pass just [False,] list
            to set all unknown answers to false. List will be expanded.
        """
        assert isinstance(variants, list) and isinstance(correct, list)
        assert len(variants) >= len(correct)
        for v, c in zip_longest(variants, correct, fillvalue=False):
            self.add_one_answer(v, c)

    def add_image_path(self, im_path: str) -> None:
        """Add one link to image file.

        Args:
            im_path: Path to image file.
        """
        self.image_path = im_path

    def correct(self):
        """Return only correct answers."""
        return filter(self.answers.get, self.answers)

    def sort_answers(self) -> None:
        """Sort answers dict in place."""
        self.answers = dict(sorted(self.answers.items()))

    @functools.cached_property
    def question_generalized(self) -> str:
        """Question for comparison, stripped of meaningless symbols."""
        return self.question.casefold().strip(self.__strip_compare)

    @functools.cached_property
    def answers_generalized(self) -> dict:
        """Answers for comparison, stripped of meaningless symbols.

        Order not preserved, as only choices with bool flags matters.
        """
        items = dict()
        for k, v in self.answers.items():
            # Answers with True/False mark
            items[k.casefold().strip(self.__strip_compare)] = v
        return items


def parse_palms(filename: str) -> list[Question | None]:
    """Parse MS PaLMS rawStructure.json (name '*.palms.json').

    You can fast-forward videos right to the end.

    https://palms-learning.ru
    https://crmm.ru

    Used by:
        https://sdo.kadrcentr.ru

    Look for "rawStructure.json", which contains course description and tests:
        * Click on a course link like https://sdo.kadrcentr.ru/assignment/9aae4240-f631-4dde-8ea8-e9e4997f7013 and available course buttons will appear
        * Clink on single course and immediately press F12, open "Network" tab. Look for "json/rawStructure.json" with test answers (also includes video, slides, text):
            https://sdo.kadrcentr.ru/api/static/content/bbbc62b0-fd4f-44cc-9dfa-83968b93fc91/35d4514d9c952b5972ae4a7c60686e94/json/rawStructure.json?hash=5-0-2

    Link generated by some method
        https://sdo.kadrcentr.ru/api/xapi/drivers/cmi5?xAPILaunchKey=
            https://sdo.kadrcentr.ru/api/static/content/bbbc62b0-fd4f-44cc-9dfa-83968b93fc91/35d4514d9c952b5972ae4a7c60686e94/index.html  # Probably random

    Etc:
        * JSON with courses assigned to me https://sdo.kadrcentr.ru/api/my-assignments/
        * Link to whole course HTML https://sdo.kadrcentr.ru/assignment/5bba1861-2102-410b-a20b-91518007244b
                               JSON https://sdo.kadrcentr.ru/api/my-assignments/5bba1861-2102-410b-a20b-91518007244b

            1-2 https://sdo.kadrcentr.ru/api/static/content/0ac8f2f9-09f8-40c3-ace4-b157456518dd/9328db33219839419122ae271aef10ed/json/rawStructure.json?hash=0-1-0
            1-3 https://sdo.kadrcentr.ru/api/static/content/62ac87d6-f2b8-48ae-b48c-fb07b77695b7/ddf0b8691d9c7be6b56d2a242bd45294/json/rawStructure.json?hash=0-1-0

            https://sdo.kadrcentr.ru/api/xapi/drivers/cmi5?xAPILaunchKey=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL3Nkby5rYWRyY2VudHIucnUvYXBpIiwic3ViIjoiNzUwODUiLCJpYXQiOjE3MDUyNjk4MDUuODUwOTI5LCJleHAiOjE3MDUzMTMwMDUuODUwODg5LCJyZWdpc3RyYXRpb24iOiJkZDM4OGExZi1mMWE4LTQyOTItOWNhYS1mOWEzN2NlNjQ4ZjAiLCJjb250ZW50X2lkIjoxMzk0LCJhdWQiOiJsbXMtY291cnNlcyJ9.2uZpzCurGfadEImTygVzRtb-DjIB4SOkJGmesoApz7s&xAPILaunchService=https%3A%2F%2Fsdo.kadrcentr.ru%2Fapi%2Fxapi%2F&url=https%3A%2F%2Fsdo.kadrcentr.ru%2Fapi%2Fstatic%2Fcontent%2F62ac87d6-f2b8-48ae-b48c-fb07b77695b7%2Fddf0b8691d9c7be6b56d2a242bd45294%2Findex.html&next=https://sdo.kadrcentr.ru/api/program/launch/1379/1394/next

        В процессе просмотра видео отправляется статус POST curl 'https://sdo.kadrcentr.ru/api/xAPI/statements' --compressed -X POST -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0' -H 'Accept: */*' -H 'Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3' -H 'Accept-Encoding: gzip, deflate, br' -H 'Content-Type: application/json' -H 'Authorization: Basic OTIwMzgzY2UyM2M2N2U3NzhlZDQ2YjlhNTk4OWEwNjFlYTE0ZTM1NzpmMGIxZDdmZmE4NGM1YTViNWFjY2JkNGIyMmNhYWMwZGZkNjg0YTE4' -H 'X-Experience-API-Version: 1.0.1' -H 'Origin: https://sdo.kadrcentr.ru' -H 'Connection: keep-alive' -H 'Referer: https://sdo.kadrcentr.ru/api/static/content/0ac8f2f9-09f8-40c3-ace4-b157456518dd/9328db33219839419122ae271aef10ed/index.html?activity_id=https%3A%2F%2Fcrmm.ru%2Fxapi%2Fcourses%2Flp_course_44059&actor=%7B%22objectType%22%3A%22Agent%22%2C%22account%22%3A%7B%22homePage%22%3A%22https%3A%2F%2Fsdo.kadrcentr.ru%2Fapi%2Faccounts%2Fuserid%22%2C%22name%22%3A%2275085%22%7D%7D&auth=Basic%20OTIwMzgzY2UyM2M2N2U3NzhlZDQ2YjlhNTk4OWEwNjFlYTE0ZTM1NzpmMGIxZDdmZmE4NGM1YTViNWFjY2JkNGIyMmNhYWMwZGZkNjg0YTE4&endpoint=https%3A%2F%2Fsdo.kadrcentr.ru%2Fapi%2FxAPI%2F&registration=dd388a1f-f1a8-4292-9caa-f9a37ce648f0&grouping=https%3A%2F%2Fsdo.kadrcentr.ru%2Fapi%2Fprogram%2F1546bd0f-06da-44d1-a824-836b9bbc90dd&context=%7B%22extensions%22%3A%7B%22https%3A%2F%2Fxapi.coursometer.ru%2Fvocabulary%2Fcontext%2Fextensions%2Fcourse%22%3A%22https%3A%2F%2Fsdo.kadrcentr.ru%2Fapi%2Fprogram%2F1546bd0f-06da-44d1-a824-836b9bbc90dd%22%7D%2C%22revision%22%3A%221%22%2C%22contextActivities%22%3A%7B%22grouping%22%3A%5B%7B%22objectType%22%3A%22Activity%22%2C%22id%22%3A%22https%3A%2F%2Fsdo.kadrcentr.ru%2Fapi%2Fprogram%2F1546bd0f-06da-44d1-a824-836b9bbc90dd%22%2C%22definition%22%3A%7B%22type%22%3A%22http%3A%2F%2Fadlnet.gov%2Fexpapi%2Factivities%2Fcourse%22%2C%22extensions%22%3A%7B%22https%3A%2F%2Fsberbank-school.ru%2Fxapi%2Fextensions%2Frevision%22%3A%221%22%7D%7D%7D%5D%7D%7D' -H 'Cookie: __ddg1_=CJyXVcgr59T0iaRcyP61; XSRF-TOKEN=eyJpdiI6IjBUVlpOTTNIdUVTbHJqaWJxNXRhaHc9PSIsInZhbHVlIjoiaDJBTnB0NE9NYXJ4dGNoRlhuTFV0a3lqdnp3UXNOZHNXdFIzdXpuUnFEVU5rMXRPZ2VIMWIrWHdCLzB0ME5wazB3Z2ZsYUM3ZVRhL2FmN2RHaVA0QVYzVmFsUC94UG5mb0V2bkhsMzlmdzU1NHA0OFFEQnBkVUpka2hSM1YvdE4iLCJtYWMiOiI0YzUwM2M2Y2ExNjY5Y2JiMTI1YTlmZTY0MmRiYTc0NDRhZGY3MDA5NzIxODFlNTg0ZWEyMjVmMTkwYjg1NzA5IiwidGFnIjoiIn0%3D; kadrcentr=eyJpdiI6Imp1Wk9DWEZObkhuVjY4RTNkTEpvd2c9PSIsInZhbHVlIjoid3FRRFI1aUIwdU1VM3JJTEdGNE90TnRkeXdlb1N3NHd1dWhZK0tkMGprUDdPRXJndmNDS2FFTEtkN3dJTmYwZVRSd3ZzVXNDZTkyTjlndzlHR3dzWktmeHE5TW5BSHptZTdtdXYrVDJaNjZIS0FvMXFYTzZiVkUrMUNxbzBSeGsiLCJtYWMiOiJhNmRhMGJiNTQ0MWNkOWIzMDNkNGIxZTJjZjMyNmQ1ODdhYjcxYTYwOTMyNWYzMTZhMWMxZmI5MzI3YjI3YmZhIiwidGFnIjoiIn0%3D; laravel_token=eyJpdiI6IitKeVR0WldQdWZtSEd3aHhFRHFCTWc9PSIsInZhbHVlIjoiZzJHYTVTcm42OEQxNTFNeklIUk52NlNIVEk5cjczVXFDdXhSY3JUM3lFMGROMzlGS2FranlESUU0R2JZb1hleFlCT0dDVUpOZ25BWXNoczRmdHdqTGtrYzNvRGVJWnVQUVNZZXM3RFY0Y3Zkc0xpdExqTWkwUmlKdjFkVXY2ZGlEWkFpQ0pTMmYvTmJnbzBqZHZIZ1R1OTVqaU1KaE5wN2dYNDR6K2k5SmZlaFlyMUs4bU5xaHZDa1g3UmkzeXJRZm9sdUlHR0dBZE5VNWxJbVJKckU2SmZzeXhCRjZ1bngyN2JMckUrWmxEQXZIMzVPMFNrMHZsTTBlOGpIWWZkUVFOekdvcE96NDdvWFRiTmhiODRMcU1zWXZRTVVHNStvWFh1SkJ1TXRMakVZVkJ6dHlXV0htS0k0QmpnVVptOWIiLCJtYWMiOiI2ODk4YjExOWNlYmM3MTFmMTUxZmRlYmE2MmEwMzIzNGNmZDNmYzhkMDBlZWRmNjFiZTgxN2NjMjI5YjNmZDdlIiwidGFnIjoiIn0%3D' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-origin' -H 'TE: trailers' --data-raw $'[{"id":"5df722e2-fb92-402a-a720-ee998540c062","actor":{"objectType":"Agent","account":{"homePage":"https://sdo.kadrcentr.ru/api/accounts/userid","name":"75085"}},"verb":{"id":"https://w3id.org/xapi/video/verbs/played","display":{"en-US":"played"}},"object":{"id":"https://crmm.ru/xapi/courses/lp_course_44059/qs6nly2oh4","objectType":"Activity","definition":{"name":{"en-US":"\u0412\u0438\u0434\u0435\u043e"},"description":{"en-US":"\u0412\u0438\u0434\u0435\u043e"},"type":"http://adlnet.gov/expapi/activities/knowledge"}},"context":{"extensions":{"https://xapi.coursometer.ru/vocabulary/context/extensions/course":"https://sdo.kadrcentr.ru/api/program/1546bd0f-06da-44d1-a824-836b9bbc90dd","contextExt:speed":1,"contextExt:viewId":"784b491a-4d57-4abd-a767-918577a91de8","contextExt:videoDuration":"PT4M16S"},"contextActivities":{"grouping":[{"id":"https://sdo.kadrcentr.ru/api/program/1546bd0f-06da-44d1-a824-836b9bbc90dd"}],"parent":{"id":"https://crmm.ru/xapi/courses/lp_course_44059/rfv57uc8hu","objectType":"Activity","definition":{"name":{"en-US":"\u041f\u0430\u0440\u0430\u043a\u043b\u0438\u043d\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u043e\u0431\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u0430\u0446\u0438\u0435\u043d\u0442\u043e\u0432 \u0441 \u043a\u043e\u0433\u043d\u0438\u0442\u0438\u0432\u043d\u044b\u043c\u0438 \u043d\u0430\u0440\u0443\u0448\u0435\u043d\u0438\u044f\u043c\u0438"},"description":{"en-US":"\u041f\u0430\u0440\u0430\u043a\u043b\u0438\u043d\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u043e\u0431\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u0430\u0446\u0438\u0435\u043d\u0442\u043e\u0432 \u0441 \u043a\u043e\u0433\u043d\u0438\u0442\u0438\u0432\u043d\u044b\u043c\u0438 \u043d\u0430\u0440\u0443\u0448\u0435\u043d\u0438\u044f\u043c\u0438"},"type":"http://adlnet.gov/expapi/activities/knowledge"}}},"registration":"dd388a1f-f1a8-4292-9caa-f9a37ce648f0"},"timestamp":"2024-01-15T00:32:06.291000+03:00","result":{"extensions":{"resultExt:resumed":"PT0S","resultExt:viewedRanges":[]}}}]'
    """

    def extract_tests(items):
        """Extract tests from JSON subtree.

        Possible to search entire JSON for `"type":"testing"` in first place
        """
        questions = list()
        for item in items:
            assert item["type"] == "test", "Not a test item"
            for key in (
                "attempts",
                "timeLimit",
                "groupTitle",
                "isAnswersShuffled",
                "completionThreshold",
                "isQuestionsShuffled",
            ):
                # print(f"{key}={item['config'][key]}")
                pass
            for question in item["content"]["questions"]:
                Q = Question(lxml.html.fromstring(question["text"]).text_content())
                for answer in question["answers"]:
                    Q.add_one_answer(
                        lxml.html.fromstring(answer["text"]).text_content(),
                        answer["correct"],
                    )
                questions.append(Q)
        return questions

    with open(filename) as f:
        courses = json.load(f)

    course_questions = list()
    # Courses/parts/items ('video', 'slide', 'test')
    for course in courses["courses"]:
        # print(course["name"])
        for part in course["items"]:
            # print(part["name"])
            for item in part["items"]:
                # print(f"{item['name']} '{item['type']}'")
                if item["type"] == "test":
                    course_questions.extend(extract_tests(part["items"]))
    return course_questions
