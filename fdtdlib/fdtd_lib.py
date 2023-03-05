import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from scipy import interpolate
from collections import OrderedDict

import importlib.util
import os
import shutil

os.add_dll_directory('C:\\Program Files\\Lumerical\\v202\\api\\python')
spec_win = importlib.util.spec_from_file_location(
    'lumapi', 'C:\\Program Files\\Lumerical\\v202\\api\\python\\lumapi.py')
spec_lin = importlib.util.spec_from_file_location(
    'lumapi', "/opt/lumerical/2020a/api/python/lumapi.py")
spec_mac = importlib.util.spec_from_file_location(
    'luampi', "/Applications/Lumerical/FDTD Solutions/FDTD Solutions.app/Contents/API/Python/lumapi.py")

lumapi = importlib.util.module_from_spec(spec_win)
spec_win.loader.exec_module(lumapi)

class Crystal(object):
  def __init__(self, name, x=5, y=5, a=0.426E-6, zspan=0.40E-6):
    self.name = name
    self.x = x
    self.y = y
    self.model = ""
    self.first_null = False
    self.a = a
    self.zspan = zspan
    
    if os.path.exists(f'{self.name}_crystal_model.txt'):
      self.read_crystal_file()
      print(f'[log] Modelo atualizado com base no arquivo {self.name}_crystal_model.txt')
    else: 
      self.make_crystal_file()
      print(f'[log] Projete o cristal no arquivo {self.name}_crystal_model.txt',
            "\n      ou corrija as dimenções x e y e execute make_crystal_file() novamente")
      
  def __str__(self):
    self.read_crystal_file()
    return self.model
  
  def __iter__(self):
    self.iter_aux = 0
    return self
  
  def __next__(self):
    if self.iter_aux < self.y:
      line = self.model.splitlines()[self.iter_aux].split()
      self.iter_aux += 1
      return line
    else:
      raise StopIteration
      
  def make_crystal_file(self, x=-1, y=-1):
    x = self.x if x == -1 else x
    y = self.y if y == -1 else y
    
    self.model = ""
    for row in range(y): 
      tmp_row = row + 1 if not ((y % 2 == 1) == self.first_null) else row
      for col in range(x):
        self.model += " 0" if tmp_row % 2 == 0 else "0 "
      self.model += "\n"
    
    if os.path.exists(f'{self.name}_crystal_model.txt'):
      i = 1
      try: os.mkdir("backups")
      except: pass
    
      while os.path.exists(f'backups\\{self.name}_crystal_model_bkp{i}.txt'):
        i += 1
        
      shutil.copyfile(f'{self.name}_crystal_model.txt', 
                      f'backups\\{self.name}_crystal_model_bkp{i}.txt')
      print("[log] arquivo antigo salvo em backup")
      
    with open(f'{self.name}_crystal_model.txt', 'w') as file:
      file.write(self.model)

  def read_crystal_file(self):
    self.model = ''
    tmp_model = ''
    with open(f'{self.name}_crystal_model.txt') as file:
      tmp_model = file.read()
      
    tmp_model += '\n'
    for line in tmp_model.splitlines(keepends=True):
      if line.isspace(): continue
      self.model += line
      
    self.x = len(max(self.model.replace(' ', '').splitlines(), key=len))
    self.y = len(self.model.splitlines())
      
    if self.model.splitlines()[-1][0] == ' ':
      self.first_null = True      

  def expand_x(self, n=1):
    self.read_crystal_file()
    
    tmp_model = self.model
    self.model = ''
    for line in tmp_model.splitlines():
      for __n in range(n):
        line += line[-2:]
      line += '\n'
      self.model += line
      
    with open(f'{self.name}_crystal_model.txt', 'w') as file:
      file.write(self.model)
      
  def reduce_x(self, n=1):
    self.read_crystal_file()
    
    tmp_model = self.model
    self.model = ''
    for line in tmp_model.splitlines():
      for __n in range(n):
        line = line[:-2]
      line += '\n'
      self.model += line
      
    with open(f'{self.name}_crystal_model.txt', 'w') as file:
      file.write(self.model)
      
  def generate_matrix(self):
    self.read_crystal_file()
    matrix = []
    for line in self:
      matrix.append(line)
    matrix = np.flip(np.array(matrix), 0)
    
    return matrix
    
class Fdtd(object):
  def __init__(self, name="fdtd_file.fsp"):
    self.fdtd = lumapi.FDTD()
    self.structures = {}
    self.width = 0
    self.height = 0
        
    self.x_margin = 0.8E-6
    self.y_margin = 0.8E-6
    
    self.source_index = 0
    
    self.fdtd.importmaterialdb("D:\\TallesArquivos\\Documents\\FotonicaArquivos\\raman\\fdtdlib\\material.mdf");
  
  def get_type(self, simbol: str, rindex: int, cindex: int):
    if simbol == '0':
      return {'type': 'circle', 'radius': 0.30}
    elif simbol == '1':
      return {'type': 'circle', 'radius': 0.38}
    elif simbol == '2':
      return {'type': 'circle', 'radius': 0.20}
    elif simbol == '3':
      return {'type': 'circle', 'radius': 0.16}
    elif simbol == '4':
      return {'type': 'circle', 'radius': 0.40}
    elif simbol == '5':
      return {'type': 'circle', 'radius': 0.25}
    
    elif simbol == '.':
      return {'type': 'none'}
    
    elif simbol == 'c':
      return {'type': 'curve', 'radius': 0.38}
    
    elif simbol == 's':
      return {'type': 'source'}
      
    return {'type': 'none'}
  
  def add_crystal(self, crystal: Crystal):
    self.fdtd.select(crystal.name)
    self.fdtd.delete()
    
    pc = self.fdtd.addstructuregroup()
    pc.name = crystal.name
    pc.x = 0
    pc.y = 0
    pc.z = 0
    
    self.structures[crystal.name] = {
      'f': pc, 
      'crystal': crystal
    }
    
    a = crystal.a
    h = a*np.sqrt(3)/2
    matrix = crystal.generate_matrix()
    script = 'deleteall; \n\n'
    
    self.source_index = 0
    
    for rindex, row in enumerate(matrix):
      for cindex, simbol in enumerate(row):
        type = self.get_type(simbol, rindex, cindex)
        
        if type['type'] == 'none':
          continue
        elif type['type'] == 'circle':
          script += 'addcircle; \n'
          
          script += 'set("radius", {}); \n'.format(a * type['radius'])
          
          if not (rindex % 2 == 1) == crystal.first_null: # odd
            script += 'set("x", {}); \n'.format(cindex*a + a/2)
          else: # even
            script += 'set("x", {}); \n'.format(cindex*a)
          
          script += 'set("y", {}); \n'.format(rindex*h)
          
          script += 'set("z", {}); \n'.format(0)
          script += 'set("z span", {}); \n'.format(crystal.zspan)
          script += 'set("material", "{}"); \n'.format('etch')
          script += '\n'
          
        elif type['type'] == 'curve':
          script += 'addpoly; \n'
          r = a * type['radius']
          vtx = [
            (0,r), 
            (a,r), 
            (2.5*a + np.cos(np.deg2rad(120))*r, h + np.sin(np.deg2rad(120))*r),
            (3*a + np.cos(np.deg2rad(150))*r, 2*h + np.sin(np.deg2rad(150))*r),
            (3*a + np.cos(np.deg2rad(-30))*r, 2*h + np.sin(np.deg2rad(-30))*r),
            (2.5*a + np.cos(np.deg2rad(-60))*r + np.cos(np.deg2rad(30))*np.tan(np.deg2rad(15))*r,
             h + np.sin(np.deg2rad(-60))*r + np.sin(np.deg2rad(30))*np.tan(np.deg2rad(15))*r),
            (a + np.tan(np.deg2rad(15))*r, -r),
            (0,-r)
          ]
          
          circle_script = 'addcircle; \n\n'
          circle_type = self.get_type('2', rindex, cindex)
          circle_script += 'set("radius", {}); \n'.format(a * circle_type['radius'])
          
          circle_script += 'set("z", {}); \n'.format(0)
          circle_script += 'set("z span", {}); \n'.format(crystal.zspan)
          circle_script += 'set("material", "{}"); \n'.format('etch')
          
          x_desv = np.cos(np.deg2rad(-60))*a*1/3
          y_desv = np.sin(np.deg2rad(-60))*a*1/3
          
          if matrix[rindex+1][cindex-1] == '.' and matrix[rindex+1][cindex-0] == '.':
            # print("curva de 60° para 0° com ponto interno a curva")
            vtx = [(-x[0] + 1.5*a, -x[1] + h) for x in vtx]
            
          elif matrix[rindex+1][cindex-0] == '.' and matrix[rindex+1][cindex+1] == '.':
            # print("curva de -60° para 0° com ponto externo a curva")
            vtx = [(-x[0] + 2*a, x[1]) for x in vtx]
            x_desv *= -1
            
          elif matrix[rindex-1][cindex-1] == '.' and matrix[rindex-1][cindex-0] == '.':
            # print("curva de -60° para 0° com ponto interno a curva")
            vtx = [(-x[0] + 1.5*a, x[1] - h) for x in vtx]
            y_desv *= -1
            
          elif matrix[rindex-1][cindex-0] == '.' and matrix[rindex-1][cindex+1] == '.':
            # print("curva de 60° para 0° com ponto externo a curva")
            vtx = [(-x[0] + 2*a, -x[1]) for x in vtx]
            x_desv *= -1
            y_desv *= -1
            
            
          elif matrix[rindex+1][cindex-1] == '.':
            # print("curva para 60° com ponto externo a curva")
            vtx = [(x[0] - 2*a, x[1]) for x in vtx]
            
          elif matrix[rindex+1][cindex+1] == '.':
            # print("curva para -60° com ponto interno a curva")
            vtx = [(x[0] - 1.5*a, -x[1] + h) for x in vtx]
            x_desv *= -1
            
          elif matrix[rindex-1][cindex-1] == '.':
            # print("curva para -60° com ponto externo a curva")
            vtx = [(x[0] - 2*a, -x[1]) for x in vtx]
            y_desv *= -1
            
          elif matrix[rindex-1][cindex+1] == '.':
            # print("curva para 60° com ponto interno a curva")
            vtx = [(x[0] - 1.5*a, x[1] - h) for x in vtx]
            x_desv *= -1
            y_desv *= -1
            
          if not (rindex % 2 == 1) == crystal.first_null: # odd
            circle_script += 'set("x", {}); \n'.format(cindex*a + a/2 + x_desv)
          else: # even
            circle_script += 'set("x", {}); \n'.format(cindex*a + x_desv)
          
          circle_script += 'set("y", {}); \n'.format(rindex*h + y_desv)  
          
          vertices = '['
          for i, point in enumerate(vtx):
            if i != 0:
              vertices += ';'
            vertices += f'{point[0]},{point[1]}'
          vertices += ']'
          
          if not (rindex % 2 == 1) == crystal.first_null: # odd
            script += 'set("x", {}); \n'.format(cindex*a + a/2)
          else: # even
            script += 'set("x", {}); \n'.format(cindex*a)
          
          script += 'set("y", {}); \n'.format(rindex*h)
          
          script += 'set("vertices", {});'.format(vertices)
          script += 'set("z span", {}); \n'.format(crystal.zspan)
          script += 'set("material", "{}"); \n'.format('etch')
          
          script += circle_script
          
          script += '\n'
        
        elif type['type'] == 'source':
          self.source_index += 1
          self.fdtd.select(f'source_{self.source_index}')
          self.fdtd.delete()
          
          props = OrderedDict([("name", f'source_{self.source_index}'), 
                               ("amplitude", 2),
                               ('injection axis', 'x-axis'),
                               ('mode selection', 'fundamental TE mode'),
                               ("override global source settings", True),
                               ("wavelength start", 1550e-9),
                               ("wavelength stop", 1550e-9),
                               ('number of trial modes', 20)
                               ])
          source = self.fdtd.addmode(properties=props)
          source.z_span = 1.14e-6
          source.x = cindex*a + a/2 if not (rindex % 2 == 1) == crystal.first_null else (cindex)*a
          source.y = rindex*h
          source.y_span = 2*a
          
    pc.script = script
    
    self.height = (len(matrix)-1)*h
    self.width  = (len(matrix[0])-1)*a + a/2
    
    self.fdtd.select('base')
    self.fdtd.delete()
  
    rect = self.fdtd.addrect()
    rect.name = 'base'
    rect.x = self.width/2
    rect.x_span = self.width + 2*self.x_margin
    rect.y = self.height/2
    rect.y_span = self.height + 2*self.y_margin
    rect.material = 'algaas_lpedraza'
    rect.z_span = 0.36E-6 
    
    self.structures['base'] = {
      'f': rect
    }
        
  def add_fdtd(self, x=-1, y=-1):
    self.fdtd.select('FDTD')
    self.fdtd.delete()
    
    x = self.width if x == -1 else x
    y = self.height if y == -1 else y
    
    self.fdtd.addfdtd(dimension="2D", x = x/2, y = y/2, 
                      x_span = x + 2*self.x_margin, 
                      y_span = y + 2*self.y_margin)
    
  def add_movie(self, x=-1, y=-1):
    self.fdtd.select('movie')
    self.fdtd.delete()
    
    x = self.width if x == -1 else x
    y = self.height if y == -1 else y
    
    self.fdtd.addmovie(name = "movie", x = x/2, y = y/2, 
                      x_span = x + 2*self.x_margin, 
                      y_span = y + 2*self.y_margin)