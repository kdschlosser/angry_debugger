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
:synopsis: setup program

.. moduleauthor:: Kevin Schlosser @kdschlosser <kevin.g.schlosser@gmail.com>
"""

from distutils.core import setup


setup(
    name='angry_debugger',
    author='Kevin Schlosser',
    version='0.1.0',
    url='https://github.com/kdschlosser/angry_debugger',
    packages=['angry_debugger'],
    description=(
        'debug logging decorator'
    )
)

