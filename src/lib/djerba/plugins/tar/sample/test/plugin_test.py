#! /usr/bin/env python3

"""
Test of the pwgs plugin
AUTHOR: Felix Beaudry
"""

import os
import unittest
import tempfile

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.tar.sample.plugin as sample
from djerba.core.workspace import workspace

class TestTarSamplePlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testTarSample(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"tar-plugin/report_json/tar.sample.json")
        params = {
            self.INI: 'tar.sample.ini',
            self.JSON: json_location,
            self.MD5: 'f8763747e45463c8163a8fe6d6c1956a'
        }
        self.run_basic_test(test_source_dir, params)

    def test_process_ichor_json(self):
        ichor_expected_location = os.path.join(self.sup_dir ,"tar-plugin/ichorCNA_metrics.json")
        ichor_json = sample.main.process_ichor_json(self, ichor_expected_location)
        purity = ichor_json["tumor_fraction"]
        self.assertEqual(purity, 0.03978)

    def test_process_consensus_cruncher(self):
        cc_expected_location = os.path.join(self.sup_dir ,"tar-plugin/allUnique-hsMetrics.HS.txt")
        unique_coverage = sample.main.process_consensus_cruncher(self, cc_expected_location)
        self.assertEqual(unique_coverage, 2088)

if __name__ == '__main__':
    unittest.main()
