#%% Imports

import sys
import os

os.chdir('D:\\TallesArquivos\\Documents\\FotonicaArquivos\\raman\\curvas')
sys.path.append('../')

from fdtdlib import fdtd_lib as flib

#%% Cristal
crystal = flib.Crystal('curvas')

#%% Lumerical
f = flib.Fdtd()

#%%

f.add_crystal(crystal)
f.add_fdtd()
f.add_movie()

#%%
f.fdtd.save("fdtd_file.fsp")
f.fdtd.run()