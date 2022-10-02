# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 16:55:40 2022

@author: mishagin.k
"""
import requests
import matplotlib.pyplot as plt
from ftplib import FTP
import pandas as pd
import numpy as np
import os



def blocks(files, size=65536):
    while True:
        b = files.read(size)
        if not b: break
        yield b
 
def copyfromftp(key, dir_path):
    ftp = FTP()
    HOST = 'ftp2.bipm.org'
    PORT = 21
    ftp.connect(HOST, PORT)
    ftp.login()

    if key == 'w':
        ftp.cwd('/pub/tai/other-products/weights/')        
    elif key == 'd':
        ftp.cwd('/pub/tai/other-products/clkdrifts/')        
    else:
        return []
    
    ftp_files = []
    try:
        ftp_files = ftp.nlst()
    except FTP.error_perm as resp:
        if str(resp) == "550 No files found":
            print("No files in this directory")
        else:
            raise
    
    already_copied = os.listdir(dir_path)
    new_copied = []
    for fname in ftp_files :        
        if key in fname and fname not in already_copied:
            with open(dir_path+fname, 'wb') as f:
                ftp.retrbinary('RETR '+fname, f.write)
                f.close()
                new_copied.append(fname)
    ftp.quit()
    
    return new_copied
    
def fproc(fname):    
    df = pd.DataFrame({'lab':[],'type':[], 'code':[]})
    try: 
        num_of_lines = 0    
        with open(fname, "r", encoding="utf-8", errors='ignore') as f:
            num_of_lines = sum(bl.count("\n") for bl in blocks(f))    
            
        ind_list = []        
        i = 0
        flag = 0
        with open(fname, "r", encoding="utf-8", errors='ignore') as f:
            for line in f:
                if flag == 0:
                    if "DENOTES THAT" in line:
                        flag = 1
                    ind_list.append(i)
                if ("RELATIVE WEIGHTS" in line or "LAB." in line 
                    or "             " in line):
                    ind_list.append(i)
                if "LAB." in line:
                    mjdline = line
                if ("Total weight" in line or "The clocks are designated" in line 
                    or "The clocks codes are defined" in line):
                    end_ind = i
                i += 1
        mjds = mjdline.split()
        print(mjds)
        for i in range(end_ind, num_of_lines):
            ind_list.append(i)    
    
        df = pd.read_csv(fname, sep=' ', index_col=False, skip_blank_lines=True, skipinitialspace=True, skiprows=ind_list, on_bad_lines='skip',
                     na_values=['*****', '*********'], names=['lab', 'type', 'code', mjds[2], mjds[3], mjds[4], mjds[5], mjds[6], mjds[7], 'x']).fillna(0)
        df = df.drop('x', axis=1)
        df = df[df.lab != 0]
        df['code'] = df['type'].astype(int).astype(str) + df['code'].astype(int).astype(str)
        df['code'] = df['code'].astype(int)
    except Exception as e:
        print(e)
    return df

def compareMasers(df, listOfModels, modelNames):
    header = list(df)
    df['model'] = df['code'].apply(lambda x: str(x)[2:4] if str(x)[0:2]=="41" else 0)
    df['model'] = df['model'].astype(int)
    mjds = header[-12*2:-1]
    prod_for_models = []
    codes_for_models = []    
    num_for_models = []
    
    for clck_model in listOfModels:
        codes = []
        prod = []
        num = []        
        for mjd in mjds:
            tmp = df[(df['model'] == clck_model) & (df[mjd] != 0) & (np.abs(df[mjd]) < 100)]
            codes.extend(list(tmp['code']))
            prod.append(np.mean(tmp[mjd]))
            #prod.append(np.std(tmp[mjd]))
            #prod.append(np.mean(np.abs(tmp[mjd])))
            num.append(len(tmp[mjd]))        
        codes_for_models.append(set(codes))
        prod_for_models.append(prod)
        num_for_models.append(num)            

    plt.figure(1)
    plt.title('Aveage clock weights in TAI, %')
    #plt.title('Mean absolute value of clock drifts, ns/day/30days')    
    for i in range(len(listOfModels)):
        plt.plot(mjds, prod_for_models[i])
    plt.xticks(rotation=45)
    plt.legend(modelNames)
    plt.figure(2)
    plt.title('Number of clocks participating in TAI')
    for i in range(len(listOfModels)):
        plt.plot(mjds, num_for_models[i])
    plt.legend(modelNames)
    plt.xticks(rotation=45)
    
    return prod_for_models, codes_for_models, num_for_models, mjds    
    

#dir_path = 'drifts/'
#key = 'd'
dir_path = 'weights/'
key = 'w'
if not os.path.exists(dir_path):
    os.makedirs(dir_path)
    

files = copyfromftp(key, dir_path)
if len(files) > 0:
    print(files)

files = []
for path in os.listdir(dir_path):
    # check if current path is a file
    if os.path.isfile(os.path.join(dir_path, path)):
        files.append(path)
yy = 0
ffiles = []
while yy < 23:    
    fname = key + str(yy).zfill(2) + '.01'
    if fname in files:
        ffiles.append(fname) 
    fname = key + str(yy).zfill(2) + '.07'
    if fname in files:
        ffiles.append(fname)         
    yy += 1
    
#df = pd.DataFrame({'lab':[],'type':[], 'code':[], 'lcode':[]})
df = pd.DataFrame({'lab':[],'type':[], 'code':[]})
for fname in ffiles:
    if key in fname:
        df1 = fproc(dir_path+fname)
        df = df.merge(df1, how='outer', on=['code', 'lab', 'type']).fillna(0)

listOfModels = [20, 21, 53, 52]
#namesOfModels = ['MHM2010', 'MHM2020', 'VCH1003M', 'VCH1008 - passive H-maser']
#prod_for_models, codes_for_models, num_for_models, mjds = compareMasers(df, listOfModels, namesOfModels)

header = list(df)
mjds = header[-12*22:-1]

impact_cs = []
num_cs = []
impact_h = []
num_h = []
for mjd in mjds:    
    
    tmp = df[((df['type'] < 40) | ((df['type'] > 41) & (df['type'] <= 53))) & (df[mjd] > 0)]        
    impact_cs.append(np.sum(tmp[mjd]))
    num_cs.append(len(tmp[mjd]))
    
    tmp = df[((df['type'] == 40) | (df['type'] == 41)) & (df[mjd] > 0)]        
    impact_h.append(np.sum(tmp[mjd]))
    num_h.append(len(tmp[mjd]))

# from matplotlib.ticker import MaxNLocator
# fig, axes = plt.subplots(1,1)
# axes.xaxis.set_major_locator(MaxNLocator(10)) 
# plt.plot(mjds, impact_cs, mjds, impact_h)
# plt.title("Вклад в международное атомное время")
# plt.xlabel("Дата, MJD")
# plt.ylabel("%")
# plt.legend(["Цезиевые стандарты", "Водородные стандарты"])
# plt.locator_params(nbins=10)
# fig, axes = plt.subplots(1,1)
# axes.xaxis.set_major_locator(MaxNLocator(10))
# plt.plot(mjds, num_cs, mjds, num_h)
# plt.locator_params(nbins=10)

from astropy.time import Time
listdt = Time(mjds, format='mjd', scale='utc').datetime
dstrlist = []
for t in listdt:
    dstrlist.append(t.strftime('%Y-%m-%d'))

import plotly.graph_objects as go
fig = go.Figure()
fig.add_trace(go.Scatter(x=dstrlist, y=impact_cs, name="Цезиевые стандарты", mode='lines'))
fig.update_layout(legend_orientation="h",
                  legend=dict(x=.5, xanchor="center"),
                  title="Вклад в международное атомное время",                  
                  yaxis_title="%")
fig.show()
