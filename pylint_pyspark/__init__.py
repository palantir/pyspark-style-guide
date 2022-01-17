"""pylint_django module."""
from __future__ import absolute_import

import sys

from pylint_django import plugin

if sys.version_info < (3,):
    raise DeprecationWarning("Version 0.11.1 was the last to support Python 2. " "Please migrate to Python 3!")

register = plugin.register  # pylint: disable=invalid-name
load_configuration = plugin.load_configuration  # pylint: disable=invalid-name