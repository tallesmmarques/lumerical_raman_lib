#%% Variaveis

import numpy as np
import time
import os
import importlib.util

nome_projeto = "section1"
base_file = "D:\TallesArquivos\Documents\FotonicaArquivos\raman\raman_base.fsp"
a = 0.426E-6 # lattice constant
h = a*np.sqrt(3)/2
zspan = 0.36E-6

#%% Inicializacao

os.add_dll_directory('C:\\Program Files\\Lumerical\\v202\\api\\python')
spec_win = importlib.util.spec_from_file_location(
    'lumapi', 'C:\\Program Files\\Lumerical\\v202\\api\\python\\lumapi.py')
lumapi = importlib.util.module_from_spec(spec_win)  
spec_win.loader.exec_module(lumapi)

f = lumapi.FDTD(filename = f'{nome_projeto}.fsp')

#%% Interpretacao do arquivo

f.switchtolayout()
f.groupscope("::model")

with open(f'{nome_projeto}.txt') as file:
  pc = file.read()

matrix = []
vector = []

for char in pc:
  if char == '\n':
    matrix.append(vector)
    vector = []
  elif char == " ": continue
  else: vector.append(char)
  
matrix = np.flip(np.array(matrix), 0)

#%% Criacao do cristal

f.groupscope("::model")
curva_id = 0
source_id = 0
monitor_int_id = 0
monitor_id = 0

f.select("curvas")
f.delete()
f.addstructuregroup()
f.set("name", "curvas")
f.set("x", 0)
f.set("y", 0)
f.set("z", 0)

f.groupscope("hex_pc")
f.set("construction group", True)
f.set("script", "")

nx        = len(matrix[0])
ny        = len(matrix)
zspan     = f.get("z span")
material  = f.get("material")

f.set("nx",nx)
f.set("ny",ny)

script = ""
script += 'deleteall; \n\n'

for lindex, linha in enumerate(matrix):
  for cindex, hole in enumerate(linha):
    if hole == ".": 
      continue
    
    elif hole in ["0", "1", "2", "3"]:
      script += 'addcircle; \n'
      
      if hole == "0":
        script += 'set("radius", {}); \n'.format(0.30*a)
      elif hole == "1":
        script += 'set("radius", {}); \n'.format(0.38*a)
      elif hole == "2":
        script += 'set("radius", {}); \n'.format(0.20*a)
      elif hole == "3":
        script += 'set("radius", {}); \n'.format(0.16*a)
      else:
        script += 'set("radius", {}); \n'.format(a)
      
      if lindex % 2 == 1: # i­mpar
        script += 'set("x", {}); \n'.format((cindex)*a + a/2)
      else: # par
        script += 'set("x", {}); \n'.format((cindex)*a)
      
      script += 'set("y", {}); \n'.format((lindex)*h)
      
      script += 'set("z", {}); \n'.format(0)
      script += 'set("z span", {}); \n'.format(zspan)
      script += 'set("material", "{}"); \n'.format(material)
      script += '\n'
    
    elif hole in ["f", "F"]:
      f.groupscope("::model")

      f.select("curva_fora")
      f.copy()
      f.addtogroup("curvas")
      
      f.groupscope("curvas")
      f.select("curva_fora")
      f.set("name", f"curva_{curva_id}")

      f.select(f"curva_{curva_id}")
      
      if lindex % 2 == 1: # i­mpar
        f.set("x", cindex*a + a/2)
      else: # par
        f.set("x", cindex*a)
        
      f.set("y", lindex*h)
      f.set("z", 0)
      if hole == "F":
        f.set("first axis", "z")
        f.set("rotation 1", 120)

      f.set("enabled", 1)

      curva_id = curva_id + 1
      f.groupscope("::model::hex_pc")
      
    elif hole in ["d", "D"]:
      f.groupscope("::model")

      f.select("curva_dentro")
      f.copy()
      f.addtogroup("curvas")
      
      f.groupscope("curvas")
      f.select("curva_dentro")
      f.set("name", f"curva_{curva_id}")

      f.select(f"curva_{curva_id}")
      
      if lindex % 2 == 1: # i­mpar
        f.set("x", cindex*a + a)
      else: # par
        f.set("x", cindex*a + a/2)
        
      f.set("z", 0)
      if hole == "d":
        f.set("first axis", "z")
        f.set("rotation 1", 120)
        f.set("y", lindex*h + h)
      else:
        f.set("y", lindex*h - h)

      f.set("enabled", 1)

      curva_id = curva_id + 1
      f.groupscope("::model::hex_pc")
      
    elif hole == "b":
      f.groupscope("::model")

      f.select("curva_inf")
      f.copy()
      f.addtogroup("curvas")
      
      f.groupscope("curvas")
      f.select("curva_inf")
      f.set("name", f"curva_{curva_id}")

      f.select(f"curva_{curva_id}")
      
      if lindex % 2 == 1: # i­mpar
        f.set("x", cindex*a + a/2)
      else: # par
        f.set("x", cindex*a)
        
      f.set("z", 0)
      f.set("y", lindex*h)

      f.set("enabled", 1)

      curva_id = curva_id + 1
      f.groupscope("::model::hex_pc")
      
    elif hole == "B":
      f.groupscope("::model")

      f.select("curva_sup")
      f.copy()
      f.addtogroup("curvas")
      
      f.groupscope("curvas")
      f.select("curva_sup")
      f.set("name", f"curva_{curva_id}")

      f.select(f"curva_{curva_id}")
      
      if lindex % 2 == 1: # i­mpar
        f.set("x", cindex*a + a/2)
      else: # par
        f.set("x", cindex*a)
        
      f.set("z", 0)
      f.set("y", lindex*h)

      f.set("enabled", 1)

      curva_id = curva_id + 1
      f.groupscope("::model::hex_pc")
      
    elif hole == "s":
      f.groupscope("::model")
      
      f.select(f"source_{source_id}")
      f.delete()

      f.select("source")
      f.copy()
      f.addtogroup("::model")
      
      f.set("name", f"source_{source_id}")
      f.select(f"source_{source_id}")
      
      if lindex % 2 == 1: # i­mpar
        f.set("x", cindex*a + a/2 - 1.5*a)
      else: # par
        f.set("x", cindex*a - 1.5*a)
        
      f.set("z", 0)
      f.set("y", lindex*h)

      f.set("enabled", 1)

      source_id = source_id + 1
      f.groupscope("::model::hex_pc")
      
    elif hole == "m":
      f.groupscope("::model")
      
      f.select(f"monitor_int_{monitor_int_id}")
      f.delete()

      f.select("monitor_int")
      f.copy()
      f.addtogroup("::model")
      
      f.set("name", f"monitor_int_{monitor_int_id}")
      f.select(f"monitor_int_{monitor_int_id}")
      
      if lindex % 2 == 1: # i­mpar
        f.set("x", cindex*a + a/2)
      else: # par
        f.set("x", cindex*a)
        
      f.set("z", 0)
      f.set("y", lindex*h)

      f.set("enabled", 1)

      monitor_int_id = monitor_int_id + 1
      f.groupscope("::model::hex_pc")
    
    elif hole == "M":
      f.groupscope("::model")
      
      f.select(f"monitor_{monitor_id}")
      f.delete()

      f.select("monitor_end")
      f.copy()
      f.addtogroup("::model")
      
      f.set("name", f"monitor_{monitor_id}")
      f.select(f"monitor_{monitor_id}")
      
      if lindex % 2 == 1: # i­mpar
        f.set("x", cindex*a + a/2 + 1.5*a)
      else: # par
        f.set("x", cindex*a + 1.5*a)
        
      f.set("z", 0)
      f.set("y", lindex*h)

      f.set("enabled", 1)

      monitor_id = monitor_id + 1
      f.groupscope("::model::hex_pc")
      
f.set("script", script)

#%% Demais componentes

f.groupscope("::model")

lx = (nx+7)*a
ly = (ny+5)*h

cx = (nx/2 - 0.5)*a
cy = (ny/2 - 0.5)*h

zspan = 0.36E-6

f.select("rec_bac")
f.set("x", cx)
f.set("x span", lx)
f.set("y", cy)
f.set("y span", ly)
f.set("z", 0)
f.set("z span", zspan)

f.select("FDTD")
f.set("x", cx)
f.set("x span", lx)
f.set("y", cy)
f.set("y span", ly)
f.set("z", 0)

f.select("dielectric_monitor")
f.set("x", cx)
f.set("x span", lx)
f.set("y", cy)
f.set("y span", ly)
f.set("z", 0)

f.select("dielectric_monitor")
f.set("x", cx)
f.set("x span", lx)
f.set("y", cy)
f.set("y span", ly)
f.set("z", 0)

f.select("field_monitor")
f.set("x", cx)
f.set("x span", lx)
f.set("y", cy)
f.set("y span", ly)
f.set("z", 0)

f.save()
