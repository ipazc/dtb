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

    def get_max_consecutive_counts(self):
        lmdb_env = lmdb.open(self.lmdb_folder)
        lmdb_txn = lmdb_env.begin()
        lmdb_cursor = lmdb_txn.cursor()

        max_consecutive_labels = {}

        datum = caffe_pb2.Datum()

        consecutive_label_name = ""
        consecutive_label_count = 0

        for key, value in lmdb_cursor:
            key = str(key, encoding="UTF-8")

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

        lmdb_env.close()

        return max_consecutive_labels


