# -*- coding: utf-8 -*-

# Copyright 2024 Technology Innovation Institute (https://www.tii.ae)
# Author: Charles Vanwynsberghe
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
from pyqtgraph.Qt import QtCore

from plotting import PlotterArray3D, scale_to_01
from phased_array import azel_to_thetaphi

# define the parameters and geometry
wavelength = 0.25
range_db = 30  # for plotting in dB

# create plotting and array handler
x, y = np.mgrid[-0.5:0.5:9j, -0.5:0.5:9j]
pos_usa = np.vstack((x.ravel(), y.ravel(), np.zeros((x.size,)))).T
arrplot = PlotterArray3D(wavelength)
arrplot.create_geom(pos_usa)
arrplot.create_sphere_mesh_uv(180, 360)

# create and collect beam scanning data
beamscan = {"bp": [], "verts": [], "src": []}
el_scan = np.linspace(-np.pi / 4, np.pi / 4, 5)
az_scan = np.linspace(-np.pi / 4, np.pi / 4, 5)
for i, el_ in enumerate(el_scan):
    print(f"\rpre-compute beams: {i}/{el_scan.size}", end='', flush=True)
    for az_ in az_scan:
        angs_ = azel_to_thetaphi(az_, el_)
        bp_ = arrplot.directivity_pattern_tx(wavelength, angs_[0], angs_[1])
        bp_01_ = 20 * np.log10(np.abs(bp_ / arrplot.n_sensor))
        bp_01_ = scale_to_01(bp_01_, -range_db, 0)

        beamscan["bp"].append(bp_01_)
        beamscan["verts"].append(arrplot.verts * bp_01_[:, np.newaxis])
        beamscan["src"].append(arrplot.src)

beamscan["bp"] = np.array(beamscan["bp"])
beamscan["verts"] = np.array(beamscan["verts"])
beamscan["src"] = np.array(beamscan["src"])

# plotting - initialize
arrplot.add_plot_geometry(size=0.1)
arrplot.add_plot_beampattern(beamscan["bp"][0], -range_db, 0, "dB")

# plotting - animate
index = 0
def update():
    global index, timer, arrplot
    print(f"\r{index}", end='', flush=True)
    # change the beam
    bp_ = beamscan["bp"][index % beamscan["bp"].shape[0]]
    src_ = beamscan["src"][index % beamscan["bp"].shape[0]]
    verts_ = beamscan["verts"][index % beamscan["bp"].shape[0], ...]

    # update plots
    arrplot.update_plot_geometry(src_)
    arrplot.update_plot_beampattern(bp_, verts=verts_)

    if index == 250:
        timer.stop()
    else:
        index += 1

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(200)

arrplot.exec()