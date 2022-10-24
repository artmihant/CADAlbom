# -*- coding: utf-8 -*-
import json
import os
import hashlib
import random
import shutil
from model import Model
from celery_tasks import do
import scripts


class Albom:

    extensions = ['stp']

    def __init__(self, basedir, namebook=None, async=True, name=None):
        self.name = name if name else basedir
        self.basedir = os.path.abspath(basedir)
        if namebook==None:
            self.namebook = os.listdir(basedir)
        else:
            self.namebook = namebook
        self.scripts = filter(lambda s:not '__' in s, dir(scripts))
        self.async = async

    def scandir(self, sourcedir):
        for root, dirs, files in os.walk(sourcedir):
            for file in files:
                self.add(os.path.join(root,file))

    def revome_cubit_logs(self):
        for model in self:
            model.revome_cubit_logs()

    def rm(self, file):
        for model in self:
            model.rm(file)

    def copy(self, folder):
        if not os.path.isabs(folder):
            folder = os.path.join(self.basedir,'..', folder)

        for model in self:
            shutil.copytree(model.path, os.path.join(folder, model.name))
            print(model.path, os.path.join(folder, model.name))

    def do(self, script):

        if type(script) == int:
            script = self.scripts[script-1]
        elif not script in self.scripts:
            raise AttributeError('Не могу найти сценарий {}'.format(script))

        print('{}({} models)'.format(script, len(self)))

        for model in self:
            if self.async:
                do.delay(script, model.path)
            else:
                do(script, model.path)

    def __str__(self):
        listing = ', '.join(self.namebook)[0:50]
        return '{}:[{} ... {}]'.format(self.name, listing, len(self))

    def __repr__(self):
        return '<Albom {} ({})>'.format(self.name, len(self))

    def __len__(self):
        return len(self.namebook)

    def __iter__(self):
        for name in self.namebook:
            yield Model(os.path.join(self.basedir,name))

    def __call__(self, key):
        if type(key).__name__ == 'function':
            namebook = []
            for model in self:
                if key(model):
                    namebook.append(model.name)
            return Albom(self.basedir, namebook=namebook, async=self.async, name=self.name)
        else:
            statistic = dict()
            for model in self:
                if model[key] in statistic:
                    statistic[model[key]] += 1
                else:
                    statistic[model[key]] = 1
            return statistic


    def write(self, key, value):
        if value != None:
            for model in self:
                model[key] = value
        else:
            for model in self:
                del(model[param])
        return self(key)


    def add(self, filepath):
        if not os.path.exists(filepath):
            return -1

        oldname, ext = os.path.splitext(filepath)
        ext = ext.lower()[1:]
        if ext == 'step':
             ext = 'stp'
        if ext not in self.extensions:
            return 0

        hash = self.get_hash_stp(filepath) \
            if ext == 'stp' \
            else self.get_hash(filepath)

        name = self.namegen(hash)
        newdir = os.path.join(self.basedir, name)
        if name in self.namebook:
            return 0
        os.makedirs(newdir)
        self.namebook.append(name)
        shutil.copyfile(filepath, os.path.join(newdir, 'model.'+ext) )

        print('Create {}.{} from {}.{}'.format(name,ext,oldname,ext))
        local_data = dict(oldname=oldname, ext=ext, name=name)
        with open(os.path.join(newdir,'note.json'), "w") as write_file:
            json.dump(local_data, write_file)


    @staticmethod
    def namegen(hash):
        random.seed(hash)
        return ''.join(random.choice('aouie' if _%2 else 'wrtsdfghklvbnm') for _ in range(9))


    @staticmethod
    def get_hash_stp(filepath):
        lines = open(filepath)
        start = False
        m = hashlib.md5()
        for line in lines:
            if 'DATA;' in line:
                start = True
            if start:
                m.update(line)
        return m.hexdigest()


    @staticmethod
    def get_hash(filename):
        with open(filename, 'rb') as f:
            m = hashlib.md5()
            while True:
                data = f.read(8192)
                if not data:
                    break
                m.update(data)
            return m.hexdigest()

