#!/usr/bin/env python
# -*- coding: utf-8 -*-
from albom import Albom

c = Albom('mini', async=False)
c.do('loadsave')