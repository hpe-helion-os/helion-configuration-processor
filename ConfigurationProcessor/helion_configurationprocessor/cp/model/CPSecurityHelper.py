#
# (c) Copyright 2015 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
import string


class CPSecurityHelper(object):

    def calculate_complexity(self, secret):
        score = 0
        score += self._num_chars_evaluator(secret)
        score += self._num_uc_evaluator(secret)
        score += self._num_lc_evaluator(secret)
        score += self._num_digits_evaluator(secret)
        score += self._num_punct_evaluator(secret)
        score += self._num_categories_evaluator(secret)

        score -= self._letters_only_penalty(secret)
        score -= self._numbers_only_penalty(secret)
        score -= self._letters_repeat_penalty(secret)
        score -= self._consecutive_uc_letters_penalty(secret)
        score -= self._consecutive_lc_letters_penalty(secret)
        score -= self._consecutive_numbers_penalty(secret)
        score -= self._sequential_letters_penalty(secret)
        score -= self._sequential_numbers_penalty(secret)
        score -= self._sequential_punct_penalty(secret)

        score = min(score, 100)
        score = max(score, 0)

        status = self._get_status(score)

        return score, status

    def _get_status(self, score):
        if score < 70:
            return 'Bad'
        elif score < 80:
            return 'Insufficient'
        elif score < 90:
            return 'Sufficient'
        else:
            return 'Excellent'

    def _num_chars_evaluator(self, secret):
        return len(secret) * 4

    def _num_uc_evaluator(self, secret):
        num_uc = 0

        for i in range(len(secret)):
            if secret[i] in string.ascii_uppercase:
                num_uc += 1

        return num_uc * 2

    def _num_lc_evaluator(self, secret):
        num_uc = 0

        for i in range(len(secret)):
            if secret[i] in string.ascii_lowercase:
                num_uc += 1

        return num_uc * 2

    def _num_digits_evaluator(self, secret):
        num_uc = 0

        for i in range(len(secret)):
            if secret[i] in string.digits:
                num_uc += 1

        return num_uc * 4

    def _num_punct_evaluator(self, secret):
        num_uc = 0

        for i in range(len(secret)):
            if secret[i] in string.punctuation:
                num_uc += 1

        return num_uc * 6

    def _num_categories_evaluator(self, secret):
        has_lc = 0
        has_uc = 0
        has_d = 0
        has_p = 0

        for i in range(len(secret)):
            if secret[i] in string.punctuation:
                has_p = 1
            elif secret[i] in string.digits:
                has_d = 1
            elif secret[i] in string.ascii_uppercase:
                has_uc = 1
            elif secret[i] in string.ascii_lowercase:
                has_lc = 1

        return (has_p + has_d + has_uc + has_lc) * 2

    def _letters_only_penalty(self, secret):
        for i in range(len(secret)):
            if secret[i] in string.punctuation:
                return 0
            elif secret[i] in string.digits:
                return 0

        return len(secret)

    def _numbers_only_penalty(self, secret):
        for i in range(len(secret)):
            if secret[i] in string.punctuation:
                return 0
            elif secret[i] in string.ascii_lowercase:
                return 0
            elif secret[i] in string.ascii_uppercase:
                return 0

        return len(secret)

    def _letters_repeat_penalty(self, secret):
        penalty = 0

        last_char = '0'
        for i in range(len(secret)):
            if (secret[i] in string.ascii_lowercase or
                    secret[i] in string.ascii_uppercase):

                if secret[i].lower() == last_char.lower():
                    penalty += 1

                last_char = secret[i].lower()
            else:
                last_char = '0'

        return penalty * 4

    def _consecutive_uc_letters_penalty(self, secret):
        penalty = 0

        for i in range(len(secret) - 1):
            if (secret[i] in string.ascii_uppercase and
                    secret[i + 1] in string.ascii_uppercase):
                penalty += 1

        return penalty * 2

    def _consecutive_lc_letters_penalty(self, secret):
        penalty = 0

        for i in range(len(secret) - 1):
            if (secret[i] in string.ascii_lowercase and
                    secret[i + 1] in string.ascii_lowercase):
                penalty += 1

        return penalty * 2

    def _consecutive_numbers_penalty(self, secret):
        penalty = 0

        for i in range(len(secret) - 1):
            if (secret[i] in string.digits and
                    secret[i + 1] in string.digits):
                penalty += 1

        return penalty * 2

    def _sequential_letters_penalty(self, secret):
        penalty = 0

        for i in range(len(secret) - 2):
            if ((secret[i] in string.ascii_uppercase or
                 secret[i] in string.ascii_lowercase) and
                (secret[i + 1] in string.ascii_uppercase or
                 secret[i + 1] in string.ascii_lowercase) and
                (secret[i + 2] in string.ascii_uppercase or
                 secret[i + 2] in string.ascii_lowercase)):

                val1 = ord(secret[i].lower())
                val2 = ord(secret[i + 1].lower())
                val3 = ord(secret[i + 2].lower())

                if (val2 - val1) == 1:
                    if (val3 - val2) == 1:
                        penalty += 1

        return penalty * 3

    def _sequential_numbers_penalty(self, secret):
        penalty = 0

        for i in range(len(secret) - 2):
            if (secret[i] in string.digits and
                secret[i + 1] in string.digits and
                    secret[i + 2] in string.digits):

                val1 = int(secret[i])
                val2 = int(secret[i + 1])
                val3 = int(secret[i + 2])

                if (val2 - val1) == 1:
                    if (val3 - val2) == 1:
                        penalty += 1

        return penalty * 3

    def _get_punct_index(self, value):
        punct = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')']
        return punct.index(value)

    def _sequential_punct_penalty(self, secret):
        penalty = 0

        for i in range(len(secret) - 2):
            if (secret[i] in string.punctuation and
                secret[i + 1] in string.punctuation and
                    secret[i + 2] in string.punctuation):

                val1 = self._get_punct_index(secret[i])
                val2 = self._get_punct_index(secret[i + 1])
                val3 = self._get_punct_index(secret[i + 2])

                if (val2 - val1) == 1:
                    if (val3 - val2) == 1:
                        penalty += 1

        return penalty * 3
