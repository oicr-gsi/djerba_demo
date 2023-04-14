"""
Main class to:
- Generate the core report elements
- Import and run plugins
- Merge and output results
"""
from configparser import ConfigParser
import logging
import json
import djerba.util.ini_fields as ini
from djerba.core.configure import configurer as core_configurer
from djerba.core.extract import extractor as core_extractor
from djerba.core.json_validator import plugin_json_validator
from djerba.core.render import renderer as core_renderer
from djerba.core.loaders import plugin_loader, merger_loader
from djerba.core.workspace import workspace
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class main(logger):

    # TODO move to constants file(s)
    COMPONENT_ORDER = 'component_order'
    PLUGINS = 'plugins'
    MERGERS = 'mergers'
    MERGE_INPUTS = 'merge_inputs'
    
    def __init__(self, work_dir, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.json_validator = plugin_json_validator(self.log_level, self.log_path)
        self.path_validator = path_validator(self.log_level, self.log_path)
        self.workspace = workspace(work_dir, self.log_level, self.log_path)
        self.plugin_loader = plugin_loader(self.log_level, self.log_path)
        self.merger_loader = merger_loader(self.log_level, self.log_path)

    def _order_html(self, header, body, footer, order):
        """
        'body' is a dictionary of strings for the body of the HTML document
        'order' is a list of component names (must include all components in data)
        """
        ordered_html = [header, ]
        if len(order)==0:
            msg = "Component order is empty, falling back to default order"
            self.logger.info(msg)
            ordered_html.extend(body.values())
        else:
            for name in order:
                # refer to merger/plugin list in core data and assemble outputs
                if name not in body:
                    msg = "Name {0} not found ".format(name)+\
                        "in user-specified component order {0}".format(order)
                    self.logger.error(msg)
                    raise ComponentNameError(msg)
                ordered_html.append(body[name])
        ordered_html.append(footer)
        return ordered_html

    def _run_merger(self, merger_name, data):
        """Assemble inputs for the named merger and run merge/dedup to get HTML"""
        merger_inputs = []
        for plugin_name in data[self.PLUGINS]:
            plugin_data = data[self.PLUGINS][plugin_name]
            if merger_name in plugin_data[self.MERGE_INPUTS]:
                merger_inputs.append(plugin_data[self.MERGE_INPUTS][merger_name])
        merger = self.merger_loader.load(merger_name)
        self.logger.debug("Loaded merger {0} for rendering".format(merger_name))
        return merger.render(merger_inputs)

    def configure(self, config_path_in, config_path_out=None):
        if config_path_out:  # do this *before* taking the time to generate output
            self.validator.validate_output_file(config_path_out)
        config_in = self.read_ini_path(config_path_in)
        # TODO first read defaults, then overwrite
        config_out = ConfigParser()
        for section_name in config_in.sections():
            if section_name == ini.CORE:
                configurer = core_configurer(self.log_level, self.log_path)
                config_out[section_name] = configurer.run(config_in[section_name])
                self.logger.debug("Updated core configuration")
            else:
                plugin_main = self.plugin_loader.load(section_name, self.workspace)
                self.logger.debug("Loaded plugin {0} for configuration".format(section_name))
                config_out[section_name] = plugin_main.configure(config_in[section_name])
        if config_path_out:
            with open(config_path_out, 'w') as out_file:
                config_out.write(out_file)
        return config_out

    def extract(self, config, json_path=None):
        if json_path:  # do this *before* taking the time to generate output
            self.validator.validate_output_file(json_path)
        data = core_extractor(self.log_level, self.log_path).run(config)
        # data includes an empty 'plugins' object
        for section_name in config.sections():
            if section_name != ini.CORE:
                plugin = self.plugin_loader.load(section_name, self.workspace)
                self.logger.debug("Loaded plugin {0} for extraction".format(section_name))
                plugin_data = plugin.extract(config[section_name])
                self.json_validator.validate_data(plugin_data)
                data[self.PLUGINS][section_name] = plugin_data
        if json_path:
            with open(json_path, 'w') as out_file:
                out_file.write(json.dumps(data))
        return data

    def render(self, data, html_path=None):
        if html_path:  # do this *before* taking the time to generate output
            self.path_validator.validate_output_file(html_path)
        [header, footer] = core_renderer(self.log_level, self.log_path).run(data)
        body = {} # strings to make up the body of the HTML document
        merger_names = set()
        for plugin_name in data[self.PLUGINS]:
            # render plugin HTML, and find which mergers it uses
            plugin_data = data[self.PLUGINS][plugin_name]
            plugin = self.plugin_loader.load(plugin_name, self.workspace)
            self.logger.debug("Loaded plugin {0} for rendering".format(plugin_name))
            body[plugin_name] = plugin.render(plugin_data)
            for name in plugin_data[self.MERGE_INPUTS]:
                merger_names.add(name)
        for merger_name in merger_names:
            if merger_name in body:
                msg = "Plugin/merger name conflict: {0}".format(name)
                self.logger.error(msg)
                raise ComponentNameError(msg)
            merged_html = self._run_merger(merger_name, data)
            body[merger_name] = merged_html
        order = data[ini.CORE][self.COMPONENT_ORDER]
        ordered_html = self._order_html(header, body, footer, order)
        html = "\n".join(ordered_html)
        if html_path:
            with open(html_path, 'w') as out_file:
                out_file.write(html)
        return html

    def read_ini_path(self, ini_path):
        self.path_validator.validate_input_file(ini_path)
        config = ConfigParser()
        config.read(ini_path)
        return config

    # TODO write a run() method to:
    # - convert command-line args to appropriate inputs
    # - run configure/extract/render as required
    # - Do PDF conversion
    def run(self, args):
        pass

class ComponentNameError(Exception):
    pass

import sys

if __name__ == '__main__':
    djerba_main = main(logging.DEBUG)
    config = djerba_main.configure(sys.argv[1])
    data = djerba_main.extract(config)
    with open(sys.argv[2], 'w') as out_file:
        out_file.write(json.dumps(data, indent=4, sort_keys=True))
    html = djerba_main.render(data)
    print(html)
