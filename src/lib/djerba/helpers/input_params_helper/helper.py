"""
Helper for writing a subset of file provenance to the shared workspace

Outputs to the workspace:
- Subset of sample provenance for the donor and study supplied by the user
- JSON file with donor, study, and sample names

Plugins can then create their own provenance reader objects using params in the JSON, to
find relevant file paths. Reading the provenance subset is very much faster than reading 
the full file provenance report.
"""

import csv
import gzip
import logging
import djerba.core.constants as core_constants
import djerba.util.ini_fields as ini  # TODO new module for these constants?
import djerba.util.provenance_index as index
from djerba.helpers.base import helper_base
from djerba.util.provenance_reader import provenance_reader, sample_name_container, \
    InvalidConfigurationError

class main(helper_base):

    # Required parameter names for INI
    DONOR = 'donor'
    STUDY = 'study'
    PROJECT = 'project'
    TUMOUR_ID = 'tumour_id'
    NORMAL_ID = 'normal_id'

    # Name for output file
    INPUT_PARAMS_FILE = 'input_params.json'
    
    # Priority
    PRIORITY = 10


    def specify_params(self):
        self.logger.debug("Specifying params for input params helper")
        self.set_priority_defaults(self.PRIORITY)

        # All required parameters for input (i.e. from dimsum, req)
        self.add_ini_required(self.DONOR)
        self.add_ini_required(self.PROJECT)
        self.add_ini_required(self.STUDY)
        self.add_ini_required(self.TUMOUR_ID)
        self.add_ini_required(self.NORMAL_ID)

    def configure(self, config):
        """
        """
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        return wrapper.get_config()

    def extract(self, config):
        """
        Write the input params JSON
        """
        self.validate_full_config(config)
        #wrapper = self.get_config_wrapper(config)

        # Retrieve the parameters from the ini
        info = self.get_input_params(config)

        # Write them to a json
        self.write_input_params_info(info)

    def get_input_params(self, config):
        """
        Retrieves values from INI and puts them in a JSON
        """
        input_params_info = {
            
            self.DONOR: config[self.identifier][self.DONOR],
            self.STUDY: config[self.identifier][self.STUDY],
            self.PROJECT: config[self.identifier][self.PROJECT],
            self.TUMOUR_ID: config[self.identifier][self.TUMOUR_ID],
            self.NORMAL_ID: config[self.identifier][self.NORMAL_ID]
        }
        return input_params_info

    def write_input_params_info(self, input_params_info):
        self.workspace.write_json(self.INPUT_PARAMS_FILE, input_params_info)
        self.logger.debug("Wrote sample info to workspace: {0}".format(input_params_info))
