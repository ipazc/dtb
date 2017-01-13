#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
from main.normalizer.normalizer import Normalizer

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