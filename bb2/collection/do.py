#!/usr/bin/env python
# -*- coding: utf-8 -*-
from albom import Albom

a = Albom('collection').filter(lambda m:m['vol']==1 and not m['mesh'])
