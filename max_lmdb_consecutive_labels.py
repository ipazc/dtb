#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from main.tools.lmdb_util import LMDBUtil

__author__ = 'Iván de Paz Centeno'

uri = sys.argv[1]

lmdb_util = LMDBUtil(uri)

print(lmdb_util.get_max_consecutive_counts())