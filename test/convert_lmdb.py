#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from main.dataset.generic_image_age_dataset import GenericImageAgeDataset
from main.normalizer.image.histogram_normalizer import HistogramNormalizer
from main.normalizer.image.size_normalizer import SizeNormalizer
from main.tools.splitter import Splitter

__author__ = 'Iván de Paz Centeno'


dataset_uri="/home/ivan/model_test/dataset/cat-dogs"

histogram_normalizer = HistogramNormalizer()
size_normalizer = SizeNormalizer()

dataset = GenericImageAgeDataset(dataset_uri, dataset_normalizers=[histogram_normalizer, size_normalizer])
dataset.load_dataset()

train_splitter = Splitter(split_percentage=1, name="train")
validation_splitter = Splitter(split_percentage=0.17, name="validation")

dataset.export_to_lmdb("/home/ivan/model_test/cat-dogs_lmdb", apply_normalizers=True,
                       splitters=[validation_splitter, train_splitter])
