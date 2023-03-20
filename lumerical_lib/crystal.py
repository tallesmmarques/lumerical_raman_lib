import numpy as np
import os
import shutil

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


class Crystal(object):
    def __init__(self, name, a=0.426E-6, zspan=0.40E-6):
        self.name = name
        self.x = 0
        self.y = 0
        self.model = ""
        self.first_null = False
        self.a = a
        self.zspan = zspan
        self.x_init = 0

        if os.path.exists(f'{self.name}_crystal_model.txt'):
            self.read_crystal_file()
            print(
                f'[log] Modelo atualizado com base no arquivo {self.name}_crystal_model.txt')
        else:
            self.generate_crystal_file()
            print(
                f'[log] Projete o cristal no arquivo {self.name}_crystal_model.txt e execulte read_crystal_file()')

    def __str__(self):
        return self.model

    def __iter__(self):
        self.iter_aux = 0
        return self

    def __next__(self):
        if self.iter_aux < self.y:
            line = self.model.splitlines()[self.iter_aux].split()
            self.iter_aux = self.iter_aux + 1
            return line
        else:
            raise StopIteration

    def generate_crystal_file(self, x=5, y=5):
        self.model = ""
        for row in range(y):
            tmp_row = row + 1 if not ((y % 2 == 1) == self.first_null) else row
            for col in range(x):
                self.model += " 0" if tmp_row % 2 == 0 else "0 "
            self.model += "\n"

        if os.path.exists(f'{self.name}_crystal_model.txt'):
            i = 1
            try:
                os.mkdir("backups")
            except:
                pass

            while os.path.exists(f'backups\\{self.name}_crystal_model_bkp{i}.txt'):
                i += 1

            shutil.copyfile(f'{self.name}_crystal_model.txt',
                            f'backups\\{self.name}_crystal_model_bkp{i}.txt')
            print("[log] Arquivo antigo salvo em backup")

        with open(f'{self.name}_crystal_model.txt', 'w') as file:
            file.write(self.model)

    def read_crystal_file(self):
        self.model = ''
        tmp_model = ''
        with open(f'{self.name}_crystal_model.txt') as file:
            tmp_model = file.read()

        tmp_model += '\n'
        for line in tmp_model.splitlines(keepends=True):
            if line.isspace():
                continue
            self.model += line

        self.set_size()
        if self.model.splitlines()[-1][0] == ' ':
            self.first_null = True

    def expand_x(self, n=1):
        tmp_model = self.model
        self.model = ''
        for line in tmp_model.splitlines():
            for __n in range(n):
                line += line[-2:]
            line += '\n'
            self.model += line
        self.set_size()

    def reduce_x(self, n=1):
        tmp_model = self.model
        self.model = ''
        for line in tmp_model.splitlines():
            for __n in range(n):
                line = line[:-2]
            line += '\n'
            self.model += line
        self.set_size()

    def generate_script(self):
        script = 'deleteall; \n\n'
        a = self.a
        zspan = self.zspan
        h = a*np.sqrt(3)/2

        matrix = self.generate_matrix()

        for rindex, row in enumerate(matrix):
            for cindex, simbol in enumerate(row):
                if simbol not in types.keys():
                    continue
                type = types[simbol]

                if type['type'] == 'none':
                    continue
                elif type['type'] == 'circle':
                    script += 'addcircle; \n'

                    script += 'set("radius", {}); \n'.format(a *
                                                             type['radius'])
                    if not (rindex % 2 == 1) == self.first_null:  # odd
                        script += 'set("x", {}); \n'.format(cindex*a + a/2)
                    else:  # even
                        script += 'set("x", {}); \n'.format(cindex*a)
                    script += 'set("y", {}); \n'.format(rindex*h)

                    script += 'set("z", {}); \n'.format(0)
                    script += 'set("z span", {}); \n'.format(zspan)
                    script += 'set("material", "{}"); \n'.format('etch')
                    script += '\n'
                elif type['type'] == 'curve':
                    script += 'addpoly; \n'
                    r = a * type['radius']
                    vtx = [
                        (0, r),
                        (a, r),
                        (2.5*a + np.cos(np.deg2rad(120)) * r,
                            h + np.sin(np.deg2rad(120))*r),
                        (3*a + np.cos(np.deg2rad(150))*r,
                            2*h + np.sin(np.deg2rad(150))*r),
                        (3*a + np.cos(np.deg2rad(-30))*r,
                            2*h + np.sin(np.deg2rad(-30))*r),
                        (2.5*a + np.cos(np.deg2rad(-30))*r,
                            h + np.sin(np.deg2rad(-30))*r),
                        (2.5*a + np.cos(np.deg2rad(-60))*r,
                            h + np.sin(np.deg2rad(-60))*r),
                        (a + np.cos(np.deg2rad(-60))*r,
                            np.sin(np.deg2rad(-60))*r),
                        (a, -r),
                        (0, -r)
                    ]

                    circle_script = 'addcircle; \n\n'
                    circle_type = types['2']
                    circle_script += 'set("radius", {}); \n'.format(a *
                                                                    circle_type['radius'])
                    circle_script += 'set("z", {}); \n'.format(0)
                    circle_script += 'set("z span", {}); \n'.format(zspan)
                    circle_script += 'set("material", "{}"); \n'.format('etch')

                    x_desv = np.cos(np.deg2rad(-60))*a*1/3
                    y_desv = np.sin(np.deg2rad(-60))*a*1/3

                    ri = rindex
                    ci = cindex

                    # print(ri, ci)
                    # print(matrix[ri-1:ri+2], '\n')

                    if matrix[ri+1][ci-1] == '.' and matrix[ri+1][ci-0] == '.':
                        # print("curva de 60° para 0° com ponto interno a curva")
                        vtx = [(-x[0] + 1.5*a, -x[1] + h) for x in vtx]
                    elif matrix[ri+1][ci-0] == '.' and matrix[ri+1][ci+1] == '.':
                        # print("curva de -60° para 0° com ponto externo a curva")
                        vtx = [(-x[0] + 2*a, x[1]) for x in vtx]
                        x_desv *= -1
                    elif matrix[ri-1][ci-1] == '.' and matrix[ri-1][ci-0] == '.':
                        # print("curva de -60° para 0° com ponto interno a curva")
                        vtx = [(-x[0] + 1.5*a, x[1] - h) for x in vtx]
                        y_desv *= -1
                    elif matrix[ri-1][ci-0] == '.' and matrix[ri-1][ci+1] == '.':
                        # print("curva de 60° para 0° com ponto externo a curva")
                        vtx = [(-x[0] + 2*a, -x[1]) for x in vtx]
                        x_desv *= -1
                        y_desv *= -1
                    elif matrix[ri+1][ci-1] == '.':
                        # print("curva para 60° com ponto externo a curva")
                        vtx = [(x[0] - 2*a, x[1]) for x in vtx]
                    elif matrix[ri+1][ci+1] == '.':
                        # print("curva para -60° com ponto interno a curva")
                        vtx = [(x[0] - 1.5*a, -x[1] + h) for x in vtx]
                        x_desv *= -1
                    elif matrix[ri-1][ci-1] == '.':
                        # print("curva para -60° com ponto externo a curva")
                        vtx = [(x[0] - 2*a, -x[1]) for x in vtx]
                        y_desv *= -1
                    elif matrix[ri-1][ci+1] == '.':
                        # print("curva para 60° com ponto interno a curva")
                        vtx = [(x[0] - 1.5*a, x[1] - h) for x in vtx]
                        x_desv *= -1
                        y_desv *= -1

                    if not (ri % 2 == 1) == self.first_null:  # odd
                        circle_script += 'set("x", {}); \n'.format(cindex *
                                                                   a + a/2 + x_desv)
                    else:  # even
                        circle_script += 'set("x", {}); \n'.format(cindex *
                                                                   a + x_desv)
                    circle_script += 'set("y", {}); \n'.format(rindex*h + y_desv)

                    vertices = '['
                    for i, point in enumerate(vtx):
                        if i != 0:
                            vertices += ';'
                        vertices += f'{point[0]},{point[1]}'
                    vertices += ']'

                    if not (rindex % 2 == 1) == self.first_null:  # odd
                        script += 'set("x", {}); \n'.format(cindex*a + a/2)
                    else:  # even
                        script += 'set("x", {}); \n'.format(cindex*a)
                    script += 'set("y", {}); \n'.format(rindex*h)

                    script += 'set("vertices", {});'.format(vertices)
                    script += 'set("z span", {}); \n'.format(zspan)
                    script += 'set("material", "{}"); \n'.format('etch')

                    script += circle_script
                    script += '\n'
                else:
                    continue
        return script

    def generate_matrix(self):
        matrix = []
        for line in self:
            matrix.append(line)
        matrix = np.flip(np.array(matrix), 0)
        return matrix

    def set_size(self):
        self.x = len(max(self.model.replace(' ', '').splitlines(), key=len))
        self.y = len(self.model.splitlines())

    def set_model(self, model):
        self.model = model

    def get_model(self):
        return self.model

    def print_crystal(self):
        print(self.model)
