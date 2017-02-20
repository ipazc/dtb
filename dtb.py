#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dataset builder tool.
Creates or converts between specific standards of datasets (like LMDB) and raw datasets.


Usage:
  dtb.py init <dataset_type> [--size=<WxH>] [--equalize-histogram] [--override-existing] [--description=<dataset_description>] [--metadata-file=<metadata_filename>]
  dtb.py list-dataset-types
  dtb.py add <resource-uri>...
  dtb.py info
  dtb.py size
  dtb.py lmdb export <lmdb_destination> <splits>... [--size=<WxH>] [--equalize-histogram] [--shuffle]
  dtb.py lmdb import <lmdb_source> [--clean]
  dtb.py lmdb size <lmdb_source>
  dtb.py lmdb check-shuffle-status <lmdb_source>
  dtb.py zip export <zip_destination>
  dtb.py zip import <zip_source> [--override-config]
  dtb.py merge <dataset_uri>... [--deduplicate-by-hash] [--blacklist=<uri>]

  dtb.py (-h | --help)
  dtb.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --size=<WxH>  Sets the width and height in the size of the dataset.
  --blacklist=<uri>   Specifies a blacklist dataset for resources. This means that all resources' hashes within this dataset are used to discard images when merging.
  --description=<dataset_description>   Specifies a dataset description.
  --metadata-file=<metadata_filename>   Specifies the name of the metadata file.
  --shuffle     Shuffles the dataset in the destination.
  --override-existing       Overrides file .options.json in case it exists.
  --equalize-histogram      Equalizes the histogram of the pixels' intensities,
  --clean       Specifies if the previous content should be cleaned. Otherwise it will be merged.
  --override-config     Overrides the configuration file for this dataset if it exists in the zip file.
"""

import json
import os
from docopt import docopt
import inspect

from main.dataset.data_holder.mem_database import MemDatabase
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


def set_config(options, override=False):
    """
    Writes the config for the current database in a hidden file ".options.json".
    :param options:
    :return: True if could be written, false if it already exists.
    """
    if os.path.exists(HIDDEN_CONFIG_FILE) and not override:
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
        self.dataset = None

    def parse_arguments(self):
        """
        Parses the arguments of the docopt.
        """
        if arguments['list-dataset-types']:
            self.do_list_dataset_types()
        elif arguments['lmdb'] and arguments['check-shuffle-status']:
            self.do_lmdb_check_shuffle()
        elif arguments['lmdb'] and arguments['size']:
            self.do_lmdb_get_size()
        #
        #

        if arguments['init']:
            self.do_initialize()
        else:
            self._load_options()

        if arguments['add']:
            self.do_add()

        if arguments['merge']:
            self.do_merge()

        elif arguments['info']:
            self.do_info()

        elif arguments['size']:
            self.do_get_size()

        elif arguments['lmdb'] and arguments['export']:
            self.do_lmdb_export()

        elif arguments['lmdb'] and arguments['import']:
            self.do_lmdb_import()

        elif arguments['zip'] and arguments['export']:
            self.do_zip_export()

        elif arguments['zip'] and arguments['import']:
            self.do_zip_import()

    def do_initialize(self):
        """
        Initializes the folder with the database configuration.
        If the folder is already initialized it won't do anything.
        """
        available_arguments = ['--size', '--equalize-histogram', '--description', '--metadata-file']

        arguments_to_store = [argument for argument in available_arguments if self.arguments[argument]]
        self.options["type"] = self.arguments["<dataset_type>"]

        for argument in arguments_to_store:
            self.options[argument.replace("--","")] = self.arguments[argument]

        do_override = self.arguments['--override-existing']

        # Let's initialize the folder if it isn't already done
        if not set_config(self.options, do_override):
            previous_options = get_config()
            print("Folder is already initialized with {}. Remove the file {} and initialize it again.".format(
                previous_options, HIDDEN_CONFIG_FILE))
            exit(-1)

        exit(0)

    def _load_options(self):
        """
        Loads the options file and, if it exists, initializes the dataset with that options.
        :return:
        """

        if os.path.exists(HIDDEN_CONFIG_FILE):
            self.options = get_config()
        else:
            print("There seems to not be any database initialized under the current folder.")
            exit(-1)

        if self.options['type'] not in dataset_proto:
            print("Invalid dataset type.")
            exit(-1)

        parameters = {
            "root_folder": os.getcwd(),
        }

        arguments_to_fulfill = [argument for argument in inspect.getargspec(dataset_proto[self.options['type']]).args
                                if argument not in parameters and argument in self.options]

        for argument in arguments_to_fulfill:
            parameters[argument] = self.options[argument]

        # If are there normalizers defined in the options, then append them to the parameters.
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
        exit(0)

    def do_add(self):
        """
        Appends to the current dataset the specified files.
        :return:
        """
        self.dataset.load_dataset()
        metadata_proto = self.dataset.get_metadata_proto()

        resources = []

        for full_uri in self.arguments['<resource-uri>']:
            uri, label = full_uri.split(":")
            resources.append(Resource(uri=uri, metadata=[metadata_proto.from_string(label)]))

        for resource in resources:
            self.dataset.put_resource(resource, autoencode_uri=True, apply_normalizers=True)

        # Now we save the dataset
        self.dataset.save_dataset()

        exit(0)

    def do_merge(self):
        """
        Merges multiple datasets into the current one. They must be of the same type.
        :return:
        """
        blacklist_mem_hashes = MemDatabase()

        if self.arguments['--blacklist']:
            blacklist_uri = self.arguments['--blacklist']
            blacklist_dataset = dataset_proto[self.options['type']](root_folder=blacklist_uri)
            blacklist_dataset.load_dataset()

            [blacklist_mem_hashes.append(key, blacklist_dataset.get_image(key)) for key in blacklist_dataset.get_keys()]

        self.dataset.load_dataset()

        # Here we wrap each URI inside a dataset object. The type of the dataset is defined inside self.options['type']
        datasets = [dataset_proto[self.options['type']](root_folder=uri) for uri in self.arguments['<dataset_uri>']]

        for dataset in datasets:
            print("Loading dataset {}...".format(dataset.get_root_folder()), end="")
            dataset.load_dataset()
            print(" Loaded.")

        # Two different ways: to hash by content or not.
        if self.arguments['--deduplicate-by-hash']:
            print("Deduplicating by md5hash of content.")

            # Mem_database helps us to hash by content on the fly.
            mem_database = MemDatabase()

            for dataset in datasets:
                print("Fetching hash keys from dataset {}...".format(dataset.get_root_folder()), end="")
                [mem_database.append(key, dataset.get_image(key)) for key in dataset.get_keys()]
                print(" Done.")

            print("Adding images to final dataset...", end="")

            for hash, [key, image] in mem_database.get_data().items():

                if not blacklist_mem_hashes.contains_image(image):
                    self.dataset.put_resource(image)

            print(" Finished.")

        else:
            print("Adding images to final dataset...", end="")
            for dataset in datasets:
                [self.dataset.put_resource(dataset.get_image(key)) for key in dataset.get_keys()]
            print(" Finished.")

        self.dataset.save_dataset()

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

        exit(0)

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
        exit(0)

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
                print("[Class {}] It is quite well shuffled and it should work under training.".format(class_name))
            elif count < LMDB_BATCH_SIZE * 0.5:
                print("[Class {}] It is partially shuffled, it could work but consider shuffling again.".format(class_name))
            else:
                print("[Class {}] Shuffle is not correct as it is greater than half of the "
                      "batch size ({}).".format(LMDB_BATCH_SIZE, class_name))

        exit(0)

    def do_list_dataset_types(self):
        """
        Prints the dataset types available for use in init.
        :return:
        """
        [print(dataset_type) for dataset_type in dataset_proto]

        exit(0)

    def do_lmdb_import(self):
        """
        Imports from an LMDB file into the current dataset folder.
        :return:
        """
        self.dataset.load_dataset()

        source = self.arguments['<lmdb_source>']

        if not os.path.exists(source):
            print("Error: the specified LMDB source folder does not exist.")
            exit(-1)

        do_clean = self.arguments['--clean']

        if do_clean:
            self.dataset.clean(remove_files=True)

        self.dataset.import_from_lmdb(source)
        self.dataset.save_dataset()

        exit(0)

    def do_zip_export(self):
        """
        Exports the current dataset into a zip file
        :return:
        """
        destination = self.arguments['<zip_destination>']

        self.dataset.export_to_zip(destination)

        exit(0)

    def do_zip_import(self):
        """
        Imports the zip into current dataset.
        :return:
        """
        source = self.arguments['<zip_source>']
        override_config = self.arguments['--override-config']

        self.dataset.import_from_zip(source)

        if not override_config:
            set_config(self.options, True)

        self.dataset.save_dataset()

        exit(0)

    def do_info(self):
        """
        Prints information regarding the current dataset.
        :return:
        """

        print("=============================")
        print("= Dataset information        ")
        print("= ")

        for option, value in self.options.items():
            print("= {}: {}".format(option, value))

        print("=============================")

        exit(0)


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Dataset Builder 0.0.1 Jan 2017')
    dtb = DTB(arguments)
    dtb.parse_arguments()
