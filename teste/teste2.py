#%% Imports

import sys
import os

sys.path.append('../')
os.chdir('D:\\TallesArquivos\\Documents\\FotonicaArquivos\\raman\\teste')

from fdtdlib import fdtd_lib as flib

#%% Cristal
crystal_test2 = flib.Crystal('test2')

#%% Lumerical
f = flib.Fdtd()

#%%

f.add_crystal(crystal_test2)
f.add_fdtd()
f.add_movie()

#%%
f.fdtd.save("fdtd_file.fsp")
f.fdtd.run()