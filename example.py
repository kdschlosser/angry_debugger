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
:synopsis: example use

.. moduleauthor:: Kevin Schlosser @kdschlosser <kevin.g.schlosser@gmail.com>
"""
from __future__ import print_function
import random
from angry_debugger import log_it, LEVEL_ANGRY, start_logging_run, end_logging_run
import logging
import threading
import time


FORMAT = '%(asctime)-15s - %(message)s'
logging.basicConfig(level=LEVEL_ANGRY, format=FORMAT)
logger = logging.getLogger(__name__)

t_lock = threading.Lock()

multi_thread_run = False
@log_it
def function_test_1():
    if multi_thread_run:
        function_test_2()
        function_test_3()


def function_test_2():
    time.sleep(random.randrange(9) / 10.0)
    with t_lock:
        print('function_test_2 thread name: ' + threading.current_thread().getName())
    function_test_3()


def function_test_3():
    @log_it
    def function_test_4():
        pass

    function_test_4()


class SomeClass(object):
    some_attribute = log_it('some_attribute example')

    def __init__(self):
        pass

    @log_it
    @property
    def property_test_1(self):
        time.sleep(random.randrange(9) / 10.0)

        if multi_thread_run:
            _ = self.property_test_2
            _ = self.property_test_3
            _ = self.property_test_4

        return 'This is the property_test_1 getter'

    @property_test_1.setter
    def property_test_1(self, value):
        if multi_thread_run:
            self.property_test_2 = value
            self.property_test_3 = value
            self.property_test_4 = value

    @property_test_1.deleter
    def property_test_1(self):
        if multi_thread_run:
            del self.property_test_2
            del self.property_test_3
            del self.property_test_4

            _ = self.some_attribute
            self.some_attribute = 'setting some_attribute'

    @property
    def property_test_2(self):
        return 'This is the property_test_2 getter'

    @log_it
    @property_test_2.setter
    def property_test_2(self, value):
        time.sleep(random.randrange(9) / 10.0)
        with t_lock:
            print('property_test_2 setter thread name: ' + threading.current_thread().getName())
        pass

    @property_test_2.deleter
    def property_test_2(self):
        time.sleep(random.randrange(9) / 1000.0)
        pass

    @property
    def property_test_3(self):
        return 'This is the property_test_3 getter'

    @property_test_3.setter
    def property_test_3(self, value):
        time.sleep(random.randrange(9) / 1000.0)
        pass

    @log_it
    @property_test_3.deleter
    def property_test_3(self):
        time.sleep(random.randrange(9) / 1000000.0)
        pass

    @log_it
    @property
    def property_test_4(self):
        time.sleep(random.randrange(9) / 10.0)
        with t_lock:
            print('property_test_4 getter thread name: ' + threading.current_thread().getName())

        return 'This is the property_test_4 getter'

    @log_it
    @property_test_4.setter
    def property_test_4(self, value):
        time.sleep(0.1)
        pass

    @log_it
    @property_test_4.deleter
    def property_test_4(self):
        time.sleep(random.randrange(9) / 1000.0)
        pass

    @log_it
    def method_test_1(self, arg, default_arg='This is a default arg'):
        time.sleep(random.randrange(9) / 10000000.0)
        if multi_thread_run:
            self.method_test_2('some_argument')

    def method_test_2(self, arg, default_arg='This is a default arg'):
        @log_it
        def method_test_3():
            time.sleep(random.randrange(9) / 10.0)
            pass

        method_test_3()


threads = [threading.current_thread()]
event = threading.Event()
event.set()


def do():
    event.wait()
    some_class = SomeClass()

    if multi_thread_run:
        start_logging_run()

        function_test_1()
        time.sleep(random.randrange(2) / 10.0)
        _ = some_class.property_test_1
        some_class.property_test_1 = 'Some Value'

        del some_class.property_test_1

        some_class.method_test_1('argument 1')
        end_logging_run()

    else:
        function_test_1()
        function_test_2()
        _ = some_class.property_test_1
        some_class.property_test_1 = 'Some Value'

        del some_class.property_test_1

        _ = some_class.property_test_2
        some_class.property_test_2 = 'Some Value'

        del some_class.property_test_2

        _ = some_class.property_test_3
        some_class.property_test_3 = 'Some Value'

        del some_class.property_test_3

        _ = some_class.property_test_4
        some_class.property_test_4 = 'Some Value'

        del some_class.property_test_4

        _ = some_class.some_attribute
        some_class.some_attribute = 'setting some_attribute single thread'

        some_class.method_test_1('argument 1')
        some_class.method_test_2('argument 2')

    threads.remove(threading.current_thread())


do()

event.clear()
multi_thread_run = True

for _ in range(5):
    t = threading.Thread(target=do)
    t.daemon = True
    t.start()
    threads += [t]

threads += [threading.current_thread()]
event.set()
do()

while threads:
    pass
