#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import os
import inspect
import unittest
from obspy import readEvents
from obspy.core.util import NamedTemporaryFile
from obspy.cnv.core import write_CNV


class CNVTestCase(unittest.TestCase):
    """
    Test suite for obspy.cnv
    """
    def setUp(self):
        self.path = os.path.dirname(os.path.abspath(inspect.getfile(
            inspect.currentframe())))
        self.datapath = os.path.join(self.path, "data")

    def test_write_cnv(self):
        """
        Test writing CNV catalog summary file.
        """
        # load QuakeML file to generate CNV file from it
        filename = os.path.join(self.datapath, "obspyck_20141020150701.xml")
        cat = readEvents(filename, format="QUAKEML")

        # read expected OBS file output
        filename = os.path.join(self.datapath, "obspyck_20141020150701.cnv")
        with open(filename, "rb") as fh:
            expected = fh.read().decode()

        # write via plugin
        with NamedTemporaryFile() as tf:
            cat.write(tf, format="CNV")
            tf.seek(0)
            got = tf.read().decode()

        self.assertEqual(expected, got)

        # write manually
        with NamedTemporaryFile() as tf:
            write_CNV(cat, tf)
            tf.seek(0)
            got = tf.read().decode()

        self.assertEqual(expected, got)


def suite():
    return unittest.makeSuite(CNVTestCase, "test")


if __name__ == "__main__":
    unittest.main(defaultTest="suite")
