"""
The purpose of this file is deal with pre-processing necessary files for the SNV Indel plugin.
They're in a separate file because the pre-processing is a little more complex.
"""

# IMPORTS
import os
import re
import csv
import gzip
import logging
from djerba.util.logger import logger
from djerba.sequenza import sequenza_reader
from djerba.util.subprocess_runner import subprocess_runner
from djerba.extract.oncokb.annotator import oncokb_annotator
from shutil import copyfile
import djerba.snv_indel_tools.constants as constants 
from djerba.plugins.base import plugin_base
import pandas as pd

class preprocess():
 
  
  cache_params = None
  log_level = "logging.WARNING"
  log_path = "None"
  
  GENE_ID = 0
  FPKM = 6
  gep_reference = "/.mounts/labs/CGI/gsi/tools/djerba/gep_reference.txt.gz"
  
  # headers of important MAF columns
  VARIANT_CLASSIFICATION = 'Variant_Classification'
  TUMOUR_SAMPLE_BARCODE = 'Tumor_Sample_Barcode'
  MATCHED_NORM_SAMPLE_BARCODE = 'Matched_Norm_Sample_Barcode'
  FILTER = 'FILTER'
  T_DEPTH = 't_depth'
  T_ALT_COUNT = 't_alt_count'
  GNOMAD_AF = 'gnomAD_AF'
  MAF_KEYS = [
      VARIANT_CLASSIFICATION,
      TUMOUR_SAMPLE_BARCODE,
      MATCHED_NORM_SAMPLE_BARCODE,
      FILTER,
      T_DEPTH,
      T_ALT_COUNT,
      GNOMAD_AF
  ]

  # Permitted MAF mutation types
  # `Splice_Region` is *included* here, but *excluded* from the somatic mutation count used to compute TMB in report_to_json.py
  # See also JIRA ticket GCGI-469
  MUTATION_TYPES_EXONIC = [
      "3'Flank",
      "3'UTR",
      "5'Flank",
      "5'UTR",
      "Frame_Shift_Del",
      "Frame_Shift_Ins",
      "In_Frame_Del",
      "In_Frame_Ins",
      "Missense_Mutation",
      "Nonsense_Mutation",
      "Nonstop_Mutation",
      "Silent",
      "Splice_Region",
      "Splice_Site",
      "Targeted_Region",
      "Translation_Start_Site"
  ]

  # disallowed MAF filter flags; from filter_flags.exclude in CGI-Tools
  FILTER_FLAGS_EXCLUDE = [
      'str_contraction',
      't_lod_fstar'
  ]

  # MAF filter thresholds
  MIN_VAF = 0.1
  MIN_VAF_TAR = 0.01
  MAX_UNMATCHED_GNOMAD_AF = 0.001


  def __init__(self, config, work_dir, tar):
      self.config = config
      self.report_dir = work_dir
      self.tmp_dir = os.path.join(self.report_dir, 'tmp')
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
      self.report_dir = work_dir
      #self.r_script_dir = os.environ.get('DJERBA_BASE_DIR') + "/plugins/tar/Rscripts/"
      self.tar = tar
       
      # THINGS FROM CONFIG 
      if self.tar == True:
          self.seg_file = self.config['tar.swgs']['seg_file']
          self.oncotree_code = self.config['tar.snv_indel']['oncotree_code']
          self.tcgacode = self.config['tar.snv_indel']['tcgacode']
          self.tumour_id = self.config['tar.snv_indel']['tumour_id']
          self.maf_file = self.config['tar.snv_indel']['maf_file']
          self.normal_id = self.config['tar.snv_indel']['normal_id']
          self.maf_file_normal = self.config['tar.snv_indel']['maf_file_normal']
          self.study_title = self.config['provenance_helper']['study_title']
      else:
          self.sequenza_path = self.config['snv_indel']['sequenza_file']
          self.sequenza_gamma = int(self.config['snv_indel']['sequenza_gamma'])
          self.sequenza_solution = self.config['snv_indel']['sequenza_solution']
          self.gep_file = self.config['snv_indel']['gep_file']
          self.oncotree_code = self.config['snv_indel']['oncotree_code']
          self.tcgacode = self.config['snv_indel']['tcgacode']
          self.tumour_id = self.config['snv_indel']['tumour_id']
          self.normal_id = self.config['snv_indel']['normal_id']
          self.maf_file = self.config['snv_indel']['maf_file']
          self.study_title = self.config['provenance_helper']['study_title']

      self.r_script_dir = os.environ.get('DJERBA_BASE_DIR') + "/snv_indel_tools/Rscripts/"
      

  # ----------------------- to do all the pre-processing --------------------
  
  def run_R_code(self):
  
    
    # FIX THIS BECAUSE THE ARATIO FILE IS DIFFERENT FOR TAR AND NONTAR
    if self.tar == True:
        maf_path = self.preprocess_maf(self.maf_file)

        cmd = [
         'Rscript', self.r_script_dir + "/process_data.r",
         '--basedir', self.r_script_dir,
         '--outdir', self.report_dir,
         '--whizbam_url', 'https://whizbam.oicr.on.ca',
         '--tumourid', self.tumour_id,
         '--normalid', self.normal_id,
         '--cbiostudy', self.study_title,
         '--maffile', maf_path,
         '--tar', 'TRUE'
        ]
   
    else:
        seg_path = self.preprocess_seg(self.sequenza_path)
        aratio_path = self.preprocess_aratio(self.sequenza_path, self.report_dir)
        gep_path = self.preprocess_gep(self.gep_file)
        maf_path = self.preprocess_maf(self.maf_file)
        cmd = [
            'Rscript', self.r_script_dir + "process_data.r",
            '--basedir', self.r_script_dir,
            '--outdir', self.report_dir,
            '--segfile', seg_path,
            '--genebed', "/.mounts/labs/gsi/modulator/sw/Ubuntu18.04/djerba-0.4.8/lib/python3.10/site-packages/djerba/data/gencode_v33_hg38_genes.bed",
            '--oncolist', os.environ.get('DJERBA_BASE_DIR') + "/data/20200818-oncoKBcancerGeneList.tsv",
            '--gain', "0.2529454648649786", # NEED TO GENERATE VALUES
            '--ampl', "0.6927983480061226", # NEED TO GENERATE VALUES
            '--htzd', "-0.3929375973235762", # NEED TO GENERATE VALUES
            '--hmzd', "-1.7148656922109384", # NEED TO GENERATE VALUES
            '--gepfile', gep_path,
            '--enscon', "/.mounts/labs/gsi/modulator/sw/Ubuntu18.04/djerba-0.4.8/lib/python3.10/site-packages/djerba/data/ensemble_conversion_hg38.txt", 
            '--genelist', "/.mounts/labs/gsi/modulator/sw/Ubuntu18.04/djerba-0.4.8/lib/python3.10/site-packages/djerba/data/targeted_genelist.txt",
            '--tcgadata', "/.mounts/labs/CGI/gsi/tools/RODiC/data",
            '--tcgacode', self.tcgacode,
            '--studyid', self.study_id,
            '--whizbam_url', 'https://whizbam.oicr.on.ca',
            '--tumourid', self.tumour_id,
            '--normalid', self.normal_id,
            '--cbiostudy', self.study_id, # NEEDS TO BE CBIOSTUDY ID
            '--maffile', maf_path,
            '--aratiofile', aratio_path,
            '--tar', 'FALSE'
        ]
    runner = subprocess_runner()
    result = runner.run(cmd, "main R script")
    self.postprocess()
    return result

  def preprocess_aratio(self, sequenza_path, report_dir):
    """
    Extract the appropriate _segments.txt file from the .zip archive output by Sequenza
    Copy the extracted file to report_dir
    """
    
    reader = sequenza_reader(sequenza_path)
    seg_path = reader.extract_segments_text_file(self.tmp_dir, self.sequenza_gamma, self.sequenza_solution)
    out_path = os.path.join(report_dir, 'aratio_segments.txt')
    copyfile(seg_path, out_path)
    return out_path
  
  def preprocess_seg(self, sequenza_path):
    """
    Extract the SEG file from the .zip archive output by Sequenza
    Apply preprocessing and write results to tmp_dir
    Replace entry in the first column with the tumour ID
    """

    seg_path = sequenza_reader(sequenza_path).extract_cn_seg_file(self.tmp_dir, self.sequenza_gamma)
    out_path = os.path.join(self.tmp_dir, 'seg.txt')
    with open(seg_path, 'rt') as seg_file, open(out_path, 'wt') as out_file:
        reader = csv.reader(seg_file, delimiter="\t")
        writer = csv.writer(out_file, delimiter="\t")
        in_header = True
        for row in reader:
            if in_header:
                in_header = False
            else:
                row[0] = self.tumour_id
            writer.writerow(row)
    return out_path
  
  def preprocess_gep(self, gep_path):
    """
    Apply preprocessing to a GEP file; write results to tmp_dir
    CGI-Tools constructs the GEP file from scratch, but only one column actually varies
    As a shortcut, we insert the first column into a ready-made file
    TODO This is a legacy CGI-Tools method, is there a cleaner way to do it?
    TODO Should GEP_REFERENCE (list of past GEP results) be updated on a regular basis?
    """
    # read the gene id and FPKM metric from the GEP file for this report
    fkpm = {}
    with open(gep_path) as gep_file:
        reader = csv.reader(gep_file, delimiter="\t")
        for row in reader:
            try:
                fkpm[row[self.GENE_ID]] = row[self.FPKM]
            except IndexError as err:
                msg = "Incorrect number of columns in GEP row: '{0}'".format(row)+\
                      "read from '{0}'".format(gep_path)
                #self.logger.error(msg)
                raise RuntimeError(msg) from err
    # insert as the second column in the generic GEP file
    ref_path = self.gep_reference
    out_path = os.path.join(self.tmp_dir, 'gep.txt')
    with \
         gzip.open(ref_path, 'rt', encoding=constants.TEXT_ENCODING) as in_file, \
         open(out_path, 'wt') as out_file:
        # preprocess the GEP file
        reader = csv.reader(in_file, delimiter="\t")
        writer = csv.writer(out_file, delimiter="\t")
        first = True
        for row in reader:
            if first:
                row.insert(1, self.tumour_id)
                first = False
            else:
                gene_id = row[0]
                try:
                    row.insert(1, fkpm[gene_id])
                except KeyError as err:
                    msg = 'Reference gene ID {0} from {1} '.format(gene_id, ref_path) +\
                        'not found in gep results path {0}'.format(gep_path)
                    #self.logger.warn(msg)
                    row.insert(1, '0.0')
            writer.writerow(row)
    return out_path



  def filter_maf_for_tar(self, maf_path):
    genes = ["BRCA2",
          "BRCA1",
          "PALB2",
          "TP53",
          "APC",
          "EPCAM",
          "PMS2",
          "MLH1",
          "MSH2",
          "MSH6",
          "ABCB1",
          "CCNE1"]

    df_bc = pd.read_csv(self.maf_file_normal,
                    sep = "\t",
                    on_bad_lines="error",
                    compression='gzip',
                    skiprows=[0],
                    index_col = 34)

    df_pl = pd.read_csv(maf_path,
                    sep = "\t",
                    on_bad_lines="error",
                    compression='gzip',
                    skiprows=[0])

    for row in df_pl.iterrows():
        hugo_symbol = row[1][0]
        hgvsp_short = row[1][34]
        #if hugo_symbol not in genes:
        #    df_pl = df_pl.drop(row[0])
        #else:
        try:
            if hgvsp_short in df_bc.index:
                df_pl.at[row[0], "n_depth"] = df_bc.loc[hgvsp_short]["n_depth"]
                df_pl.at[row[0], "n_ref_count"] = df_bc.loc[hgvsp_short]["n_ref_count"]
                df_pl.at[row[0], "n_alt_count"] = df_bc.loc[hgvsp_short]["n_alt_count"]
            else:
                df_pl.at[row[0], "n_depth"] = 0
                df_pl.at[row[0], "n_ref_count"] = 0
                df_pl.at[row[0], "n_alt_count"] = 0
                
        except:
            df_pl.at[row[0], "n_depth"] = 0
            df_pl.at[row[0], "n_ref_count"] = 0
            df_pl.at[row[0], "n_alt_count"] = 0
            
        if df_pl.loc[row[0]]["n_alt_count"] > 4 or df_pl.loc[row[0]]["gnomAD_AF"] > 0.001:
            df_pl = df_pl.drop(row[0])
    
    for row in df_pl.iterrows():
        hugo_symbol = row[1][0]
        if hugo_symbol not in genes:
            df_pl = df_pl.drop(row[0])   
     

    out_path = os.path.join(self.tmp_dir, 'filtered_maf_for_tar.maf.gz')
    df_pl.to_csv(out_path, sep = "\t", compression='gzip', index=False)
    return out_path
     
 
 

  def preprocess_maf(self, maf_path):
    """Apply preprocessing and annotation to a MAF file; write results to tmp_dir"""
    tmp_path = os.path.join(self.tmp_dir, 'tmp_maf.tsv')
    if self.tar:
        maf_path = self.filter_maf_for_tar(maf_path)
    #self.logger.info("Preprocessing MAF input")
    # find the relevant indices on-the-fly from MAF column headers
    # use this instead of csv.DictReader to preserve the rows for output
    with \
        gzip.open(maf_path, 'rt', encoding=constants.TEXT_ENCODING) as in_file, \
        open(tmp_path, 'wt') as tmp_file:
        # preprocess the MAF file
        reader = csv.reader(in_file, delimiter="\t")
        writer = csv.writer(tmp_file, delimiter="\t")
        in_header = True
        total = 0
        kept = 0
        for row in reader:
            if in_header:
                if re.match('#version', row[0]):
                    # do not write the version header
                    continue
                else:
                    # write the column headers without change
                    writer.writerow(row)
                    indices = self._read_maf_indices(row)
                    in_header = False
            else:
                total += 1
                if self.tar:
                    if self._maf_body_row_ok(row, indices, self.MIN_VAF_TAR):
                        # filter rows in the MAF body and update the tumour_id
                        row[indices.get(self.TUMOUR_SAMPLE_BARCODE)] = self.tumour_id
                        writer.writerow(row)
                        kept += 1
                else:
                    if self._maf_body_row_ok(row, indices, self.MIN_VAF):
                        # filter rows in the MAF body and update the tumour_id
                        row[indices.get(self.TUMOUR_SAMPLE_BARCODE)] = self.tumour_id
                        writer.writerow(row)
                        kept += 1
    #self.logger.info("Kept {0} of {1} MAF data rows".format(kept, total))
    # apply annotation to tempfile and return final output
    out_path = oncokb_annotator(
        self.tumour_id,
        self.oncotree_code,
        self.report_dir,
        self.tmp_dir
        #self.cache_params,
        #self.log_level,
        #self.log_path
    ).annotate_maf(tmp_path)
    return out_path

  def _maf_body_row_ok(self, row, ix, vaf_cutoff):
    """
    Should a MAF row be kept for output?
    Implements logic from functions.sh -> hard_filter_maf() in CGI-Tools
    Expected to filter out >99.9% of input reads
    ix is a dictionary of column indices
    """
    ok = False
    row_t_depth = int(row[ix.get(self.T_DEPTH)])
    alt_count_raw = row[ix.get(self.T_ALT_COUNT)]
    gnomad_af_raw = row[ix.get(self.GNOMAD_AF)]
    row_t_alt_count = float(alt_count_raw) if alt_count_raw!='' else 0.0
    row_gnomad_af = float(gnomad_af_raw) if gnomad_af_raw!='' else 0.0
    is_matched = row[ix.get(self.MATCHED_NORM_SAMPLE_BARCODE)] != 'unmatched'
    filter_flags = re.split(';', row[ix.get(self.FILTER)])
    if row_t_depth >= 1 and \
        row_t_alt_count/row_t_depth >= vaf_cutoff and \
        (is_matched or row_gnomad_af < self.MAX_UNMATCHED_GNOMAD_AF) and \
        row[ix.get(self.VARIANT_CLASSIFICATION)] in self.MUTATION_TYPES_EXONIC and \
        not any([z in self.FILTER_FLAGS_EXCLUDE for z in filter_flags]):
        ok = True
    return ok

  def _read_maf_indices(self, row):
    indices = {}
    for i in range(len(row)):
        key = row[i]
        if key in self.MAF_KEYS:
            indices[key] = i
    if set(indices.keys()) != set(self.MAF_KEYS):
        msg = "Indices found in MAF header {0} ".format(indices.keys()) +\
                "do not match required keys {0}".format(self.MAF_KEYS)
        #self.logger.error(msg)
        raise RuntimeError(msg)
    return indices

  def postprocess(self):
     """
     Apply postprocessing to the Rscript output directory
     - Annotate CNA and (if any) fusion data
     - Remove unnecessary files written by the R script
     - Remove the temporary directory if required
     """
     annotator = oncokb_annotator(
            self.tumour_id,
            self.oncotree_code,
            self.report_dir,
            self.tmp_dir,
            self.cache_params,
     )
     annotator.annotate_cna()
        #if self.cleanup:
        #    rmtree(self.tmp_dir)
        #    os.remove(os.path.join(self.report_dir, constants.DATA_CNA_ONCOKB_GENES))
