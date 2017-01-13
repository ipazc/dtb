#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from main.dataset.generic_image_age_dataset import GenericImageAgeDataset

__author__ = 'Iván de Paz Centeno'

generic_dataset = GenericImageAgeDataset("/home/ivan/generic_dataset_test3/")
generic_dataset.load_dataset()
generic_dataset.import_from_lmdb("/home/ivan/model_test/cat-dogs_lmdb")
generic_dataset.save_dataset()  # The dataset is dumped into /home/ivan/generic_dataset_test2