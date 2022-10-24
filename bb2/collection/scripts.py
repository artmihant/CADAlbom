#!/usr/bin/env python
# -*- coding: utf-8 -*-

def loadsave(model):
    model.load('model.stp')
    model.vol()
    model.save('model.fds')

def load(model):
    model.load('model.stp')

def mesh1(model):
    model.load('merge.fds')
    model.cmd('volume all scheme auto')
    model.cmd('mesh volume all')
    return check_mesh(model, 'mesh1')

def mesh2(model):
    model.load('merge.fds')
    model.cmd('volume all scheme tetmesh')
    model.cmd('mesh volume all')
    return check_mesh(model, 'mesh2')


def check_mesh(model,iter):
    """Проверяет, построилась ли сетка"""
    model['mesh'] = model.is_mesh()

    if not 'mesh_iter' in model:
        model['mesh_iter'] = dict()

    model['mesh_iter'][iter] = model['mesh']

    if model['mesh']:
        model.save('mesh.fds')
    else:
        print(model.get_not_meshed_volumes(), len(model.get_not_meshed_volumes()))

    return model['mesh']


def mesh4(model, prime=['all'],count=1000):
    model.load('merge.fds')
    model.cmd('volume all scheme tetmesh')
    model.cmd('mesh volume {}'.format(' '.join(prime)))
    if model.get_not_meshed_volumes():
        model.cmd('mesh volume {}'.format(' '.join(model.get_not_meshed_volumes())))
    check_mesh(model,'mesh4')
    if not model['mesh']:
        unmeshed = model.get_not_meshed_volumes()
        print unmeshed
        if len(unmeshed) < count:
            mesh4(model, prime=unmeshed, count=len(unmeshed))
    return model['mesh']


def mesh3(model):
    model.load('merge.fds')
    model.cmd(r'delete body with is_sheetbody = True')
    model.cmd('compress all')
    model.cmd('delete mesh volume all propagate')
    model.cmd('healer autoheal body all rebuild maketolerant')
    model.cmd('volume all scheme tetmesh')
    model.cmd('mesh volume all')
    return check_mesh(model, 'mesh3')


def imprintmerge(model):
    model.load('model.fds')
    model.cmd(r'delete body with is_sheetbody = True')
    model.cmd('imprint all')
    model['imprintmerge'] = model.cmd('merge all')
    model.vol()

    if model['imprintmerge']:
        model.save('merge.fds')
    
    return model['imprintmerge']

def imprintmerge2(model):
    model.load('model.fds')
    model.cmd('Volume all scale 1000.0')
    model.cmd(r'delete body with is_sheetbody = True')
    model.cmd('imprint all')
    model['imprintmerge'] = model.cmd('merge all')
    model.cmd('Volume all scale 0.001 ')
    model.vol()

    if model['imprintmerge']:
        model.save('merge.fds')
    
    return model['imprintmerge']




# def imprintmerge(model):
#     if model.vol() == 0:
#         model['count'] = 0
#         model['imprintmerge'] = 0
#     elif model.vol() == 1:
#         model['count'] = 1
#         model['imprintmerge'] = 1
#     elif model.vol() > 1:
#         model['count'] = 2
#         model.cmd('imprint all')
#         model['imprintmerge'] = model.cmd('merge all')
#     else:
#         model['count'] = -1
#         model['imprintmerge'] = -1
#     return model['imprintmerge']
