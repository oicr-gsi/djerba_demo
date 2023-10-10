#! /usr/bin/env python3

"""
Test of the WGTS CNV plugin
"""

import os
import string
import tempfile
import unittest
from shutil import copy
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.plugins.cnv.plugin import main as cnv
from djerba.core.workspace import workspace

class TestWgtsCnv(PluginTester):

    INI_NAME = 'cnv.ini'
    JSON_NAME = 'cnv.json'

    def testWgtsCnv(self):
        sup_dir = os.environ.get('DJERBA_TEST_DATA')
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(sup_dir, "plugins/cnv/cnv.json")
        sequenza_filename = 'OCT_011488_Lu_M_WG_OCT_011488-TS_results.gamma400.zip'
        sequenza_path = os.path.join(sup_dir, 'plugins', 'cnv', sequenza_filename)
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'SEQUENZA_PATH': sequenza_path})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        copy(os.path.join(test_source_dir, self.JSON_NAME), input_dir)
        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.JSON_NAME,
            self.MD5: 'e8d5c9777e4dbd6162105cd189cb40bf'
        }
        self.run_basic_test(input_dir, params)

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        del data['plugins']['wgts.cnv']['results']['cnv_plot']
        return data 

if __name__ == '__main__':
    unittest.main()
