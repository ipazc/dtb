#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
from main.normalizer.normalizer import Normalizer, normalizer_proto

__author__ = 'Iván de Paz Centeno'


class SizeNormalizer(Normalizer):
    """
    Resizes the image blob to a specific size.
    """
    def __init__(self, width=227, height=227):
        """
        Constructor for the size normalizer.
        :param width: width in pixels to resize the blobs.
        :param height: height in pixels to resize the blobs.
        """
        self.width = width
        self.height = height

    def apply(self, blob):
        #Image Resizing
        blob = cv2.resize(blob, (self.width, self.height), interpolation = cv2.INTER_CUBIC)
        return blob

    @classmethod
    def fromstring(cls, size):
        """
        Creates the instance from a string of the format WIDTHxHEIGHT.
        :param size: string with the format WIDTHxHEIGHT.
        :return: instance of the class
        """
        sizes = size.split('x')

        if len(sizes) != 2:
            raise Exception("Format of size \"{}\" is not valid! It must be WIDTHxHEIGHT. Example: 1024x768".format(size))

        return cls(sizes[0], sizes[1])


normalizer_proto["size"] = SizeNormalizer
