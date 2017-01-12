#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from main.dataset.generic_image_age_dataset import GenericImageAgeDataset

__author__ = 'Iván de Paz Centeno'

generic_dataset = GenericImageAgeDataset("/home/ivan/generic_dataset_test/")
generic_dataset.load_dataset()

keys = generic_dataset.get_keys()

print("Keys are: {}".format(keys))

image = generic_dataset.get_image(keys[0])
image.load_from_uri()
print(image)