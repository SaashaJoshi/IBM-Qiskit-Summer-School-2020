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

import numpy as np
import os
import json
from typing import Any
import requests
from qiskit import QuantumCircuit, assemble
from qiskit.qobj import PulseQobj
from .validate_config import validate_name_email

dir_path = os.path.dirname(os.path.realpath(__file__))

SERVERS = ['http://127.0.0.1:5000',
           'https://us-south.functions.appdomain.cloud/api/v1/web/1d8ef74d-78f2-4214-a876-b8e011a0c87e/default/qgss_grading',
           'https://eu-gb.functions.cloud.ibm.com/api/v1/web/salvador.de.la.puente.gonzalez%40ibm.com_dev/default/qgss_grading',
           'https://salvadelapuente.com:8088']


def get_a_server(labid=None, exid=None):
    for server in SERVERS:
        try:
            response = requests.get(url=server + '/')
            response.raise_for_status()
            if response.json().get('Qiskit Global Summer School') == '2020':
                if labid and exid:
                    available_validations = response.json().get('available validations')
                    if available_validations is None:
                        return server
                    if [labid, exid] in available_validations:
                        return server
                    else:
                        continue
                return server
        except Exception:
            pass


def search_ex(labdir):
    ret = []
    for file in os.listdir(labdir):
        if file.startswith('ex') and file.endswith(".py"):
            ret.append(os.path.abspath(os.path.join(labdir, file)))
    if len(ret) == 0:
        raise Exception('No exercise found!')
    return sorted(ret)


def qobj_to_json(qobj: PulseQobj) -> str:
    class _QobjEncoder(json.encoder.JSONEncoder):
        def default(self, obj: Any) -> Any:
            if isinstance(obj, np.ndarray):
                return {'__class__': 'ndarray', 'list': obj.tolist()}
            if isinstance(obj, complex):
                return {'__class__': 'complex', 're': obj.real, 'im': obj.imag}
            return json.JSONEncoder.default(self, obj)

    return json.dumps(qobj.to_dict(), cls=_QobjEncoder)


def circuit_to_json(qc: QuantumCircuit) -> str:
    qobj = assemble(qc)
    return qobj_to_json(qobj)


def check_answer(answer, lab_name, exercise_name, participant_name, participant_email,
                 endpoint=None, verbose=True, session=None):
    is_update = False

    if answer is None:
        result_msg = '🤐 Skip'
        result_msg += ': answer variable is None' if verbose else ''
    elif not isinstance(answer, (QuantumCircuit, PulseQobj)):
        result_msg = '🤐 Skip'
        result_msg += ': answer variable should be a QuantumCircuit or a PulseQobj (not %s)' % \
                      type(answer) if verbose else ''
    else:
        answer_type = type(answer).__name__
        answer_string = circuit_to_json(answer) if answer_type == 'QuantumCircuit' \
            else qobj_to_json(answer)

        data = {'answer': answer_string,
                'answer_type': answer_type,
                'participant_name': participant_name,
                'participant_email': participant_email,
                'lab_id': lab_name,
                'ex_id': exercise_name}

        if session:
            data['session'] = session
        answer_response = send_request(data, endpoint)
        is_update = answer_response.get('is_update', True)
        if answer_response.get('is_valid'):
            result_msg = '🎉 Correct'
        else:
            cause = answer_response.get('cause')
            if (cause is None or 'owner does not match request owner' in cause) and session:
                print(cause, '...Retrying with a fresh session...')
                return check_answer(answer, lab_name, exercise_name, participant_name,
                                    participant_email, endpoint=endpoint, verbose=verbose)
            result_msg = '❌ Failed'
            result_msg += ': %s' % answer_response.get('cause') if verbose else ''
        session = answer_response.get('session')
    return "%s/%s - %s" % (lab_name, exercise_name, result_msg), session, is_update


def send_request(data, endpoint, header=None):
    header = header if header else {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.post(url=endpoint, json=data, headers=header)
    if "Cannot decipher" in response.text:
        print('Cannot decipher session!')
    response.raise_for_status()
    return response.json()


def commit_answer_file(labid, email, answerfile=None):
    session = create_session(answerfile)
    commit_answer(labid, email, session)


def commit_answer(labid, email, session, server):
    print("Submitting the answers for %s..." % labid)
    data = {'participant_email': email,
            'session': session}
    answer = send_request(data, server + '/commit-answers')
    if answer.get('is_committed'):
        print('📝 Our records, so far, are:')
        print_record(answer, 'Correct answers')
        print_record(answer, 'Incorrect answers')
    else:
        print('Something went wrong with the submission: %s' % answer.get('cause'))


def print_record(answer, record):
    if answer.get('details') and \
            answer['details'].get('fields') and answer['details']['fields'].get(record):
        print('%s: %s' % (record, answer['details']['fields'][record]))


def create_session(answerfile):
    if answerfile and not os.path.isfile(answerfile):
        raise FileExistsError('answer file %s does not exist' % answerfile)

    if answerfile is None:
        answerfile = os.path.join(dir_path, 'answers.enc')

    if os.path.isfile(answerfile):
        with open(answerfile, mode='r') as answerfile_file:
            session = answerfile_file.read()
    else:
        session = None
    return session


def grade(answer=None, name=None, email=None, labid=None, exerciseid=None,
          server=None, answerfile=None, force_commit=False):
    session = create_session(answerfile)
    validate_name_email(name, email, silent=True)

    if labid is None:
        print("🚫 In which lab are you?.")
        return

    if exerciseid is None:
        print("🚫 In which exercise are you?.")
        return

    print("Grading...")

    server = server if server else get_a_server(labid, exerciseid)
    if server is None:
        print("🚫 Either your internet connection is too unreliable or the grading servers are"
              " down right now.")
        return

    result, session, is_update = check_answer(answer,
                                              labid,
                                              exerciseid,
                                              name,
                                              email,
                                              server + '/validate-answer',
                                              session=session)
    if session:
        with open(os.path.join(dir_path, 'answers.enc'), 'w') as answer_file:
            answer_file.write(session)
    print(result)

    if is_update:
        force_commit = True
        if "Correct" in result:
            print("🎊 Hurray! You have a new correct answer! Let's submit it.")

    if force_commit:
        commit_answer(labid, email, session, server)


def send_code(filename, server=None):
    import hashlib
    import base64

    server = server if server else get_a_server()

    if server is None:
        print("🚫 Either you is too unreliable or the grading servers are down right now.")
        return

    sha1 = hashlib.sha1()
    text = ''
    with open(filename, 'r') as fp:
        line = fp.readline()
        while line:
            if 'name =' in line:
                line = fp.readline()
                continue
            if 'email =' in line:
                line = fp.readline()
                continue
            text += line
            line = fp.readline()

    encoded = base64.standard_b64encode(text.encode()).decode('utf-8')
    sha1.update(text.encode())

    data = {'filename': filename,
            'hash': sha1.hexdigest(),
            'content': encoded}

    print('Sending %s ...' % filename)
    answer = send_request(data, server + '/send-file')
    if answer.get('is_sent'):
        print('Sent. Thanks!')
    else:
        print('Error:', answer.get('cause'))
