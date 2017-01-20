#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dataset builder tool.
Creates or converts between specific standards of datasets (like LMDB) and raw datasets.


Usage:
  dtb.py init <dataset_type> [--size=<WxH>] [--equalize-histogram] [--override-existing] [--description=<dataset_description>] [--metadata-file=<metadata_filename>]
  dtb.py add <resource-uri>...
  dtb.py size
  dtb.py lmdb export <lmdb_destination> <splits>... [--size=<WxH>] [--equalize-histogram] [--shuffle]
  dtb.py lmdb import <lmdb_source> <dataset_type> [--clean]
  dtb.py lmdb size <lmdb_source>
  dtb.py lmdb check-shuffle-status <lmdb_source>
  dtb.py zip export <zip_destination>
  dtb.py zip import <zip_source>

  dtb.py (-l | --list-available-dataset-types)
  dtb.py (-h | --help)
  dtb.py --version

Options:
  -h --help     Show this screen.
  -l --list-available-dataset-types     Lists the available dataset types.
  --version     Show version.
  --size=<WxH>  Sets the width and height in the size of the dataset.
  --description=<dataset_description>   Specifies a dataset description.
  --metadata-file=<metadata_filename>   Specifies the name of the metadata file.
  --shuffle     Shuffles the dataset in the destination.
  --override-existing       Overrides file .options.json in case it exists.
  --equalize-histogram      Equalizes the histogram of the pixels' intensities,
  --clean       Specifies if the previous content should be cleaned. Otherwise it will be merged.
"""

import json
import os
from docopt import docopt
import inspect

from main.dataset.dataset import dataset_proto, LMDB_BATCH_SIZE
from main.normalizer.normalizer import normalizer_proto

# Import datasets to register them
from main.dataset.generic_image_age_dataset import GenericImageAgeDataset           # DO NOT DELETE THIS LINE

# Import normalizers to register them
from main.normalizer.image.histogram_normalizer import HistogramNormalizer          # DO NOT DELETE THIS LINE
from main.normalizer.image.size_normalizer import SizeNormalizer                    # DO NOT DELETE THIS LINE

from main.resource.resource import Resource
from main.tools.lmdb_util import LMDBUtil
from main.tools.splitter import Splitter

__author__ = 'Iván de Paz Centeno'
HIDDEN_CONFIG_FILE='.options.json'


def get_config():
    """
    Gets the config for the current database from a hidden file ".options.json".
    :return: dict with config.
    """
    with open(HIDDEN_CONFIG_FILE) as data_file:
        options = json.load(data_file)

    return options


def set_config(options):
    """
    Writes the config for the current database in a hidden file ".options.json".
    :param options:
    :return: True if could be written, false if it already exists.
    """
    if os.path.exists(HIDDEN_CONFIG_FILE):
        done = False

    else:
        with open(HIDDEN_CONFIG_FILE, mode='w') as data_file:
            json.dump(options, data_file)
        done = True

    return done


class DTB(object):
    """
    DTB class for handling each of the options.
    """

    def __init__(self, arguments):
        self.arguments = arguments
        self.options = {}

    def parse_arguments(self):
        """
        Parses the arguments of the docopt.
        """

        if arguments['init']:
            self.do_initialize()
        else:
            self._load_options()

        if arguments['add']:
            self.do_add()

        elif arguments['size']:
            self.do_get_size()

        elif arguments['lmdb'] and arguments['export']:
            self.do_lmdb_export()

        elif arguments['lmdb'] and arguments['import']:
            pass#self.do_lmdb_import()

        elif arguments['lmdb'] and arguments['check-shuffle-status']:
            self.do_lmdb_check_shuffle()

        elif arguments['lmdb'] and arguments['size']:
            self.do_lmdb_get_size()

        elif arguments['zip'] and arguments['export']:
            pass#self.do_zip_export()

        elif arguments['zip'] and arguments['import']:
            pass#self.do_zip_import()

    def do_initialize(self):
        """
        Initializes the folder with the database configuration.
        If the folder is already initialized it won't do anything.
        """
        available_arguments = ['--size', '--equalize-histogram', '--description', '--metadata-file']

        arguments_to_store = [argument for argument in available_arguments if self.arguments[argument]]

        for argument in arguments_to_store:
            self.options[argument.replace("--","")] = self.arguments[argument]

        # Let's initialize the folder if it isn't already done
        if not set_config(self.options):
            previous_options = get_config()
            print("Folder is already initialized with {}. Remove the file {} and initialize it again.".format(
                previous_options, HIDDEN_CONFIG_FILE))
            exit(-1)

    def _load_options(self):
        """
        Loads the options file and, if it exists, initializes the dataset with that options.
        :return:
        """

        if os.path.exists(HIDDEN_CONFIG_FILE):
            self.options = get_config()

        if self.options['type'] not in dataset_proto:
            print("Invalid dataset type.")
            exit(-1)

        parameters = {
            "root_folder": os.getcwd(),
        }

        arguments_to_fulfill = [argument for argument in inspect.getargspec(dataset_proto[self.options['type']])
                                if argument not in parameters and argument in self.options]

        for argument in arguments_to_fulfill:
            parameters[argument] = self.options[argument]

        # If are there normalizers defined in the options, then append them to the paremeters.
        normalizers_to_fulfill = [normalizer for normalizer in normalizer_proto if normalizer in self.options]

        normalizers = []
        for normalizer in normalizers_to_fulfill:
            normalizers.append(normalizer_proto[normalizer].fromstring(self.options[normalizer]))

        if normalizers:
            parameters['dataset_normalizers'] = normalizers

        self.dataset = dataset_proto[self.options['type']](**parameters)

    def do_get_size(self):
        """
        Prints the size of the dataset (in number of elements).
        :return:
        """
        self.dataset.load_dataset()
        print(len(self.dataset.get_keys()))

    def do_add(self):
        """
        Appends to the current dataset the specified files.
        :return:
        """
        self.dataset.load_dataset()

        resources = [Resource(uri=uri) for uri in self.arguments['<resource-uri>']]

        for resource in resources:
            self.dataset.put_image(resource, autoencode_uri=True, apply_normalizers=True)

    def do_lmdb_export(self):
        """
        Exports the current dataset into a LMDB format under the specified folder with the specified splits.
        :return:
        """
        dest_dir = self.arguments['<lmdb_destination>']

        splits_preprocessed = [split.split(":") for split in self.arguments['<splits>']]

        percentages = [float(split_elements[1]) for split_elements in splits_preprocessed]

        if sum(percentages) > 1:
            print("Splits for LMDB export are not correctly defined: they must sum 1 or less.")
            exit(-1)

        # The percentage with highest value must be changed to 1. Required by dataset's lmdb export method
        index_max = max(range(len(percentages)), key=percentages.__getitem__)
        splits_preprocessed[index_max][1] = 1

        splits = [Splitter(split_elements[1], split_elements[0]) for split_elements in splits_preprocessed]

        # The percentage with highest value must be the last in the splits list.
        if index_max+1 < len(splits):
            # Let's swap index_max by the last element.
            splits[-1], splits[index_max] = splits[index_max], splits[-1]

        # If are there normalizers defined for this export we need to create them.
        normalizers_to_fulfill = [normalizer for normalizer in normalizer_proto if self.arguments["--"+normalizer]]

        normalizers = []
        for normalizer in normalizers_to_fulfill:
            normalizers.append(normalizer_proto[normalizer].fromstring(self.arguments["--"+normalizer]))

        self.dataset.update_normalizers(normalizers)
        self.dataset.load_dataset()

        self.dataset.export_to_lmdb(lmdb_foldername=dest_dir, splitters=splits,
                                    apply_normalizers=(len(normalizers) > 0))

    def do_lmdb_get_size(self):
        """
        Prints the number of elements in a LMDB file.
        """
        lmdb_source = self.arguments["<lmdb_source>"]

        if not os.path.exists(lmdb_source):
            print("Specified LMDB source wasn't found.")
            exit(-1)

        lmdb_util = LMDBUtil(lmdb_source)

        print(lmdb_util.get_size())

    def do_lmdb_check_shuffle(self):
        """
        Checks if a given LMDB is shuffled or not.
        :return:
        """
        lmdb_source = self.arguments["<lmdb_source>"]

        if not os.path.exists(lmdb_source):
            print("Specified LMDB source wasn't found.")
            exit(-1)

        lmdb_util = LMDBUtil(lmdb_source)

        classes = lmdb_util.get_classes()
        max_consecutive_counts = lmdb_util.get_max_consecutive_counts()
        total_classes = len(classes)
        total_elements = sum([value for key, value in classes.items()])

        print("Available_classes:")
        print(json.dumps(classes, indent="    "))
        print("\n Total classes: {}\n Total elements: {}".format(total_classes, total_elements))
        print("\n Max consecutive count:")
        print(json.dumps(max_consecutive_counts, indent="    "))

        # Shuffle logic check: should be lesser than LMDB_BATCH_SIZE
        for class_name, count in max_consecutive_counts.items():
            if count < LMDB_BATCH_SIZE * 0.2:
                print("It is quite well shuffled and it should work under training.")
            elif count < LMDB_BATCH_SIZE * 0.5:
                print("It is partially shuffled, it could work but consider shuffling again.")
            else:
                print("Shuffle is not correct as it is greater than half of the "
                      "batch size ({}).".format(LMDB_BATCH_SIZE))


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Dataset Builder 0.0.1 Jan 2017')
    dtb = DTB(arguments)
    dtb.parse_arguments()
