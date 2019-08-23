# This file is part of pex_config.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import lsst.utils.tests
import lsst.pex.config as pexConf
import lsst.utils


class Config1(pexConf.Config):
    f = pexConf.Field("Config1.f", float, default=4)


class Config2(pexConf.Config):
    r = pexConf.ConfigChoiceField("Config2.r", {"c1": Config1}, default="c1")


class Config3(pexConf.Config):
    c = pexConf.ConfigField("Config3.c", Config2)


class FieldNameReportingTest(unittest.TestCase):
    def test(self):
        c3 = Config3()
        pex_product_dir = lsst.utils.getPackageDir('pex_config')
        c3.load(pex_product_dir + "/tests/config/ticket1914.py")


class TestMemory(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
