#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from main.dataset.generic_image_age_dataset import GenericImageAgeDataset
from main.resource.image import Image
from main.tools.age_range import AgeRange

__author__ = 'Iván de Paz Centeno'

example = Image(uri="/home/ivan/edurne.jpg", metadata=[AgeRange(24,26)])
example2 = Image(uri="/home/ivan/edurne.jpg", metadata=[AgeRange(24,26)])
example3 = Image(uri="/home/ivan/edurne.jpg", metadata=[AgeRange(1,2)])

generic_dataset = GenericImageAgeDataset("/home/ivan/generic_dataset_test/")

generic_dataset.put_image(example)
generic_dataset.put_image(example2)
generic_dataset.put_image(example3)

generic_dataset.save_dataset()