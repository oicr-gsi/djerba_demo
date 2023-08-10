"""
The purpose of this file is deal with pre-processing necessary files for the SWGS plugin.
They're in a separate file because the pre-processing is a little more complex.
AUTHOR: Aqsa Alam
"""

# IMPORTS
import os
import csv
import gzip
import logging
import pandas as pd
from djerba.util.logger import logger
from djerba.sequenza import sequenza_reader
from djerba.util.subprocess_runner import subprocess_runner
from djerba.extract.oncokb.annotator import oncokb_annotator
from shutil import copyfile
import djerba.plugins.tar.swgs.constants as constants 

class preprocess:

  # FOR TESTING
  #tumour_id = "100-PM-064_LCM3"
  #oncotree_code = "paad"
  #seg_file = "REVOLVE_0002_01_LB04-01.seg.txt"

  def __init__(self, config, work_dir, seg_file):

    self.config = config
    # DIRECTORIES
    self.work_dir = work_dir
    self.tmp_dir = os.path.join(self.work_dir, 'tmp')
    if os.path.isdir(self.tmp_dir):
        print("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
        #self.logger.debug("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
    elif os.path.exists(self.tmp_dir):
        msg = "tmp dir path {0} exists but is not a directory".format(self.tmp_dir)
        #self.logger.error(msg)
        raise RuntimeError(msg)
    else:
        #print("Creating tmp dir {0} for R script wrapper".format(tmp_dir))
        #self.logger.debug("Creating tmp dir {0} for R script wrapper".format(self.tmp_dir))
        os.mkdir(self.tmp_dir)
    self.r_script_dir = os.environ.get('DJERBA_BASE_DIR') + "/plugins/tar/Rscripts"
    self.r_script_dir_swgs = os.environ.get('DJERBA_BASE_DIR') + "/plugins/tar/swgs/" 
    self.data_dir = os.environ.get('DJERBA_BASE_DIR') + "/data/"
    self.tumour_id = self.config['tar.snv_indel']['tumour_id']
    self.oncotree_code = self.config['tar.snv_indel']['oncotree_code']

    # SEG FILE

    self.seg_file = seg_file 

    # RANDOM
    self.cache_params = None
    self.log_level = "logging.WARNING"
    self.log_path = "None"
  

  # ----------------------- to do all the pre-processing --------------------
    
    
  def run_R_code(self):
    seg_path = self.preprocess_seg(self.seg_file)

    cmd = [
        'Rscript', self.r_script_dir_swgs + "/process_CNA_data.r",
        '--basedir', self.r_script_dir,
        '--outdir', self.work_dir,
        '--segfile', seg_path,
        '--genebed', "/.mounts/labs/gsi/modulator/sw/Ubuntu18.04/djerba-0.4.8/lib/python3.10/site-packages/djerba/data/gencode_v33_hg38_genes.bed",
        '--oncolist', self.data_dir + "/20200818-oncoKBcancerGeneList.tsv"
    ]

    runner = subprocess_runner()
    result = runner.run(cmd, "main R script")
    self.postprocess()
    return result

 
  def preprocess_seg(self, seg_file):
    """
    Filter for amplifications.
    """
    seg_path =  os.path.join(self.seg_file)
    # Create a dataframe so we can filter by amplifications only...or in this case, by gain only for testing.
    df_seg = pd.read_csv(seg_path, sep = '\t')
    df_seg = df_seg[df_seg["call"].str.contains("AMP|HLAMP") == True]

    # Delete the seg.mean column, and rename the Corrected_Copy_Number column to seg.mean
    df_seg = df_seg.drop(columns = "seg.median.logR")
    df_seg = df_seg.rename(columns={"Corrected_Copy_Number": "seg.mean"})
    df_seg = df_seg.rename(columns={"start": "loc.start"})
    df_seg = df_seg.rename(columns={"end": "loc.end"})

    # Convert the dataframe back into a tab-delimited text file.
    out_path = os.path.join(self.work_dir, 'seg_amplifications.txt')
    df_seg.to_csv(out_path, sep = '\t', index=None)

    return out_path


  def postprocess(self):
     """
    Annotate CNA data
     """
     annotator = oncokb_annotator(
            self.tumour_id,
            self.oncotree_code,
            self.work_dir,
            self.tmp_dir,
            self.cache_params,
     )
     annotator.annotate_cna()
