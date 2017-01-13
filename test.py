#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from main.tools.splitter import Splitter

__author__ = 'Iván de Paz Centeno'

val_splitter = Splitter(0.1)
test_splitter = Splitter(0.2)

train_set = []
test_set = []
val_set = []

total_size = 200

for num in range(total_size):
    if val_splitter.decide(num):
        continue

    if test_splitter.decide(num):
        continue

    train_set.append(num)


test_set = test_splitter.get_splitted_list()
val_set = val_splitter.get_splitted_list()

print("Len of train set: {} ({}%)".format(len(train_set), len(train_set) / total_size * 100))
print("Len of test set: {} ({}%)".format(len(test_set), len(test_set) / total_size * 100))
print("Len of val set: {} ({}%)".format(len(val_set), len(val_set) / total_size * 100))

print(test_set)