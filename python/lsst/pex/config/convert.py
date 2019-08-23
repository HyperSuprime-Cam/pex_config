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

__all__ = ('makePropertySet', 'makePolicy')

import lsst.pex.policy
import lsst.daf.base


def makePropertySet(config):
    """Convert a configuration into a `lsst.daf.base.PropertySet`.

    Parameters
    ----------
    config : `lsst.pex.config.Config`
        Configuration instance.

    Returns
    -------
    propertySet : `lsst.daf.base.PropertySet`
        A `~lsst.daf.base.PropertySet` that is equivalent to the ``config``
        instance. If ``config`` is `None` then this return value is also
        `None`.

    See also
    --------
    makePolicy
    lsst.daf.base.PropertySet
    """
    def _helper(ps, prefix, dict_):
        for k, v in dict_.items():
            name = prefix + "." + k if prefix is not None else k
            if isinstance(v, dict):
                _helper(ps, name, v)
            elif v is not None:
                ps.set(name, v)

    if config is not None:
        ps = lsst.daf.base.PropertySet()
        _helper(ps, None, config.toDict())
        return ps
    else:
        return None


def makePolicy(config):
    """Convert a configuration into a `lsst.pex.policy.Policy`.

    Parameters
    ----------
    config : `lsst.pex.config.Config`
        Configuration instance.

    Returns
    -------
    policy : `lsst.pex.policy.Policy`
        A `~lsst.pex.policy.Policy` that is equivalent to the ``config``
        instance. If ``config`` is `None` then return value is also `None`.

    See also
    --------
    makePropertySet
    lsst.pex.policy.Policy
    """
    def _helper(dict_):
        p = lsst.pex.policy.Policy()
        for k, v in dict_.items():
            if isinstance(v, dict):
                p.set(k, _helper(v))
            elif isinstance(v, list):
                for vi in v:
                    p.add(k, vi)
            elif v is not None:
                p.set(k, v)
        return p
    if config:
        return _helper(config.toDict())
    else:
        return None
