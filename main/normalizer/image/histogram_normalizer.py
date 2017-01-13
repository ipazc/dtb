#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
from main.normalizer.normalizer import Normalizer

__author__ = 'Iván de Paz Centeno'


class HistogramNormalizer(Normalizer):
    """
    Equalizes the histogram of an image blob.
    """

    def apply(self, blob):
        #Histogram Equalization
        blob[:, :, 0] = cv2.equalizeHist(blob[:, :, 0])
        blob[:, :, 1] = cv2.equalizeHist(blob[:, :, 1])
        blob[:, :, 2] = cv2.equalizeHist(blob[:, :, 2])

        return blob