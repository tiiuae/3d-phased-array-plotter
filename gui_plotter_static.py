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

from plotting import scale_to_01, PlotterArray3D

# define the parameters and geometry
wavelength = 0.5
ang_ref = [np.pi/4, -np.pi/4]  # spherical coordinates [rad, rad]
range_db = 30  # for plotting in dB

# create plotting and array handler
x_usa, y_usa = np.mgrid[-0.5:0.5:9j, -0.5:0.5:9j]
pos_usa = np.vstack((x_usa.ravel(), y_usa.ravel(),
                     np.zeros((x_usa.size,)))).T
arrplt = PlotterArray3D(wavelength)
arrplt.create_geom(pos_usa)
arrplt.create_sphere_mesh_uv(180, 360)

# create and collect beam
dp = arrplt.directivity_pattern_tx(0.5, ang_ref[0], ang_ref[1])
dp = 20*np.log10(np.abs(dp) / arrplt.n_sensor)
dp_sc = scale_to_01(dp, -range_db, 0)  # ensure [0, 1] for rendering

# plotting 
arrplt.add_plot_geometry(size=0.1)
arrplt.add_plot_beampattern(dp_sc, -range_db, 0, "dB")
arrplt.exec()
