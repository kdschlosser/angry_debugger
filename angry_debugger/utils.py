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
project https://github.com/kdschlosser/angry_debugger.

:platform: Unix, Windows, OSX
:license: GPL(v3)
:synopsis: Utilities

.. moduleauthor:: Kevin Schlosser @kdschlosser <kevin.g.schlosser@gmail.com>
"""


from __future__ import print_function
import logging
import inspect
import sys

logger = logging.getLogger(__name__)

PY3 = sys.version_info[0] > 2


def get_line_and_file(stacklevel=2):
    """
    Gets the line number anf the file name where a call is made from and where a call is made to.
    """
    try:
        # noinspection PyProtectedMember
        caller = sys._getframe(stacklevel)
    except ValueError:
        glbs = sys.__dict__
        line_no = 1
    else:
        glbs = caller.f_globals
        line_no = caller.f_lineno
    if '__name__' in glbs:
        module = glbs['__name__']
    else:
        module = "<string>"
    filename = glbs.get('__file__')
    if filename:
        fnl = filename.lower()
        if fnl.endswith((".pyc", ".pyo")):
            filename = filename[:-1]
    else:
        if module == "__main__":
            try:
                filename = sys.argv[0]
            except AttributeError:
                # embedded interpreters don't have sys.argv
                filename = '__main__'
        if not filename:
            filename = module

    return filename, int(line_no)


def _get_stack(frame):
    frames = []
    while frame:
        frames += [frame]
        frame = frame.f_back
    return frames


def calling_function_logger(func_name):
    func_name = func_name.split('.')

    while func_name:
        if '.'.join(func_name) in sys.modules:
            return logging.getLogger('.'.join(func_name))
        func_name = func_name[:-1]


def caller_name(start=2):
    """
    This function creates a `"."` separated name for where the call is being
    made from\to. an example would be `"some_library.some_module"`

    This function also handles nested functions and classes alike.
    """
    # noinspection PyProtectedMember
    stack = _get_stack(sys._getframe(1))

    def get_name(s):
        if len(stack) < s + 1:
            return []
        parent_frame = stack[s]

        name = []
        module = inspect.getmodule(parent_frame)
        if module:
            name.append(module.__name__)

        codename = parent_frame.f_code.co_name
        if codename not in ('<module>', '__main__'):  # top level usually
            frame = parent_frame
            if 'self' in frame.f_locals:
                name.append(frame.f_locals['self'].__class__.__name__)
                name.append(codename)  # function or a method
            else:
                name.append(codename)  # function or a method
                frame = frame.f_back
                while codename in frame.f_locals:
                    codename = frame.f_code.co_name
                    if codename in ('<module>', '__main__'):
                        break
                    name.append(codename)
                    frame = frame.f_back

        del parent_frame
        return name

    res = get_name(start)

    if not res or 'pydev_run_in_console' in res:
        res = get_name(start - 1)

    if res == ['<module>'] or res == ['__main__']:
        res = get_name(start - 1)
        if 'log_it' in res:
            res = get_name(start)

    if 'wrapper' in res:
        res = get_name(start + 1) + get_name(start - 1)[-1:]

    return ".".join(res)


def func_arg_string(func, args, kwargs):
    """
    Gets a functions/methods arguments. This includes the parameter names as well as the default (if any)
    """

    if PY3:
        # noinspection PyUnresolvedReferences
        arg_names = inspect.getfullargspec(func)[0]
    else:
        # noinspection PyDeprecation
        arg_names = inspect.getargspec(func)[0]

    start = 0
    if arg_names:
        if arg_names[0] == "self":
            start = 1

    res = []
    append = res.append

    for key, value in list(zip(arg_names, args))[start:]:
        append(str(key) + "=" + repr(value).replace('.<locals>.', '.'))

    for key, value in kwargs.items():
        append(str(key) + "=" + repr(value).replace('.<locals>.', '.'))

    return "(" + ", ".join(res) + ")"

