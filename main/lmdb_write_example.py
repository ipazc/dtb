#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from main.dataset.generic_image_age_dataset import GenericImageAgeDataset

__author__ = 'Iván de Paz Centeno'

generic_dataset = GenericImageAgeDataset("/home/ivan/generic_dataset_test/")
generic_dataset.load_dataset()  # The dataset is loaded from /home/ivan/generic_dataset_test

generic_dataset.export_to_lmdb("/home/ivan/generic_dataset_test/generic_dataset_test.lmdb")
# LMDB will create a folder named "generic_dataset_test.lmdb" with the lmdb files.