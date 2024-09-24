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

from typing import List

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from phased_array import PhasedArray3D

np.product = np.prod # for compatibility between recent numpy and pyqtgraph


def scale_to_01(v, v_min, v_max, clipping=True):
    """Transform array `v` linearly from [v_min, v_max] to [0, 1]."""
    v_out = (v - v_min) / (v_max - v_min)
    if clipping is True:
        v_out = np.clip(v_out, 0, 1)

    return v_out


def msphere_to_mpattern(verts, faces, radius, cmap, interp_color=False):
    """Transform a sphere mesh to a directivity pattern mesh via radius."""
    assert np.all((radius >= 0) & (radius <= 1)), "radius is not in [0, 1]"
    verts_out = verts * radius[:, np.newaxis]  # .astype(np.float32)

    if interp_color is False:
        val_faces = radius[faces[:, 0]]  # take the first vertex of each face
    else:
        raise Exception("not implemented yet")
    colors = cmap.map(val_faces, mode=cmap.FLOAT)

    return gl.MeshData(vertexes=verts_out, faces=faces, faceColors=colors)



class GLViewWidgetLinked(gl.GLViewWidget):
    """GLViewWidget with a linked camera view (rotation only)."""

    def __init__(self, parent=None, devicePixelRatio=None,
                 rotationMethod='euler'):
        self.linked_views: List[gl.GLViewWidget] = []
        super().__init__(parent, devicePixelRatio, rotationMethod)

    def mouseMoveEvent(self, ev):
        """Update camera on move event."""
        super().mouseMoveEvent(ev)
        self._update_camera()

    def _update_camera(self):
        """Take camera parameters and sync with all views."""
        camera_params = self.cameraParams()
        for view in self.linked_views:
            view.setCameraParams(elevation=camera_params["elevation"],
                                 azimuth=camera_params["azimuth"])

    def setCameraLink(self, view: gl.GLViewWidget):
        """Add view to sync camera with."""
        self.linked_views.append(view)

class GLLabelItem(gl.GLGraphicsItem.GLGraphicsItem):
    """Text label in a `GLViewWidget`."""

    def __init__(self, **kwds):
        """
        Text label in a `GLViewWidget`.

        Arguments:
        ---------
            pos: position of the text, in pixels from the top left corner.
            text: text value to display.
            fontColor: sets the text color with :func:`~pyqtgraph.mkColor`

        """
        gl.GLGraphicsItem.GLGraphicsItem.__init__(self)
        glopts = kwds.pop("glOptions", "additive")
        self.setGLOptions(glopts)
        self.pos = (10, 10)
        self.fontColor = QtGui.QColor(QtCore.Qt.GlobalColor.white)
        self.setData(**kwds)

    def setData(self, **kwds):
        args = ["pos", "text", "fontColor"]
        for k in kwds.keys():
            if k not in args:
                raise Exception(
                    "Invalid keyword argument: %s (allowed arguments are %s)"
                    % (k, str(args))
                )

        for key in kwds:
            value = kwds[key]
            if key == 'fontColor':
                value = pg.functions.mkColor(value)
            setattr(self, key, value)

        self.update()

    def paint(self):
        self.setupGLState()
        painter = QtGui.QPainter(self.view())
        painter.setPen(self.fontColor)
        painter.drawText(QtCore.QPointF(*self.pos), self.text)
        painter.end()

class PlotterArray3D(PhasedArray3D):
    def __init__(self, wavelength):
        # TODO Ultimately, wavelength must coincide with wavelength from SensorArray3D
        super().__init__()
        # prepare the layout
        self.w = pg.GraphicsLayoutWidget(show=True, size=(1000, 500),
                                         title="array analysis rendering")
        self.layoutgb = QtWidgets.QGridLayout()
        self.w.setLayout(self.layoutgb)
        self._init_view_geometry(wavelength)
        self._init_view_beampattern()
        self.glvw1.setCameraLink(self.glvw2)
        self.glvw2.setCameraLink(self.glvw1)

    def _init_view_geometry(self, wavelength):
        """Prepare geometry rendering."""
        self.glvw1 = GLViewWidgetLinked()
        self.glvw1.setCameraPosition(distance=3, azimuth=-45)
        # add grid
        self.grid1 = gl.GLGridItem(size=QtGui.QVector3D(50, 50, 1))
        self.grid1.scale(wavelength, wavelength, wavelength / 1000)
        self.glvw1.addItem(self.grid1)
        # add axes
        self.ax1 = gl.GLAxisItem(glOptions="opaque")
        self.ax1.setSize(wavelength, wavelength, wavelength)
        self.ax1.translate(0, 0, wavelength/1e3)
        self.glvw1.addItem(self.ax1)
        # add title label
        self.label1 = GLLabelItem(pos=(50, 10), text="TRANSDUCER ARRAY",
                                  fontColor="grey")
        self.glvw1.addItem(self.label1)
        # add view to main window
        self.layoutgb.addWidget(self.glvw1, 0, 0)

    def _init_view_beampattern(self):
        """Prepare beampattern rendering."""
        self.glvw2 = GLViewWidgetLinked()
        self.glvw2.setCameraPosition(distance=3, azimuth=-45)
        self.grid2 = gl.GLGridItem(size=QtGui.QVector3D(2, 2, 1))
        # add grid
        self.grid2.scale(1, 1, 1)
        self.glvw2.addItem(self.grid2)
        # add title label
        label2 = GLLabelItem(pos=(50, 10), text="BEAM PATTERN",
                             fontColor="grey")
        self.glvw2.addItem(label2)
        # add view to main window
        self.layoutgb.addWidget(self.glvw2, 0, 2)

    def add_plot_geometry(self, size=0.1):
        """Plot geometry. Use this function at the first time."""
        self.cmap_phases = pg.colormap.get("CET-CBTC1")
        cbar1_legend = dict(zip(["0", "π", "2π"], [0, 0.5, 1]))
        self.cbar1 = gl.GLGradientLegendItem(pos=(10, 10), size=(10, 200),
                                             gradient=self.cmap_phases,
                                             labels=cbar1_legend)
        self.glvw1.addItem(self.cbar1)

        colors = self.cmap_phases.map(np.angle(self.src) / (2 * np.pi) + 0.5,
                                      mode=self.cmap_phases.FLOAT)
        self.scat_arr = gl.GLScatterPlotItem(pos=self.pos_sensor,
                                             size=size,
                                             color=colors,
                                             pxMode=False)

        self.glvw1.addItem(self.scat_arr)

    def update_plot_geometry(self, src):
        """Update geometry. Use after calling `self.add_plot_geometry`."""
        colors = self.cmap_phases.map(np.angle(src) / (2 * np.pi) + 0.5,
                                      mode=self.cmap_phases.FLOAT)
        self.scat_arr.setData(color=colors)

    def add_plot_beampattern(self, dp_01, cb_min, cb_max, cb_unit=""):
        """Plot beampattern. Use this function at the first time."""
        self.cmap_bp = pg.colormap.get('CET-R4')
        cbar2_legend = dict(zip([f"{cb_min} {cb_unit}", f"{cb_max} {cb_unit}"],
                                [0, 1]))
        self.cbar2 = gl.GLGradientLegendItem(pos=(10, 10), size=(10, 200),
                                             gradient=self.cmap_bp,
                                             labels=cbar2_legend)
        self.glvw2.addItem(self.cbar2)

        self.md = msphere_to_mpattern(self.verts, self.faces, dp_01, self.cmap_bp)
        self.m = gl.GLMeshItem(meshdata=self.md, smooth=False, shader=None,
                               glOptions="opaque", drawEdges=False,
                               computeNormals=False)
        self.glvw2.addItem(self.m)

    def update_plot_beampattern(self, bp_01, verts=None):
        """Update beampattern. Use after calling `self.add_plot_beampattern`."""
        colors = self.cmap_bp.map(bp_01[self.faces[:, 0]],
                                  mode=self.cmap_bp.FLOAT)
        if verts is None:
            verts = self.verts * bp_01[:, np.newaxis]
        self.m.setMeshData(vertexes=verts, faces=self.faces,
                           faceColors=colors)

    def exec(self):
        """Run main loop & diplay the window."""
        pg.exec()
