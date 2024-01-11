#! /usr/bin/env python3

"""Test of the pwgs plugin"""

import os
import unittest
import tempfile
import string

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.pwgs.sample.plugin as sample
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools
from djerba.core.workspace import workspace
import djerba.plugins.pwgs.constants as constants

class TestPwgSamplePlugin(PluginTester):

    INI_NAME = 'pwgs.sample.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testPreprocessSNVcount(self):
        snv_count_expected_location = os.path.join(self.sup_dir ,"plugins/pwgs/snv.txt")
        snv_count = sample.main.preprocess_snv_count(self, snv_count_expected_location)
        self.assertEqual(snv_count, 21000)

    def testPwgsSample(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.sup_dir ,"plugins/pwgs/report_json/pwgs.sample.json")
        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '29d7af558da3aced6116ef8ec740f716'
        }
        self.run_basic_test(input_dir, params)

    #TODO: add fetch_coverage_etl_data test


if __name__ == '__main__':
    unittest.main()
