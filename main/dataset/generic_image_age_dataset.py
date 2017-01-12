#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import errno
import caffe
from caffe.io import array_to_datum
from caffe.proto import caffe_pb2
import cv2
import lmdb
import numpy as np
from main.dataset.dataset import Dataset
from main.resource.image import Image
from main.tools.age_range import AgeRange

__author__ = 'Iván de Paz Centeno'


LMDB_BATCH_SIZE = 256   # Batch size for writing into LMDB. This is the amount of images
                        # before the batch is commited into the file.


def mkdir_p(dir):
    """
    Creates a dir recursively (like mkdir -p).
    If it already exists does nothing.
    :param dir: dir to create.
    :return:
    """

    try:
        os.makedirs(dir)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dir):
            pass
        else:
            print("Error when creating dir for dataset: {}".format(exc))
            raise

class GenericImageAgeDataset(Dataset):
    """
    Dataset of images for ages.
    It allows to read an existing dataset or to create a new one under the specified root folder.
    """

    def __init__(self, root_folder, metadata_file="labels.json",
                 description="Generic Dataset JSON-Based of images with Age labels"):
        """
        Initialization of a dataset of images with ages labeled.
        Metadata is built from a JSON file.
        :param root_folder:
        :param metadata_file: JSON file URI, which is composed by the following format: {'IMAGE_FILE_NAME': AGE_RANGE_STRING}

                              Example:
                                {'test/image1.jpg': '[23,34]'}

                              Note: the working directory when loading the metadata_file is root_folder.
        :param description: description of the dataset for report purposes.
        :return:
        """
        # This dataset class is also capable of creating datasets.
        mkdir_p(root_folder)

        # When metadata_file is not an absolute URI, it is related to root_folder.
        if not self._is_absolute_uri(metadata_file):
            metadata_file = os.path.join(root_folder, metadata_file)

        Dataset.__init__(self, root_folder, metadata_file, description)

        self.autoencoded_uris = {}

    def _is_absolute_uri(self, uri):
        """
        Checks if the specified uri is absolute or relative.
        :param uri: URI to check
        :return: True if it is absolute, False otherwise.
        """
        return uri.startswith("/")

    def get_keys(self):
        """
        Returns the keys for the find_route method as a list.
        :return: list of keys for the find_route
        """

        return list(self.metadata_content.keys())

    def get_key_metadata(self, key):
        """
        Retrieves the metadata for the specified key
        :param key:
        :return:
        """

        return self.metadata_content[key]

    def get_image(self, key):
        """
        Retrieves the image representing the specified key ID.
        :return:
        """
        # For generic image age dataset, the key is the relative uri to the file.
        uri = os.path.join(self.root_folder, key)
        image = Image(image_id=key, uri=uri, metadata=[self.get_key_metadata(key)])

        return image

    def put_image(self, image, autoencode_uri=True):
        """
        Puts an image in the dataset.
        It must be filled with content, relative uri and metadata in order to be created the dataset.
        :param image: Image to save in the dataset.
        :param autoencode_uri: Boolean flag to set if the URI should be automatically filled by the dataset or not.
        :return:
        """

        if autoencode_uri:
            uri = self._encode_uri_for_image(image)

        else:
            uri = image.get_uri()

        if self._is_absolute_uri(uri):
            raise Exception("Uri for storing into dataset must be relative, not absolute")

        key = uri   # We index by the relative uri
        uri = os.path.join(self.root_folder, uri)
        mkdir_p(os.path.dirname(uri))

        self.metadata_content[key] = image.get_metadata()[0]

        try:
            if not image.is_loaded():
                image.load_from_uri()

            cv2.imwrite(uri, image.get_blob())
            print("Saved into {}".format(uri))
        except Exception as ex:
            print("Could not write image in \"{}\"".format(image.get_uri()))
            del self.metadata_content[key]
            raise

    def _encode_uri_for_image(self, image):
        """
        Finds a new URI for the specified image inside the dataset.
        It is going to create an uri based on the age-range and the number of images that matches that age range.
        :param image: image to find an URI for.
        :return: URI for the image.
        """
        try:
            age_range = image.get_metadata()[0]
        except Exception as ex:
            print("Image to save does not contain label for age (AgeRange) in metadata.")
            raise

        if age_range.hash() not in self.autoencoded_uris:
            self.autoencoded_uris[age_range.hash()] = 0
            #mkdir_p(os.path.join(self.root_folder, "{}-{}".format(age_range.get_range()[0], age_range.get_range()[1])))

        uri = "{}-{}/{}.jpg".format(age_range.get_range()[0], age_range.get_range()[1],
                                 self.autoencoded_uris[age_range.hash()])
        self.autoencoded_uris[age_range.hash()] += 1

        return uri

    def load_dataset(self):
        """
        Loads the dataset from the specified root folder.
        """

        # Let's load the routes list. This way we can reference them easily by the metadata_file content.
        self._load_routes()
        self._load_metadata_file()
        self.metadata_content = self._preprocess_metadata(self.metadata_content)

    @staticmethod
    def _preprocess_metadata(raw_metadata):
        """
        Processes the metadata content in order to be framework-compliant (AgeRange classes for ages)
        :param raw_metadata: raw metadata content to be processed.
        :return: Metadata dict with {FileName:AgeRange} format.
        """
        metadata_content = json.loads("".join(raw_metadata))
        preprocessed_metadata = {}

        for key, value in metadata_content.items():
            preprocessed_metadata[key] = AgeRange.from_string(value)

        return preprocessed_metadata

    @staticmethod
    def _postprocess_metadata(preprocessed_metadata):
        """
        Processes the metadata to make a raw metadata again (in order to be dumped to a file for example).
        :param preprocessed_metadata:
        :return: raw metadata without objects, dumpable into string and/or file.
        """
        postprocessed_metadata = {}

        for key, value in preprocessed_metadata.items():
            postprocessed_metadata[key] = value.to_dict()["Age_range"]

        return postprocessed_metadata

    def save_dataset(self):
        """
        Dumps the metadata labels in JSON format inside the dataset's folder with name labels.json
        :return:
        """

        with open(self.metadata_file, 'w') as outfile:
            json.dump(self._postprocess_metadata(self.metadata_content), outfile, indent=4)

    def get_dataset_size(self):
        """
        Calculates the dataset size based on the images' sizes.
        :return: size in bytes of the whole dataset (excluding the metadata).
        """
        keys = self.get_keys()

        dataset_size = 0
        for key in keys:
            image = self.get_image(key)
            image.load_from_uri()
            dataset_size += image.get_blob().nbytes

        return dataset_size

    def export_to_lmdb(self, lmdb_foldername, ages_as_means=True, map_size=-1):
        """
        Exports the current dataset to LMDB format.
        If the LMDB already exists, it will append to its content.
        :param lmdb_foldername: filename LMDB.
        :param ages_as_means: save the age_range in mean format.
        :param map_size: size of map of the LMDB database. If set to -1, it will attempt to calculate a map_size that
        fits this dataset. Remember however, that it won't allow to expand the LMDB database with new data and you'll
        need to create a new one in case you want to.
        """
        iteration = 0

        keys = self.get_keys()
        count = len(keys)

        if map_size == -1:
            map_size = self.get_dataset_size() + count * 30000

        print("Map size is {} MBytes".format(round(map_size/1000/1000, 2)))
        env = lmdb.Environment(lmdb_foldername, map_size=map_size)
        txn = env.begin(write=True, buffers=True)

        for key in keys:
            iteration += 1

            image = self.get_image(key)
            image.load_from_uri()
            age_range = image.get_metadata()[0]
            if ages_as_means:
                label = age_range.get_mean()
            else:
                label = age_range.get_range()[0]

            #HxWxC to CxHxW in caffe
            image_blob = np.transpose(image.get_blob(), (2,0,1))

            # Datum is the element map in LMDB. We associate image with label here.
            datum = array_to_datum(image_blob, label)

            # Now we encode the image id in ascii format inside the lmdb container.
            txn.put(image.get_id().encode("ascii"), datum.SerializeToString())

            # write batch
            if iteration % LMDB_BATCH_SIZE == 0:
                txn.commit()
                txn = env.begin(write=True)
                print("[{}%] Stored batch of {} images in LMDB".format(round(iteration/count * 100, 2),
                                                                       LMDB_BATCH_SIZE))

        # There could be a last batch without being commited.
        if iteration % LMDB_BATCH_SIZE != 0:
            txn.commit()
            print("[{}%] Stored batch of {} images in LMDB".format(round(iteration/count * 100, 2),
                                                                       iteration % LMDB_BATCH_SIZE))

        env.close()

    def import_from_lmdb(self, lmdb_foldername):
        """
        Imports the dataset from LMDB format into the root_folder.
        :param lmdb_foldername: filename LMDB.
        """

        lmdb_env = lmdb.open(lmdb_foldername)
        lmdb_txn = lmdb_env.begin()
        lmdb_cursor = lmdb_txn.cursor()

        datum = caffe_pb2.Datum()

        for key, value in lmdb_cursor:
            key = str(key, encoding="UTF-8")

            datum.ParseFromString(value)

            label = datum.label
            data = caffe.io.datum_to_array(datum)

            # CxHxW to HxWxC in cv2
            image_blob = np.asarray(np.transpose(data, (1,2,0)), order='C')

            image = Image(uri=key, image_id=key, metadata=[AgeRange(label, label)], blob_content=image_blob)
            self.put_image(image, autoencode_uri=False)

        lmdb_env.close()