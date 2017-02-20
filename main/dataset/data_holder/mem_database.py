#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib

__author__ = "Ivan de Paz Centeno"

# TODO: Make a more generic MemDatabase, not specified to Images only but resources!
class MemDatabase(object):

    def __init__(self):

        self.data = {}

    def _extract_key_from_hash(self, image):
        image = image.clone()

        if not image.is_loaded():
            image.load_from_uri()

        if not image.is_loaded():
            result = None
        else:
            result = self._get_image_hash(image.get_jpeg())

        return result

    def contains_image(self, image):
        """
        Checks if a given image is hashed here.
        :param image:
        :return:
        """
        return self._extract_key_from_hash(image) in self.data

    def append(self, key, image):
        """
        Appends the image to the database.
        Each image is indexed by its md5 hash.

        :param key:
        :param image:
        :return:
        """
        hash_key = self._extract_key_from_hash(image)

        if hash_key is not None:
            self.data[hash_key] = [key, image]

        #image.unload()  # Unload to free memory. We may load it again later.

    @staticmethod
    def _get_image_hash(image_bytes):
        """
        Computes the image hash from its array of bytes
        :param self:
        :param image_bytes: array of bytes of the image (it is not a numpy array, it is the image in binary format,
        like jpg or png).
        :return:
        """
        return hashlib.md5(image_bytes).hexdigest()

    def get_data(self):
        return self.data