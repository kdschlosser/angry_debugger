# -*- coding: utf-8 -*-

# **angry_debugger** is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# **angry_debugger** is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with angry_debugger. If not, see http://www.gnu.org/licenses.

"""
This file is part of the **angry_debugger**
project https://github.com/kdschlosser/angry_debugger

:platform: Unix, Windows, OSX
:license: GPL(v3)
:synopsis: angry_debugger

.. moduleauthor:: Kevin Schlosser @kdschlosser <kevin.g.schlosser@gmail.com>
"""

import logging
import threading
import traceback
import sys
import time
import inspect
import functools
from logging import NullHandler

from .utils import (
    caller_name,
    get_line_and_file,
    func_arg_string
)

logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())

PY3 = sys.version_info[0] > 2

LOGGING_TEMPLATE = '''\
[{debug_type}] \
{thread_name}\
[{thread_id}]
                          src: {calling_obj} [{calling_filename}:{calling_line_no}]
                          dst: {called_obj} [{called_filename}:{called_line_no}]
                          {msg}'''

LEVEL_TIME_IT = 128
LEVEL_ARGS = 256
LEVEL_RETURN = 512
LEVEL_CALL_FROM = 1024
LEVEL_CALL_TO = 2048
LEVEL_ANGRY = 3968

logging.addLevelName(LEVEL_TIME_IT, 'TIME_IT')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_ARGS, 'TIME_IT | ARGS')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_ARGS | LEVEL_RETURN, 'TIME_IT | ARGS | RETURN')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_ARGS | LEVEL_RETURN | LEVEL_CALL_FROM, 'TIME_IT | ARGS | RETURN | CALL_FROM')
logging.addLevelName(LEVEL_ANGRY, 'ANGRY')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_ARGS | LEVEL_RETURN | LEVEL_CALL_TO, 'TIME_IT | ARGS | RETURN | CALL_TO')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_ARGS | LEVEL_CALL_FROM, 'TIME_IT | ARGS | CALL_FROM')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_ARGS | LEVEL_CALL_FROM | LEVEL_CALL_TO, 'TIME_IT | ARGS | CALL_FROM | CALL_TO')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_ARGS | LEVEL_CALL_TO, 'TIME_IT | ARGS | CALL_TO')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_RETURN, 'TIME_IT | RETURN')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_RETURN | LEVEL_CALL_FROM, 'TIME_IT | RETURN | CALL_FROM')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_RETURN | LEVEL_CALL_FROM | LEVEL_CALL_TO, 'TIME_IT | RETURN | CALL_FROM | CALL_TO')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_RETURN | LEVEL_CALL_TO, 'TIME_IT | RETURN | CALL_TO')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_CALL_FROM, 'TIME_IT | CALL_FROM')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_CALL_FROM | LEVEL_CALL_TO, 'TIME_IT | CALL_FROM | CALL_TO')
logging.addLevelName(LEVEL_TIME_IT | LEVEL_CALL_TO, 'TIME_IT | CALL_TO')
logging.addLevelName(LEVEL_ARGS, 'ARGS')
logging.addLevelName(LEVEL_ARGS | LEVEL_RETURN, 'ARGS | RETURN')
logging.addLevelName(LEVEL_ARGS | LEVEL_RETURN | LEVEL_CALL_FROM, 'ARGS | RETURN | CALL_FROM')
logging.addLevelName(LEVEL_ARGS | LEVEL_RETURN | LEVEL_CALL_FROM | LEVEL_CALL_TO, 'ARGS | RETURN | CALL_FROM | CALL_TO')
logging.addLevelName(LEVEL_ARGS | LEVEL_RETURN | LEVEL_CALL_TO, 'ARGS | RETURN | CALL_TO')
logging.addLevelName(LEVEL_ARGS | LEVEL_CALL_FROM, 'ARGS | CALL_FROM')
logging.addLevelName(LEVEL_ARGS | LEVEL_CALL_FROM | LEVEL_CALL_TO, 'ARGS | CALL_FROM | CALL_TO')
logging.addLevelName(LEVEL_ARGS | LEVEL_CALL_TO, 'ARGS | CALL_TO')
logging.addLevelName(LEVEL_RETURN, 'RETURN')
logging.addLevelName(LEVEL_RETURN | LEVEL_CALL_FROM, 'RETURN | CALL_FROM')
logging.addLevelName(LEVEL_RETURN | LEVEL_CALL_FROM | LEVEL_CALL_TO, 'RETURN | CALL_FROM | CALL_TO')
logging.addLevelName(LEVEL_RETURN | LEVEL_CALL_TO, 'RETURN | CALL_TO')
logging.addLevelName(LEVEL_CALL_FROM, 'CALL_FROM')
logging.addLevelName(LEVEL_CALL_FROM | LEVEL_CALL_TO, 'CALL_FROM | CALL_TO')
logging.addLevelName(LEVEL_CALL_TO, 'CALL_TO')


def _get_func_name(func):
    func_location = caller_name(2)
    func_name = func.__name__
    func_module = func.__module__

    if func_location:
        real_func_name = func_location + '.' + func_name
    else:
        real_func_name = func_module + '.' + func_name

    return func_name, func_location, func_module, real_func_name


def _get_duration(start, stop):
    divider = 1.0
    suffix = 'sec'
    suffixes = [
        'ms',
        'us',
        'ns',
        'ps',
        'fs',
        'as',
        'zs',
        'ys'
    ]

    duration = 0
    while suffixes:
        duration = round((stop - start) * divider, 3)
        if int(duration) > 0:
            break

        divider *= 1000.0
        suffix = suffixes.pop(0)

    if duration == 0:
        duration = '                          duration: to fast to measure\n'
    else:
        duration = '                          duration: {0:.3f} {1}\n'.format(duration, suffix)

    return duration


def _run_func(
        lgr,
        func_name,
        func_location,
        func_module,
        real_func_name,
        called_filename,
        called_line_no,
        obj_type,
        func,
        *args,
        **kwargs
):
    lgr_level = int(lgr.getEffectiveLevel())

    log_time_it = lgr_level | LEVEL_TIME_IT == lgr_level
    log_args = lgr_level | LEVEL_ARGS == lgr_level
    log_return = lgr_level | LEVEL_RETURN == lgr_level
    log_call_from = lgr_level | LEVEL_CALL_FROM == lgr_level
    log_call_to = lgr_level | LEVEL_CALL_TO == lgr_level

    if True not in (
        log_time_it,
        log_args,
        log_return,
        log_call_from,
        log_call_to
    ):
        return func(*args, **kwargs)

    if log_call_from:
        calling_filename, calling_line_no = get_line_and_file(3)
        calling_obj = caller_name()
    else:
        calling_filename = 'NOT LOGGED'
        calling_line_no = 'NOT LOGGED'
        calling_obj = 'NOT LOGGED'

    if not log_call_to:
        called_filename = 'NOT LOGGED'
        called_line_no = 'NOT LOGGED'

    thread = threading.current_thread()

    if log_args:
        arg_string = func_arg_string(func, args, kwargs)
    else:
        arg_string = ''

    if 'self' in kwargs:
        obj = kwargs['self']
        f_name = [
            obj.__class__.__module__,
            obj.__class__.__name__,
            func_name
        ]
    elif hasattr(func, '__class__') and len(args):
        obj = args[0]
        f_name = [
            obj.__class__.__module__,
            obj.__class__.__name__,
            func_name
        ]
    else:
        if func_location:
            f_name = [func_location, func_name]
        else:
            f_name = [func_module, func_name]

    f_name = '.'.join(f_name)

    if real_func_name != f_name:
        called_obj = real_func_name
    else:
        called_obj = f_name

    msg = 'function called: {0}{1}\n'.format(f_name, arg_string)

    msg = LOGGING_TEMPLATE.format(
        debug_type=logging.getLevelName(lgr_level),
        thread_name=thread.getName(),
        thread_id=thread.ident,
        calling_obj=calling_obj,
        calling_filename=calling_filename,
        calling_line_no=calling_line_no,
        called_obj=called_obj + obj_type,
        called_filename=called_filename,
        called_line_no=called_line_no,
        msg=msg
    )

    if log_time_it:
        start = time.time()
        result = func(*args, **kwargs)
        stop = time.time()

        msg += _get_duration(start, stop)

    else:
        result = func(*args, **kwargs)

    if log_return:
        msg += '                          {0} => {1}\n'.format(f_name, repr(result))

    if thread in _logging_runs:
        _logging_runs[thread] += [[lgr, lgr_level, msg + '\n']]
    elif _logging_runs:
        _unknown_logging.append([lgr, lgr_level, msg + '\n'])
    else:
        lgr.log(lgr_level, msg + '\n')

    return result


def log_it(obj):
    """
    OK so this is the skinny on how this works.

    log_it is if the main entry point. It logs the data path through a program.

    it provides output that looks like this

    2019-12-07 17:36:45,229 - [ANGRY] Thread-5[14016]
                          src: __main__.SomeClass.property_test_1 [C:/Users/Administrator/Documents/GitHub/angry_debugger/angry_debugger/__init__.py:783]
                          dst: __main__.SomeClass.property_test_4 (getter) [C:/Users/Administrator/Documents/GitHub/angry_debugger/angry_debugger/__init__.py:838]
                          function called: __main__.SomeClass.property_test_4()
                          duration: 0.5148007869720459 sec
                          __main__.SomeClass.property_test_4 => 'This is the property_test_4 getter'

    2019-12-07 17:36:45,073 - [ANGRY] Thread-4[14292]
                          src: __main__.do [C:/Users/Administrator/Documents/GitHub/angry_debugger/angry_debugger/__init__.py:889]
                          dst: __main__.SomeClass.method_test_1 [C:/Users/Administrator/Documents/GitHub/angry_debugger/angry_debugger/__init__.py:859]
                          function called: __main__.SomeClass.method_test_1(arg='argument 1')
                          duration: 358.80041122436523 ms
                          __main__.SomeClass.method_test_1 => None


    the layout of a log entry is as follows.

    {date} {time},{fractions of a second} - [{log level}] {thread name}[{thread id}]
                          src: {call origin} [{file}:{line number}]
                          dst: {call destination} [{file}:{line number}]
                          function called: {call destination}({arguments passed if any including defaults})
                          duration: {length of time the call took}
                          {call destination} => {return value}

    log_it can be used as a decorator for functions, methods and properties. It can also be used as a callable for
    class attributes.


    @log_it
    def some_method_or_function():
        pass


    if used on properties you have to place it before the property decorator. it is a selective decoration,
    what that meas is if you want to log only the setter portion you can do that by placing the log_it decorator
    before the setter only. This will log the getter, setter and deleter.


    class attributes
    instead of using log_it as a decorator you need to use it like you would a function and place the data
    into the function call that you want to have the attribnute set to.


    class SomeClass(object):
        class_attribute = log_it('this is the contents')


    you will have a log entry when the data gets accessed or changed.


    No I am sure at some point or another you have had to deal ith the logging mess when running a multi
    threaded application. It is a daunting task to sift through the log having to piece together a log that makes sense.

    I have simplified this for you. there are 2 functions also in this module.
    `start_logging_run` and `end_logging_run`
    so say you have a thread that is about to go to work. if you 'call start_logging_run' then do the work
    and call `end_logging_run` when finished it is going to spit out anl logging done by using log_it in the order
    in which each step through your application was taken. it keeps everything all nice and neat and easy to understand.
    it also times how long it took for the complete run to take. This is nice for determining a bottleneck.


    This library uses the logging module which is a standard library included with Python. This is important if you
    want things to get displayed correctly. You will want to have the following code in each of the files here you are
    using log_it.

    import logging
    logger = logging.getLogger(__name__)

    you can have logger set to LOGGER if you like it will work either way.

    log_it searches the functions, methods or properties __globals__ attribute to see if `logger' or `LOGGER` exits.
    and this is what gets used to output the log information for where the decorator is located.

    you are also going to wat to have the following in the __init__ of your application

    import logging

    FORMAT = '%(asctime)-15s - %(message)s'
    logging.basicConfig(level=NOTSET, format=FORMAT)

    you would change NOTSET to any of the logging levels included in this library. None of the logging levels that are
    apart of the logging library are going to make this decorator function.

    LEVEL_TIME_IT: times the calls
    LEVEL_ARGS: logs any parameters passed to a call
    LEVEL_RETURN: logs the return data from a call
    LEVEL_CALL_FROM: file and lone number information where the call was made from
    LEVEL_CALL_TO: file and line number information where the call was made to.
    LEVEL_ANGRY: all of the above

    I created the logging levels so they can be combined by means of "bitwise or" `|`. So if you want to log the
    returned data and the passed arguments you would use  `LEVEL_ARGS | LEVEL_RETURN` `LEVEL_ANGRY` is the same as doing
    `LEVEL_TIME_IT | LEVEL_ARGS | LEVEL_RETURN | LEVEL_CALL_FROM | LEVEL_CALL_TO`

    So here is the brief version

    Add this to the first file that gets run in your application

    import logging
    import angry_debugger
    FORMAT = '%(asctime)-15s - %(message)s'
    logging.basicConfig(level=angry_debugger.LEVEL_ARGS | angry_debugger.LEVEL_RETURN, format=FORMAT)


    you can change the level to any of the angry_debugger.LEVEL_* constants or a combination of them using
    the `|` between them

    add this to that first file as well and also to any file that is using log_it

    import logging
    logger = logging.getLogger(__name__)


    add this before a function, methods r property decleration

    @angry_debugger.log_it

    add this for a class attribute

    some_attribute = angry_debugger.log_it('some attribute value')
    
    ***IMPORTANT***
    
    This debugging routine is very expensive to run. It WILL slow down the program you are using it in if the
    logging level is set to one of the level constants. This library is for debugging use ONLY. it can create HUGE
    amounts of data in a really small period of time. So be careful when having it write to a file.

    """

    called_filename, called_line_no = get_line_and_file()
    called_line_no += 1

    if isinstance(obj, property):
        fset = obj.fset
        fget = obj.fget
        fdel = obj.fdel

        if fget is None and fset.__doc__ is not None:
            doc = fset.__doc__
        elif fget is not None and fget.__doc__ is not None:
            doc = fget.__doc__
        elif fdel is not None and fdel.__doc__ is not None:
            doc = fdel.__doc__
        else:
            doc = None

        class FDelWrapper(object):

            def __init__(self, fdel_object):
                self._fdel_object = fdel_object
                if func_name:
                    self._f_name = func_name + '.' + fdel_object.__name__
                else:
                    self._f_name = (
                            fdel_object.__module__ + '.' + fdel_object.__name__
                    )

                if 'logger' in fdel_object.__globals__:
                    lgr = fdel_object.__globals__['logger']
                elif 'LOGGER' in fdel_object.__globals__:
                    lgr = fdel_object.__globals__['LOGGER']
                else:
                    lgr = logging.getLogger(fdel_object.__module__)

                if not isinstance(lgr, logging.Logger):
                    lgr = logging.getLogger(fdel_object.__module__)

                self._lgr = lgr

            def __call__(self, *args, **kwargs):
                return _run_func(
                    self._lgr,
                    func_name,
                    func_location,
                    func_module,
                    real_func_name,
                    called_filename,
                    called_line_no,
                    ' (deleter)',
                    self._fdel_object,
                    *args,
                    **kwargs
                )

        class FSetWrapper(object):

            def __init__(self, fset_object):
                self._fset_object = fset_object
                if func_name:
                    self._f_name = func_name + '.' + fset_object.__name__
                else:
                    self._f_name = (
                            fset_object.__module__ + '.' + fset_object.__name__
                    )

                if 'logger' in fset_object.__globals__:
                    self._lgr = fset_object.__globals__['logger']
                elif 'LOGGER' in fset_object.__globals__:
                    self._lgr = fset_object.__globals__['LOGGER']
                else:
                    self._lgr = logging.getLogger(fset_object.__module__)

                if not isinstance(self._lgr, logging.Logger):
                    self._lgr = logging.getLogger(fset_object.__module__)

            def __call__(self, *args, **kwargs):

                return _run_func(
                    self._lgr,
                    func_name,
                    func_location,
                    func_module,
                    real_func_name,
                    called_filename,
                    called_line_no,
                    ' (setter)',
                    self._fset_object,
                    *args,
                    **kwargs
                )

        class FGetWrapper(object):

            def __init__(self, fget_object):
                self._fget_object = fget_object
                if func_name:
                    self._f_name = func_name + '.' + fget_object.__name__
                else:
                    self._f_name = (
                            fget_object.__module__ + '.' + fget_object.__name__
                    )

                if 'logger' in fget_object.__globals__:
                    self._lgr = fget_object.__globals__['logger']
                elif 'LOGGER' in fget_object.__globals__:
                    self._lgr = fget_object.__globals__['LOGGER']
                else:
                    self._lgr = logging.getLogger(fget_object.__module__)

                if not isinstance(self._lgr, logging.Logger):
                    self._lgr = logging.getLogger(fget_object.__module__)

            def __call__(self, *args, **kwargs):
                return _run_func(
                    self._lgr,
                    func_name,
                    func_location,
                    func_module,
                    real_func_name,
                    called_filename,
                    called_line_no,
                    ' (getter)',
                    self._fget_object,
                    *args,
                    **kwargs
                )

        if fdel is not None:
            func_name, func_location, func_module, real_func_name = _get_func_name(fdel)
            return property(fget=fget, fset=fset, fdel=FDelWrapper(fdel), doc=doc)

        if fset is not None:
            func_name, func_location, func_module, real_func_name = _get_func_name(fset)
            return property(fget=fget, fset=FSetWrapper(fset), fdel=fdel, doc=doc)

        func_name, func_location, func_module, real_func_name = _get_func_name(fget)
        return property(FGetWrapper(fget), fset, doc=doc)

    elif inspect.isfunction(obj) or inspect.ismethod(obj):
        if 'logger' in obj.__globals__:
            lgr = obj.__globals__['logger']

        elif 'LOGGER' in obj.__globals__:
            lgr = obj.__globals__['LOGGER']
        else:
            lgr = logging.getLogger(obj.__module__)

        if not isinstance(lgr, logging.Logger):
            lgr = logging.getLogger(obj.__module__)

        func_name, func_location, func_module, real_func_name = _get_func_name(obj)

        def wrapper(*args, **kwargs):

            return _run_func(
                lgr,
                func_name,
                func_location,
                func_module,
                real_func_name,
                called_filename,
                called_line_no,
                '',
                obj,
                *args,
                **kwargs
            )

        wrapper = functools.update_wrapper(wrapper, obj)
        return wrapper

    elif inspect.isclass(obj):
        func_name, func_location, func_module, real_func_name = _get_func_name(obj)

        if func_name:
            class_name = func_name + '.' + obj.__name__
        else:
            class_name = obj.__module__ + '.' + obj.__name__

        def wrapper(*args, **kwargs):
            return _run_func(
                lgr,
                class_name,
                func_location,
                func_module,
                real_func_name,
                called_filename,
                called_line_no,
                '',
                obj,
                *args,
                **kwargs
            )

        return functools.update_wrapper(wrapper, obj)
    else:
        # noinspection PyProtectedMember
        frame = sys._getframe().f_back
        source = inspect.findsource(frame)[0]
        called_line_no -= 1

        while (
                '=log_it' not in source[called_line_no] and
                '= log_it' not in source[called_line_no] and
                '=angry_debugger.log_it' not in source[called_line_no] and
                '= angry_debugger.log_it' not in source[called_line_no]
        ):
            called_line_no -= 1

        symbol = source[called_line_no].split('=')[0].strip()

        func_name = caller_name(1)

        if func_name:
            symbol_name = func_name + '.' + symbol
            lgr = logging.getLogger(func_name)
        else:
            lgr = logger
            symbol_name = symbol

        def get_wrapper(*_, **__):
            lgr_level = int(lgr.getEffectiveLevel())

            log_call_from = lgr_level | LEVEL_CALL_FROM == lgr_level
            log_call_to = lgr_level | LEVEL_CALL_TO == lgr_level

            log_angry = lgr_level == LEVEL_ANGRY

            if True not in (log_call_from, log_call_to, log_angry):
                return obj[0]

            if log_call_to:
                c_filename = called_filename
                c_line_no = called_line_no
            else:
                c_filename = 'NOT LOGGED'
                c_line_no = 'NOT LOGGED'

            if log_call_from:
                calling_filename, calling_line_no = get_line_and_file()
                calling_obj = caller_name()
            else:
                calling_filename = 'NOT LOGGED'
                calling_line_no = 'NOT LOGGED'
                calling_obj = 'NOT LOGGED'

            msg = 'attribute get: {0}\n'.format(symbol_name)

            thread = threading.current_thread()

            msg = LOGGING_TEMPLATE.format(
                debug_type=logging.getLevelName(lgr_level),
                thread_name=thread.getName(),
                thread_id=thread.ident,
                calling_obj=calling_obj,
                calling_filename=calling_filename,
                calling_line_no=calling_line_no,
                called_obj=symbol_name + ' (attribute)',
                called_filename=c_filename,
                called_line_no=c_line_no,
                msg=msg
            )

            if thread in _logging_runs:
                _logging_runs[thread] += [[lgr, lgr_level, msg + '\n']]
            elif _logging_runs:
                _unknown_logging.append([lgr, lgr_level, msg + '\n'])
            else:
                lgr.log(lgr_level, msg + '\n')

            return obj[0]

        def set_wrapper(self, value):
            lgr_level = int(lgr.getEffectiveLevel())

            log_call_from = lgr_level | LEVEL_CALL_FROM == lgr_level
            log_call_to = lgr_level | LEVEL_CALL_TO == lgr_level

            log_angry = lgr_level == LEVEL_ANGRY

            if True not in (log_call_from, log_call_to, log_angry):
                return obj[0]

            if log_call_to:
                c_filename = called_filename
                c_line_no = called_line_no
            else:
                c_filename = 'NOT LOGGED'
                c_line_no = 'NOT LOGGED'

            if log_call_from:
                calling_filename, calling_line_no = get_line_and_file()
                calling_obj = caller_name()
            else:
                calling_filename = 'NOT LOGGED'
                calling_line_no = 'NOT LOGGED'
                calling_obj = 'NOT LOGGED'

            msg = 'attribute set: {0} = {1}\n'.format(symbol_name, repr(value))

            thread = threading.current_thread()

            msg = LOGGING_TEMPLATE.format(
                debug_type=logging.getLevelName(lgr_level),
                thread_name=thread.getName(),
                thread_id=thread.ident,
                calling_obj=calling_obj,
                calling_filename=calling_filename,
                calling_line_no=calling_line_no,
                called_obj=symbol_name,
                called_filename=c_filename,
                called_line_no=c_line_no,
                msg=msg
            )

            if thread in _logging_runs:
                _logging_runs[thread] += [[lgr, lgr_level, msg + '\n']]
            elif _logging_runs:
                _unknown_logging.append([lgr, lgr_level, msg + '\n'])
            else:
                lgr.log(lgr_level, msg + '\n')

            obj[0] = value

        obj = [obj]

        return property(get_wrapper, set_wrapper)


_logging_runs = {}
_unknown_logging = []
_logging_run_lock = threading.Lock()
_logging_run_times = {}


STAR_TEMPLATE = '*' * 20 + ' {0} Logging Run {1} ' + ('*' * 20) + '\n'


def start_logging_run():
    thread = threading.current_thread()

    with _logging_run_lock:
        for lgr, level, msg in _unknown_logging[:]:
            _unknown_logging.remove([lgr, level, msg])
            lgr.log(level, msg)

        if thread in _logging_runs and _logging_runs[thread]:
            started = False
            lgr = None
            level = None

            for lgr, level, msg in _logging_runs[thread]:
                if not started:
                    started = True
                    lgr.log(level, STAR_TEMPLATE.format('Start', thread.getName()))

                lgr.log(level, msg)

            start = _logging_run_times[thread]
            stop = time.time()

            msg = _get_duration(start, stop)
            msg += STAR_TEMPLATE.format('Stop', thread.getName())

            lgr.log(level, msg)

        start = time.time()
        _logging_run_times[thread] = start
        _logging_runs[thread] = []


def end_logging_run():
    thread = threading.current_thread()
    with _logging_run_lock:
        for lgr, level, msg in _unknown_logging[:]:
            _unknown_logging.remove([lgr, level, msg])
            lgr.log(level, msg)

        if thread in _logging_runs:
            if _logging_runs[thread]:
                started = False
                lgr = None
                level = None

                for lgr, level, msg in _logging_runs[thread]:
                    if not started:
                        started = True
                        lgr.log(level, STAR_TEMPLATE.format('Start', thread.getName()))
                    lgr.log(level, msg)

                start = _logging_run_times[thread]
                stop = time.time()
                msg = _get_duration(start, stop)
                msg += STAR_TEMPLATE.format('Stop', thread.getName())

                lgr.log(level, msg)

            del _logging_run_times[thread]
            del _logging_runs[thread]


def logging_run(func):
    def wrapper(*args, **kwargs):
        start_logging_run()
        result = func(*args, **kwargs)
        end_logging_run()
        return result

    return wrapper


# This is rather odd to see.
# I am using sys.excepthook to alter the displayed traceback data.
# The reason why I am doing this is to remove any lines that are generated
# from any of the code in this file. It adds a lot of complexity to the
# output traceback when any lines generated from this file do not really need
# to be displayed.

def trace_back_hook(tb_type, tb_value, tb):
    tb = "".join(
        traceback.format_exception(
            tb_type,
            tb_value,
            tb,
        )
    )
    if tb_type == DeprecationWarning:
        sys.stderr.write(tb)
    else:
        new_tb = []
        skip = False
        for line in tb.split('\n'):
            if line.strip().startswith('File'):
                if __file__ in line:
                    skip = True
                else:
                    skip = False
            if skip:
                continue

            new_tb += [line]

        sys.stderr.write('\n'.join(new_tb))


_old_except_hook = sys.excepthook

sys.excepthook = trace_back_hook


def unhook_exceptions():
    sys.excepthook = _old_except_hook


def hook_exceptions():
    sys.excepthook = trace_back_hook

