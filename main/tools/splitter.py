#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random

__author__ = 'Iván de Paz Centeno'


class Splitter(object):
    """
    Allows to decide when to split a given entry.
    It is has a buffer to store a list of entries.
    """

    def __init__(self, split_percentage=0.2, name=None):
        """
        Initialization of the splitter.
        :param split_percentage: percentage of inputs that are going to be splitted.
        """
        self.split_percentage = split_percentage
        random.seed()
        self.splitted_list = []
        self.name = name

    def decide(self, entry):
        """
        Performs a decision on a given entry. This means, to split it or to not split it.
        It is going to split this entry with a self.split_percentage probability.
        :param entry: entry to decide if it should be splitted or not.
        :return:
        """

        if random.random() < self.split_percentage:
            split_made = True
            self.splitted_list.append(entry)
        else:
            split_made = False

        return split_made

    def get_splitted_list(self):
        """
        Getter for the splitted list
        :return:
        """
        return self.splitted_list

    def get_name(self):
        """
        Getter for the name of the splitter.
        :return:
        """
        return self.name