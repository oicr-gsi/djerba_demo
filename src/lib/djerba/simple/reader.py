"""Read input data for Djerba"""

import json
import jsonschema
from djerba.simple.containers import gene, sample

class reader:
    """
    Parent class for Djerba data readers.

    Subclasses need to:
    - Read data
    - Store it in gene and sample objects
    - Use the objects to update self.genes and self.sample_info
    """

    GENE_METRICS_KEY = 'gene_metrics'
    GENE_NAME_KEY = 'Gene'
    ITEMS_KEY = 'items'
    PROPERTIES_KEY = 'properties'
    REVIEW_STATUS_KEY = 'review_status'
    SAMPLE_INFO_KEY = 'sample_info'
    SAMPLE_NAME_KEY = 'sample_name'

    def __init__(self, config, schema):
        """Constructor for superclass; should be called in all subclass constructors"""
        self.config = config
        self.schema = schema
        self.genes = {} # gene name -> gene object
        self.sample_info = None  # sample object

    def get_genes_list(self):
        return list(self.genes.values())

    def get_output(self):
        """
        Get final output, ready to be written as JSON
        """
        if not self.is_complete():
            raise RuntimeError("Refusing to generate output from incomplete Djerba reader")
        output = {}
        output[self.GENE_METRICS_KEY] = [x.get_attributes() for x in self.genes.values()]
        output[self.REVIEW_STATUS_KEY] = -1
        output[self.SAMPLE_INFO_KEY] = self.sample_info.get_attributes()
        output[self.SAMPLE_NAME_KEY] = self.sample_info.get_name()
        jsonschema.validate(output, self.schema)
        return output

    def get_sample_info(self):
        return self.sample_info

    def is_complete(self):
        complete = True
        for gene in self.genes.values():
            if not gene.is_complete():
                complete = False
                break
        if complete: # all genes are OK, check the sample
            complete = self.sample_info.is_complete()
        return complete

    def total_genes(self):
        return len(self.genes)

    def update_multiple_genes(self, new_genes):
        # input an array of gene objects
        for new_gene in new_genes:
            self.update_single_gene(new_gene)

    def update_single_gene(self, new_gene):
        # input a single gene object
        name = new_gene.get_name()
        if name == None:
            raise RunTimeError("Gene name is required")
        elif name in self.genes:
            self.genes[name].update(new_gene)
        else:
            self.genes[name] = new_gene

    def update_sample_info(self, sample_info):
        # update with a sample info object
        if self.sample_info == None:
            self.sample_info = sample_info
        else:
            self.sample_info.update(sample_info)

class multiple_reader(reader):
    """Create a list of single_reader objects; read data; collate into JSON report"""

    def __init__(self, config, schema):
        super().__init__(config, schema)
        self.factory = reader_factory()
        self.read_all()

    def read_all(self):
        """Similarly to single_reader, this is called as part of the constructor"""
        for single_config in self.config: # array of reader configuration objects
            reader = self.factory.create_instance(single_config, self.schema)
            self.update_sample_info(reader.get_sample_info())
            self.update_multiple_genes(reader.get_genes_list())

class single_reader(reader):
    """Read a single data source with parameters in config, using a read() method"""

    def __init__(self, config, schema):
        super().__init__(config, schema)
        self.read()

class json_reader(single_reader):
    """
    Reader for JSON data.
    Supply input as JSON, as default/fallback if other sources not available
    """

    def read(self):
        """
        Similarly to multiple_reader, this is called as part of the constructor
        """
        for attributes in self.config.get(self.GENE_METRICS_KEY):
            self.update_single_gene(gene(attributes, self.schema))
        sample_attributes = self.config.get(self.SAMPLE_INFO_KEY)
        self.update_sample_info(sample(sample_attributes, self.schema))

class reader_factory:
    """Given the config, construct a reader of the appropriate subclass"""

    READER_CLASS_KEY = "reader_class"

    def __init__(self):
        pass

    def create_instance(self, config, schema):
        """
        Return an instance of the reader class named in the config
        Config is a dictionary with a reader_class name, plus other parameters as needed
        """
        classname = config.get(self.READER_CLASS_KEY)
        if classname == None:
            msg = "Unknown or missing %s value in config. " % self.READER_CLASS_KEY
            #self.logger.error(msg)
            raise ValueError(msg)
        klass = globals().get(classname)
        #self.logger.debug("Created instance of %s" % classname)
        return klass(config, schema)
