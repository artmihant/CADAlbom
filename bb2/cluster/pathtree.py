# -*- coding: utf-8 -*-
import os

def treetodict(tree, name='', root=[]):

    def checkType(arg, Type, num=None):
        if type(arg) != Type:
            raise TypeError('{} - uncorrected type: type({}) is {}'.format(num, tree, type(tree)))

    if type(tree) == str:
        return {name: root+[tree]}

    checkType(tree, list)

    body = tree[:-1]
    tails = tree[-1]

    for el in body:
        checkType(el, str)

    if type(tails) == str:
        body = body + [tails]
        tails = {}

    if len(body) == 0:
        if name:
            body.append(name)
    elif body[-1] == '':
        body[-1] = name

    body = root+body

    if not tails:
        return {name: body}

    checkType(tails, dict)

    result = {name: body} if name else {}

    for name in tails:
        if not tails[name]:
            result[name] = body + [name]
            continue

        tail = treetodict(tails[name], name, body)

        for key in tail:
            assert not key in result, '{} duplicated in tree!'.format(key)
            result[key] = body+tail[key][:-1]+[key] if tail[key][-1]=='' else tail[key]

    return result

class PathTree:
    def __init__(self, tree):
        self.tree = treetodict(tree)

    def __getitem__(self, key):
        return self.tree[key]

    def __setitem__(self, key, value):
        if type(value) == list:
            self.tree[key] = value
        elif type(value) == str:
            self.tree[key] = [value]
        else:
            raise TypeError('uncorrected type: type({}) is {}'.format(value, type(value)))

    def __len__(self):
        return len(self.tree)

    def __iter__(self):
        for name in self.tree:
            yield name

    def __call__(self, key, *join):
        return os.path.join(*self.tree[key]+list(join))

    def __str__(self):
        res = ''
        for key in self.tree:
            res += key+':\t'+os.path.join(*self.tree[key])+'\n'
        return res 