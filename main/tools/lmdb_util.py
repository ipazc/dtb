#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import caffe
from caffe.proto import caffe_pb2
import lmdb

__author__ = 'Iván de Paz Centeno'


class LMDBUtil(object):
    """
    Wraps a LMDB database to know information about it.
    """

    def __init__(self, lmdb_folder):
        self.lmdb_folder = lmdb_folder

    def get_size(self):
        """
        :return: the amount of elements inside the LMDB file.
        """
        classes = self.get_classes()
        return sum([value for key, value in classes.items()])

    def get_classes(self):
        """
        :return: the different classes available inside the LMDB file.
        """
        lmdb_env = lmdb.open(self.lmdb_folder)
        lmdb_txn = lmdb_env.begin()
        lmdb_cursor = lmdb_txn.cursor()

        classes = {}

        datum = caffe_pb2.Datum()
        for key, value in lmdb_cursor:
            datum.ParseFromString(value)

            label = datum.label

            if label not in classes:
                classes[label] = 0

            classes[label] += 1

        lmdb_env.close()

        return classes

    def get_max_consecutive_counts(self):
        lmdb_env = lmdb.open(self.lmdb_folder)
        lmdb_txn = lmdb_env.begin()
        lmdb_cursor = lmdb_txn.cursor()

        max_consecutive_labels = {}

        datum = caffe_pb2.Datum()

        consecutive_label_name = ""
        consecutive_label_count = 0

        for key, value in lmdb_cursor:
            datum.ParseFromString(value)

            label = datum.label

            if consecutive_label_name == "":
                consecutive_label_name = label

            if label == consecutive_label_name:
                consecutive_label_count += 1

            else:
                if consecutive_label_name in max_consecutive_labels:
                    max_consecutive_label = max_consecutive_labels[consecutive_label_name]
                else:
                    max_consecutive_label = 0

                max_consecutive_labels[consecutive_label_name] = max(consecutive_label_count, max_consecutive_label)
                consecutive_label_name = label
                consecutive_label_count = 1

        if consecutive_label_name not in max_consecutive_label:
            max_consecutive_label[consecutive_label_name] = consecutive_label_count

        lmdb_env.close()

        return max_consecutive_labels


