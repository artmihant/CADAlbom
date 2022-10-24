#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from os.path import join
import re
import sys
import shutil
from pathtree import PathTree
from datetime import datetime
from smb.SMBConnection import SMBConnection
from smb.SMBHandler import SMBHandler
import hglib
from state import State
import subprocess

PATHTREE = ['/home','fidesys', {
    'cluster':[{
        'smb.ini':'',
        'testers.ini':'',
        'log':'log.txt',
        'hg_testers':['fidesys-testers',{
            'cluster_logs':''
        }],
        'hg_cluster':'fidesys-testers-cluster',
        'hg_calclogs':['logs',{
            'calclogs.ini':'',
            'hg_logs_alpha':'alpha',
            'hg_logs_beta':'beta',
            'hg_logs_gamma':'gamma',
            'hg_logs_delta':'delta',
        }],
        'yandex.disk':[{
            'installer_dir':['fidesys_runfile',{
                'installer.ini':''
            }],
        }]
    }]
}]

Path = PathTree(PATHTREE)

INSTALLER = {
    'regalar_name_format': r'CAE-Fidesys-.*.exe',
    'hash_prefix': 'md5',
    'regalar_date_format': r'\d{4}-\d{2}-\d{2}'
}

TESTERS = {
    'branch_testers': 'default',
    'branch_cluster': 'default',
    'limit': 10,
    'folders': ['AAAA','python_autotests','CRITERIA']
}

CALCLOGS = {
    'commentary_format': r'version: ([0-9.]+),',
    'branch_testers': 'default',
    'logs_path_pref': 'hg_logs_',
    'logs':{'alpha':'E1N3','beta':'E1N4','gamma':'E2N4','delta':'WSFM'},
    'common': ['main_log.txt', 'failed_tests.txt', 'main_json_log.txt']
}

def log(message):
    print(message)
    with open(Path('log'), "a") as file:
        file.write(message)

def now():
    return datetime.now().isoformat(sep='|')


def check_installer(setting):
    """Сверяет последний инсталлер на наоми с локальным. Если не совпадает, скачивает. 
    Пишет в лог и сопровождающий файл инсталлера"""
    print("| Start check installer")

    installer_state = State(Path('installer.ini'))
    date_path = installer_state['naomi']

    smb_state = State(Path('smb.ini'))
    smb = SMBConnection(
        smb_state['user'], 
        smb_state['pass'], 
        smb_state['client'].encode('ascii'), 
        smb_state['server'].encode('ascii')
    )
    smb.connect(smb_state['server'])

    date_list = [item.filename 
        for item in smb.listPath(smb_state['share'], date_path)]

    date_list.sort(reverse=True)

    for date in date_list:

        if not re.match(setting['regalar_date_format'], date):
            continue

        date_path = join(date_path, date)

        files = [item.filename for item in smb.listPath(smb_state['share'], date_path)]

        for file in files:
            if re.match(setting['regalar_name_format'], file):
                name = file[:-4]

                installer_state = State(Path('installer.ini'))
                local_name = installer_state['name']

                if name != local_name and installer_state['update_installer']:

                    log("\nDownload new file {} | ".format(file))
                    with open(Path('installer_dir',file),'wb+') as installer_file:
                        smb.retrieveFile(smb_state['share'], join(date_path, file), installer_file)

                    installer_state['name'] = name
                    installer_state['update'] = now()
                    installer_state['version'] = re.search('([0-9.]+)-', name).group(1)
                    log("\nupdate installer {} {}".format(name, now()))

                    return True
                else:
                    print("| Installer is actual")
                    return False

    log("\nFiles fidesys installer not found on naomi server!")
    return False


def copydir(begin,end):
    if os.path.exists(end):
        shutil.rmtree(end)
    shutil.copytree(begin, end)


def check_testers(setting):
    print("| Start check testers")
    branch = setting['branch_testers']
    hg = hglib.open(Path('hg_testers'))
    hg.pull()
    rev = hg.log(branch=branch,limit=1)[0]
    # 0: number, 1: hash, 2: tip, 3: branch, 4: author, 5: message, d: datetime

    state = State(Path('testers.ini'))

    local_hash = state['hash']

    if rev[1] != local_hash:

        hg.update(rev=rev[0],clean=True)
        hg.close()

        #---#
        hg = hglib.open(Path('hg_cluster'))

        branch = setting['branch_cluster']
        hg.pull(branch=branch)
        hg.update(clean=True)
        
        for folder in os.listdir(Path('hg_testers')): 
            if os.path.isdir(Path('hg_testers',folder)) and folder != '.hg':
                copydir(Path('hg_testers',folder),Path('hg_cluster',folder))

        try:
            hg.addremove()
            hg.commit(message=rev[5], addremove=True)
            log("{} : commit, message:\n {} | {}".format(now(), rev[5], hg.push()))
        except hglib.error.CommandError:
            log("{} : up but not commited".format(now()))
        hg.close()

        #---#

        state['hash'] = rev[1]
        state['update'] = now()
        state['rev'] = rev[0]

        return True
    print("| Testers is actual")
    return False


def check_calclogs(setting):
    print("| Start check calclogs")
    state = State(Path('calclogs.ini'))

    flag_update = False    
    commit = {}

    hg_testers = hglib.open(Path('hg_testers'))
    hg_testers.pull(branch=setting['branch_testers'])
    hg_testers.update(clean=True)

    for key in setting['logs']:
        path = Path(setting['logs_path_pref']+key)
        hg = hglib.open(path)
        hg.pull()
        local_hash = state[key+'_hash']
        branch = 'logs-'+key
        current_rev = hg.log(branch=branch,limit=1)[0]
        hg.update(rev=current_rev[0], clean=True)
        hg.close()

        if current_rev[1] != local_hash:
            print('Calc complited: {}!'.format(current_rev[5]))
            flag_update = True
            commit[key] = current_rev[5]
            state[key+'_hash'] = current_rev[1]

            #---#
            logs_path = join(path,'logs')
            date = datetime.now().strftime("%d-%m-%Y")
            version = re.search(setting['commentary_format'], current_rev[5]).group(1)

            version_path = Path('cluster_logs', version)
            if not os.path.exists(version_path):
                os.makedirs(version_path)
            
            installer = State(Path('installer.ini'))
            
            if installer['overwrite_logs']:
                folders = os.listdir(Path('cluster_logs'))
                for folder in folders:

                    if folder != version:
                        shutil.rmtree(Path('cluster_logs',folder))

            files = os.listdir(logs_path)

            for file in files:
                if file in setting['common'] or file in os.listdir(version_path):
                    shutil.copy(join(logs_path,file), join(version_path, setting['logs'][key]+'_'+file))
                else:
                    shutil.copy(join(logs_path,file), version_path)

    if flag_update:
        hg_testers.addremove()
        try:
            message = ''
            for key in commit:
                message = message+'\n'+setting['logs'][key]+': '+commit[key]
            hg_testers.commit(message=message)
            hg_testers.push()
            log("\n update calc logs:{}".format(message))
        except hglib.error.CommandError:
            print(message)
            print('nothing changed!')
    else:
        print("| Calclogs is actual")


if __name__ == '__main__':

    subprocess.check_call(['yandex-disk','start'])
    check_installer(INSTALLER)
    check_testers(TESTERS)
    check_calclogs(CALCLOGS)


