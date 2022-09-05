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

dir_path = 'weights/'

def blocks(files, size=65536):
    while True:
        b = files.read(size)
        if not b: break
        yield b
 
def copyfromftp():
    ftp = FTP()
    HOST = 'ftp2.bipm.org'
    PORT = 21
    ftp.connect(HOST, PORT)
    ftp.login()

    ftp.cwd('/pub/tai/other-products/weights/')
    #ftp.retrlines('LIST')
    files = []
    try:
        files = ftp.nlst()
    except FTP.error_perm as resp:
        if str(resp) == "550 No files found":
            print("No files in this directory")
        else:
            raise
    for f in files:
        print(f)
        
    for fname in files:        
        if 'w' in fname:
            with open(dir_path+fname, 'wb') as f:
                ftp.retrbinary('RETR '+fname, f.write)
                f.close()
    ftp.quit()
    
    return files
    
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
                    if "(***** DENOTES THAT THE CLOCK WAS NOT USED)" in line:
                        flag = 1
                    ind_list.append(i)
                if ("RELATIVE WEIGHTS" in line or "LAB." in line 
                    or "             " in line):
                    ind_list.append(i)
                if "LAB." in line:
                    mjdline = line
                if "Total weight" in line or "The clocks are designated" in line:
                    end_ind = i
                i += 1
        mjds = mjdline.split()
        print(mjds)
        for i in range(end_ind, num_of_lines):
            ind_list.append(i)    
    
        df = pd.read_csv(fname, sep=' ', index_col=False, skip_blank_lines=True, skipinitialspace=True, skiprows=ind_list, 
                     na_values='*****', names=['lab', 'type', 'code', mjds[2], mjds[3], mjds[4], mjds[5], mjds[6], mjds[7], 'x']).fillna(0)
        df = df.drop('x', axis=1)
        df['code'] = df['type'].astype(int).astype(str) + df['code'].astype(int).astype(str)
        df['code'] = df['code'].astype(int)
    except Exception as e:
        print(e)
    return df

files = copyfromftp()

files = []
for path in os.listdir(dir_path):
    # check if current path is a file
    if os.path.isfile(os.path.join(dir_path, path)):
        files.append(path)
yy = 0
ffiles = []
while yy < 23:    
    fname = 'w' + str(yy).zfill(2) + '.01'
    if fname in files:
        ffiles.append(fname) 
    fname = 'w' + str(yy).zfill(2) + '.07'
    if fname in files:
        ffiles.append(fname)         
    yy += 1
    
#df = pd.DataFrame({'lab':[],'type':[], 'code':[], 'lcode':[]})
df = pd.DataFrame({'lab':[],'type':[], 'code':[]})
for fname in ffiles:
    if 'w' in fname:
        df1 = fproc(dir_path+fname)
        df = df.merge(df1, how='outer', on=['code', 'lab', 'type']).fillna(0)

header = list(df)
df['model'] = df['code'].apply(lambda x: str(x)[2:4] if str(x)[0:2]=="41" else 0)
df['model'] = df['model'].astype(int)
mjds = header[-12*2:-1]
mhm2010 = []
mhm2020 = []
vch1003m = []
vch1008 = []
codes_mhm2010 = []
codes_mhm2020 = []
codes_vch1003m = []
codes_vch1008 = []
num_mhm2010 = []
num_mhm2020 = []
num_vch1003m = []
num_vch1008 = []
for mjd in mjds:
    
    tmp = df[(df['model'] == 20) & (df[mjd] > 0)]
    codes_mhm2010.extend(list(tmp['code']))    
    mhm2010.append(np.mean(tmp[mjd]))
    num_mhm2010.append(len(tmp[mjd]))
    
    tmp = df[(df['model'] == 21) & (df[mjd] > 0)]
    codes_mhm2020.extend(list(tmp['code']))    
    mhm2020.append(np.mean(tmp[mjd]))
    num_mhm2020.append(len(tmp[mjd]))
    
    tmp = df[(df['model'] == 53) & (df[mjd] > 0)]    
    codes_vch1003m.extend(list(tmp['code']))    
    vch1003m.append(np.mean(tmp[mjd]))    
    num_vch1003m.append(len(tmp[mjd]))
    
    tmp = df[(df['model'] == 52) & (df[mjd] > 0)]
    codes_vch1008.extend(list(tmp['code']))    
    vch1008.append(np.mean(tmp[mjd]))
    num_vch1008.append(len(tmp[mjd]))

print('Codes of MHM2010:', set(codes_mhm2010))
print('Codes of MHM2020:', set(codes_mhm2020))
print('Codes of VCH1003M:', set(codes_vch1003m))
print('Codes of VCH1008:', set(codes_vch1008))

plt.figure(1)
plt.title('Aveage clock weights in TAI, %')
plt.plot(mjds, mhm2010, mjds, mhm2020, mjds, vch1003m, mjds, vch1008)
plt.xticks(rotation=45)
plt.legend(['MHM2010', 'MHM2020', 'VCH1003M', 'VCH1008 - passive H-maser'])
plt.figure(2)
plt.title('Number of clocks participating in TAI')
plt.plot(mjds, num_mhm2010, mjds, num_mhm2020, mjds, num_vch1003m, mjds, num_vch1008)
plt.legend(['MHM2010', 'MHM2020', 'VCH1003M', 'VCH1008 - passive H-maser'])
plt.xticks(rotation=45)