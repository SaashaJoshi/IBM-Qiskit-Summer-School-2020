#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


def validate(checker, to_check, check_name, details, silent=False):
    if checker(to_check):
        if not silent:
            print('👍  %s' % check_name)
    else:
        msg = "❌  %s - %s" % (check_name, details)
        if silent:
            raise Exception(msg)
        else:
            print(msg)


def validate_name_email(name, email, silent=False):

    validate(lambda x: x is not None, name, 'name provided?',
             'You should provide a name', silent)
    validate(lambda x: x is not None, email, 'name provided?',
             'You should provide an email address', silent)
    validate(lambda x: isinstance(x, str), name, 'is name a str?',
             'The name should be a string', silent)
    validate(lambda x: isinstance(x, str), email, 'is email a str?',
             'The email address should be a string', silent)
    validate(lambda x: 'First Last' not in x, name, 'is name set?',
             'You should write your name in the name variable', silent)
    validate(lambda x: 'first.last@domain.com' not in x, email, 'is email set?',
             'You should write your email address in the email variable', silent)

