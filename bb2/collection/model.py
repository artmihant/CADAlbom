# -*- coding: utf-8 -*-
import os
import sys
import json
from billiard.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded
import importlib

class Model:

    musthave = {
        'data':'note.json',
        'source': 'model.stp'
    }

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.name = os.path.basename(path)
        self.basepath = os.path.dirname(os.path.abspath(__file__))
        with open(self.abs(self.musthave['data']), "r") as file:
            self.data = json.load(file)

        self.source = self.abs(r'model.{}'.format(self['ext']))


    def __str__(self):
        return '<{}.{} ({})>'.format(self.name, self['ext'], len(self))


    def __repr__(self):
        return '<Model {} ({})>'.format(self.name, len(self))


    def __len__(self):
        if 'size' not in self.data:
            self['size'] = os.path.getsize(self.source)
        return self['size']


    def __getitem__(self, key):
        if key not in self.data:
            return None
        return self.data[key]


    def __setitem__(self, key, value):
        self.data[key] = value


    def __delitem__(self, key):
        if key in self.data:
            del(self.data[key])


    def __iter__(self):
        for name in self.data:
            yield name


    def __enter__(self):
        sys.path.append('/home/fidesys/collection/fidesys/preprocessor/bin')
        os.chdir(self.path)
        self.cubit = importlib.import_module('cubit')
        self.cubit.init([])
        return self


    def __exit__(self, *args):
        if args[0] in (SoftTimeLimitExceeded, TimeLimitExceeded):
            print('It is Soft Time!')
            self['timeout'] = True
        self.cubit.destroy()
        os.chdir(self.basepath)

    def __del__(self):
        with open(self.abs(self.musthave['data']), "w") as file:
            json.dump(self.data, file)


    def abs(self, file):
        return file \
            if os.path.isabs(file) \
            else os.path.abspath(os.path.join(self.path, file))


    def vol(self):
        self['vol'] = self.cubit.get_volume_count()
        return self['vol']


    def cmd(self, arg):
        error_count = self.cubit.get_error_count()
        arg = str(arg)
        self.cubit.cmd(arg)
        if self.cubit.get_error_count() > error_count:
            print('ERROR: Command: ' + arg)
            return False
        return True        

    def revome_cubit_logs(self):
        for file in os.listdir(self.path):
            if 'cubit' in file and '.jou' in file:
                os.remove(self.abs(file))

    def rm(self, file):
        for key in self.musthave:
            if file == self.musthave[key]:
                raise PermissionError('{} нельзя стирать!'.format(file))
        if os.path.exists(self.abs(file)):
            os.remove(self.abs(file))


    def load(self, filename):
        if not filename:
            filename = self.source
        filename = self.abs(filename)
        ext = filename.split('.')[1]

        self.cmd('reset')
        if ext=='stp':
            return self.cmd(r'import step "{}" heal no_surfaces no_curves no_vertices'.format(filename))
        elif ext=='fds':
            return self.cmd(r'open "{}"'.format(filename))
        else:
            print('Неопознанное расширение .{}'.format(ext))



    def save(self,filename='model.fds'):
        self.cmd(r'save as "{}" overwrite'.format(self.abs(filename)))


    def is_mesh(self):
        return len(self.get_not_meshed_volumes()) == 0


    def get_not_meshed_volumes(self):
        volumes = self.cubit.get_entities('volume')
        return [
            str(vol) 
            for vol in volumes
            if not self.cubit.is_meshed('volume', vol)
        ]
