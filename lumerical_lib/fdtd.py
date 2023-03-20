import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from scipy import interpolate, constants
from collections import OrderedDict

import importlib.util
import os
import shutil

from lumerical_lib import crystal

os.add_dll_directory('C:\\Program Files\\Lumerical\\v202\\api\\python')
spec_win = importlib.util.spec_from_file_location(
    'lumapi', 'C:\\Program Files\\Lumerical\\v202\\api\\python\\lumapi.py')
spec_lin = importlib.util.spec_from_file_location(
    'lumapi', "/opt/lumerical/2020a/api/python/lumapi.py")
spec_mac = importlib.util.spec_from_file_location(
    'luampi', "/Applications/Lumerical/FDTD Solutions/FDTD Solutions.app/Contents/API/Python/lumapi.py")

lumapi = importlib.util.module_from_spec(spec_win)
spec_win.loader.exec_module(lumapi)

types = {
    '0': {'type': 'circle', 'radius': 0.30},
    '1': {'type': 'circle', 'radius': 0.38},
    '2': {'type': 'circle', 'radius': 0.20},
    '3': {'type': 'circle', 'radius': 0.16},
    '4': {'type': 'circle', 'radius': 0.40},
    '5': {'type': 'circle', 'radius': 0.25},
    '.': {'type': 'none'},
    'c': {'type': 'curve', 'radius': 0.38},
    'j': {'type': 'junction', 'radius': 0.38},
    's': {'type': 'source'},
    'm': {'type': 'monitor'}
}


class Fdtd(object):
    def __init__(self, name="fdtd_file.fsp", new=False):
        if not new:
            self.fdtd = lumapi.FDTD(name)
        else:
            self.fdtd = lumapi.FDTD()

        self.structures = {'crystals': {}, 'sources': {}}
        self.width = 0
        self.height = 0
        self.a = 0.426E-6

        self.x_margin = 0.8E-6
        self.y_margin = 0.8E-6

        self.source_index = 0
        self.last_crystal_x = 0

        self.fdtd.importmaterialdb('..\\lumerical_lib\\material.mdf')

    def add_crystal(self, crystal: crystal.Crystal):
        self.fdtd.select(crystal.name)
        self.fdtd.delete()
        self.a = crystal.a

        pc = self.fdtd.addstructuregroup()
        pc.name = crystal.name

        pc.x = self.last_crystal_x
        pc.y = 0
        pc.z = 0

        self.structures['crystals'][crystal.name] = {
            'f': pc, 'crystal': crystal}
        self.last_crystal_x += crystal.x * crystal.a
        pc.script = crystal.generate_script()

    def add_sources(self, amp=2.07766e+08, f=1541.3e-9, offset=30E-15, pulselength=50E-15):
        crystal = self.structures['crystals'][next(
            iter(self.structures['crystals']))]['crystal']
        a = crystal.a
        zspan = crystal.zspan
        h = a*np.sqrt(3)/2
        self.source_index = 0

        matrix = crystal.generate_matrix()

        for rindex, row in enumerate(matrix):
            for cindex, simbol in enumerate(row):
                if simbol not in types.keys():
                    continue
                type = types[simbol]

                if type['type'] == 'source':
                    self.source_index += 1
                    self.fdtd.select(f'source_{self.source_index}')
                    self.fdtd.delete()

                    c = constants.c

                    props = OrderedDict([("name", f'source_{self.source_index}'),
                                         ("amplitude", amp),
                                         ('injection axis', 'x-axis'),
                                         ('mode selection', 'fundamental TE mode'),
                                         ("override global source settings", True),
                                         # ("wavelength start", 1550e-9),
                                         # ("wavelength stop", 1550e-9),
                                         ('set time domain', True),
                                         ('pulse type', 'standard'),
                                         ('frequency', (c/f)),  # Hz
                                         ('offset', offset),  # fs
                                         ('pulselength', pulselength),  # fs
                                         ('number of trial modes', 20)
                                         ])
                    source = self.fdtd.addmode(properties=props)
                    source.z_span = 1.14e-6
                    source.x = cindex*a + a / \
                        2 if not (rindex %
                                  2 == 1) == crystal.first_null else (cindex)*a
                    source.y = rindex*h
                    source.y_span = 2*a

                    self.structures['sources'][f'source_{self.source_index}'] = {
                        'f': source}

    def add_base(self):
        width, height = self.get_size()

        self.fdtd.select('base')
        self.fdtd.delete()

        rect = self.fdtd.addrect()
        rect.name = 'base'
        rect.x = width/2
        rect.x_span = width + 2*self.x_margin
        rect.y = height/2
        rect.y_span = height + 2*self.y_margin
        rect.material = 'algaas_lpedraza'
        rect.z_span = 0.36E-6

        self.structures['base'] = {
            'f': rect
        }

    def get_size(self):
        crystal = self.structures['crystals'][next(
            iter(self.structures['crystals']))]['crystal']

        h = self.a * np.sqrt(3)/2
        height = crystal.y * h - h
        width = self.last_crystal_x
        return width, height
