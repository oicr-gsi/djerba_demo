"""Djerba plugin for pwgs supplement"""
import logging
import os
from djerba.plugins.base import plugin_base, DjerbaPluginError
import djerba.core.constants as core_constants
from djerba.util.render_mako import mako_renderer
import djerba.util.input_params_tools as input_params_tools

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 1000
    MAKO_TEMPLATE_NAME = 'supplementary_materials_template.html'
    SUPPLEMENT_DJERBA_VERSION = 0.1
    ASSAY = "assay"
    
    def specify_params(self):
        discovered = [
            self.ASSAY
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper.set_my_priorities(self.DEFAULT_CONFIG_PRIORITY)
        workspace = self.workspace

        # Get input_data.json if it exists; else return None
        input_data = input_params_tools.get_input_params_json(workspace)
        
        if wrapper.my_param_is_null(self.ASSAY):
            wrapper.set_my_param(self.ASSAY, input_data[self.ASSAY])
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        #TO DO: add a check that assay type is a permitted value
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
            'merge_inputs': {},
            'results': {
                'assay': config[self.identifier][self.ASSAY]
            },
            'version': str(self.SUPPLEMENT_DJERBA_VERSION)
        }
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)
