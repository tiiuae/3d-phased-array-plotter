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
from pyqtgraph.opengl import MeshData

def azel_to_thetaphi(az, el):
    """
    Convert (azimuth, elevation) to  spherical coordinate angles (θ, φ).

    Parameters
    ----------
    az : float or numpy.array
        Azimuth angle [rad].
    el : float or numpy.array
        Elevation angle [rad].

    Returns
    -------
    [theta, phi] : list
        Array of (theta, phi) angles [rad].

    """
    cos_theta = np.cos(el) * np.cos(az)
    theta = np.arccos(cos_theta)
    phi = np.arctan2(np.tan(el), np.sin(az))

    return theta, phi


def thetaphi_to_dir(angs):
    """
    Convert N spherical coordinate system angles (θ, φ) to unit vector.

    Parameters
    ----------
    angs : numpy.array
        (N, 2) array of (θ, φ) coordinates.

    Returns
    -------
    e : numpy.array
        (N, 3) array of (x, y, z) coordinates.
    """
    e = np.zeros((angs.shape[0], 3))
    e[:, 0] = np.cos(angs[:, 1]) * np.sin(angs[:, 0])
    e[:, 1] = np.sin(angs[:, 1]) * np.sin(angs[:, 0])
    e[:, 2] = np.cos(angs[:, 0])

    return e

class PhasedArray3D:
    def __init__(self):
        self.pos_sensor = None
        self.wavelength = None

    def create_geom(self, pos):
        """
        Generic function to define transducer positions and orientations.
        Assumes omnidirectional transducers.

        """
        self.pos_sensor = np.array(pos)
        assert self.pos_sensor.shape[1] == 3, "pos shape should be (N, 3)"
        self.n_sensor = pos.shape[0]

    def create_sphere_mesh_uv(self, nb_theta, nb_phi):
        self.nb_theta = nb_theta
        self.nb_phi = nb_phi        

        # create a sphere mesh from existing pyqtgraph helper
        sphere_uv = MeshData().sphere(nb_theta, nb_phi, radius=1)
        self.verts = sphere_uv._vertexes
        self.faces = sphere_uv._faces
        self.dir_grid = self.verts

    def directivity_pattern_tx(self, wavelength, theta_ref, phi_ref):
        """
        Generate tx far field directivity pattern when array beams towards
        (theta_ref, phi_ref).

        """
        self.dir_ref = thetaphi_to_dir(np.array((theta_ref, phi_ref))[None, :])
        self.dir_ref = self.dir_ref.ravel()
        if self.wavelength != wavelength:
            self.steer_vecs = np.exp(-2j*np.pi/wavelength *
                                     self.pos_sensor @ self.dir_grid.T)
            self.wavelength = wavelength

        self.src = np.exp(-2j*np.pi/wavelength * self.pos_sensor @ self.dir_ref) 
        self.pattern_tx = self.steer_vecs.T.conj() @ self.src

        return self.pattern_tx
