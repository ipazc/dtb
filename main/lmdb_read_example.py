#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from main.dataset.generic_image_age_dataset import GenericImageAgeDataset

__author__ = 'Iván de Paz Centeno'

generic_dataset = GenericImageAgeDataset("/home/ivan/generic_dataset_test2/")

generic_dataset.import_from_lmdb("/home/ivan/generic_dataset_test/generic_dataset_test.lmdb")
generic_dataset.save_dataset()  # The dataset is dumped into /home/ivan/generic_dataset_test2