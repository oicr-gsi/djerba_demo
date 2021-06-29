"""
Publish Djerba results in human-readable format.
Wrap an Rmarkdown script to output HTML from a Djerba results directory.
"""

import os
import pdfkit
import subprocess
import djerba.util.ini_fields as ini

class html_renderer:

    R_MARKDOWN_DIRNAME = 'R_markdown'

    def __init__(self, config):
        self.r_script_dir = config[ini.SETTINGS].get(ini.R_SCRIPT_DIR)
        if not self.r_script_dir:
            self.r_script_dir = os.path.join(os.path.dirname(__file__), self.R_MARKDOWN_DIRNAME)
        self.markdown_script = os.path.join(self.r_script_dir, 'html_report.Rmd')

    def run(self, report_dir, out_path):
        """Read the reporting directory, and use the Rmarkdown script to write HTML"""
        # no need for double quotes around the '-e' argument; subprocess does not use a shell
        render = "rmarkdown::render('{0}', output_file = '{1}')".format(self.markdown_script, out_path)
        cmd = [
            'Rscript', '-e',
            render,
            report_dir
        ]
        print('###', ' '.join(cmd))
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode!=0:
            print('###', result.stderr.decode('utf-8'))
            raise subprocess.CalledProcessError
        return result

class pdf_renderer:

    def __init__(self, config):
        # input config for consistency with other classes, and later for logging params etc.
        self.config = config

    def run(self, html_path, pdf_path):
        """Render HTML to PDF"""
        #create options, which are arguments to wkhtmltopdf for footer generation
        print('### placeholder; PDF renderer still in development')
        options = {
            'footer-right': '[page] of [topage]',
            'footer-left': '[date]',
            'footer-center': '${ANALYSIS_UNIT}' # TODO ensure env variable is present
        }
        #pdfkit.from_url(html_path, pdf_path, options = options)
