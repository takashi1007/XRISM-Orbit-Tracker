#! /usr/bin/env python

import os
import sys
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QVBoxLayout, QSlider, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
import matplotlib.image as mpimg
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
import random
import ephem
import cartopy.crs as ccrs
import datetime as dt
from cartopy.feature.nightshade import Nightshade
import math
import numpy as np
import pandas as pd


# TLE info from NORAD website
name = 'XRISM'
line1 = '1 57800U 23137A   25057.59890194  .00013364  00000-0  87798-3 0  9999'
line2 = '2 57800  31.0020 186.8700 0008114 219.6131 140.3913 15.06408680 80934'
xrism = ephem.readtle(name, line1, line2)

# SAA definition file
saa_file = 'saa_sxs.conf.20160324a'

sc_image = 'XRISM_spacecraft.png'

sliderMin = -7200 # in min, 7200 min = 5 days
sliderMax = 14400 # in min, 14400 min = 10 days

# main window
# which inherits QDialog
class Window(QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        # create a canvas for a world map
        self.figure = plt.figure(tight_layout=True)
        self.canvas = FigureCanvas(self.figure)

        # create buttons and a slider
        self.buttonS = QPushButton(self)
        self.buttonS.setText('Stop update')
        self.buttonS.setCheckable(True)
        self.buttonS.clicked.connect(self.autoUpdate)
        self.buttonQ = QPushButton('Close')
        self.buttonQ.clicked.connect(self.closeApp)
        self.slidebar = QSlider(Qt.Orientation.Horizontal, self)
        self.slidebar.setRange(sliderMin, sliderMax)
        self.slidebar.valueChanged.connect(self.sliderAction)

        # place the buttons and slider
        hboxOperate = QHBoxLayout()
        hboxOperate.addWidget(self.buttonS)
        hboxOperate.addWidget(self.slidebar)
        hboxOperate.addWidget(self.buttonQ)

        # creating a Vertical Box layout
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.canvas)
        mainLayout.addLayout(hboxOperate)

        # setting layout to the main window
        self.setLayout(mainLayout)

        # draw the first orbit track
        self.update()

        # enable auto update at the start up
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10000)
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def autoUpdate(self):
        if self.buttonS.isChecked():
            self.buttonS.setText('Auto update')
            self.timer.stop()
        else:
            self.buttonS.setText('Stop update')
            self.update()
            self.timer.start()

    def sliderAction(self, value):
        if not self.buttonS.isChecked():
            self.buttonS.toggle()
            self.timer.stop()
            self.buttonS.setText('Auto update')
            self.update(value)

        self.update(value)
        
    def insertEvent(self, eventList, xrismTrack):
        for ii in range(len(eventList)):
            event = eventList[ii].strip()
            eventTmp = event.split(' ')
            eventName = eventTmp[6:]
            eventTime = dt.datetime(int(eventTmp[0]), int(eventTmp[1]), int(eventTmp[2]), int(eventTmp[3]), int(eventTmp[4]))

            trackTime_start_dt = ephem.Date(int(xrismTrack[0][0]/ephem.minute)*ephem.minute).datetime()
            trackTime_end_dt = ephem.Date(int(xrismTrack[0][-1]/ephem.minute)*ephem.minute).datetime()
            if (eventTime > trackTime_start_dt) and (eventTime < trackTime_end_dt):
                for jj in range(len(xrismTrack[0])):
                    trackTime_dt = ephem.Date(int(xrismTrack[0][jj]/ephem.minute)*ephem.minute).datetime()
                    if eventTime == trackTime_dt:
                        plt.plot(xrismTrack[1][jj], xrismTrack[2][jj], color='b', marker='o', markersize=5, transform=ccrs.PlateCarree())
                        if xrismTrack[1][jj] < 0:
                            plt.text(xrismTrack[1][jj]+1, xrismTrack[2][jj]+2, ' '.join(eventName), color='b', size=20, ha='left', transform=ccrs.PlateCarree())
                        if xrismTrack[1][jj] > 0:
                            plt.text(xrismTrack[1][jj]+1, xrismTrack[2][jj]+2, ' '.join(eventName), color='b', size=20, ha='right', transform=ccrs.PlateCarree())
                        break
        if eventTime < trackTime_end_dt:
            plt.text(0, 0, 'You need a new event list file', fontsize=30, color='r', ha='center')
         
    def drawSAA(self):
        # SAA line
        plt.plot(saa_lon, saa_lat, color='k',  transform=ccrs.PlateCarree())
        plt.text(-25, -39, 'SAA', color='k', size=20)

            
    def update(self, value=0):
        self.figure.clear()
        ax = self.figure.add_subplot(1,1,1, projection=ccrs.PlateCarree())
        start_time = ephem.now() + ephem.minute*value
        updateTime = (dt.datetime.now(dt.UTC)+dt.timedelta(minutes=value)).strftime('%Y/%m/%d %H:%M')
        ax.coastlines()
        ax.set_title(f'XRISM Resolve events/orbit {updateTime} (UT)', fontsize=25)
        ax.set_global()
        ax.add_feature(Nightshade(dt.datetime.now(dt.UTC), alpha=0.2))

	# add USC at 31.2513N, 131.0761E from Google
        ax.plot(131.0761, 31.2513, color='g', mew=2, marker='+', markersize=15, transform=ccrs.PlateCarree())
        ax.text(132.0761, 25.2513, 'USC', color='g', size=20, transform=ccrs.PlateCarree())
	# add SNT at 33.1333S, 70.6667
        ax.plot(-70.6667, -33.1333, color='royalblue', mew=2, marker='+', markersize=15, transform=ccrs.PlateCarree())
        ax.text(-80.6667, -38.1333, 'SNT', color='royalblue', size=20, transform=ccrs.PlateCarree())
	# add HBK at 25.8870S, 27.7120E
        ax.plot(27.7120, -25.8870, color='palegreen', mew=2, marker='+', markersize=15, transform=ccrs.PlateCarree())
        ax.text(28.7120, -30.8870, 'HBK', color='palegreen', size=20, transform=ccrs.PlateCarree())
	# add MSP at 27.7633N, 15.6342W
        ax.plot(-15.6342, 27.7633, color='orange', mew=2, marker='+', markersize=15, transform=ccrs.PlateCarree())
        ax.text(-20.6342, 32.7633, 'MSP', color='orange', size=20, transform=ccrs.PlateCarree())
	# add AUWA at 29.0457S, 115.3487E
        ax.plot(115.3487, -29.0457, color='gold', mew=2, marker='+', markersize=15, transform=ccrs.PlateCarree())
        ax.text(100.3487, -34.0457, 'AUWA', color='gold', size=20, transform=ccrs.PlateCarree())
	# add USHI at 19.0140N, 155.6633W
        ax.plot(155.6633, 19.0140, color='skyblue', mew=2, marker='+', markersize=15, transform=ccrs.PlateCarree())
        ax.text(156.6633, 14.0140, 'USHI', color='skyblue', size=20, transform=ccrs.PlateCarree())


        position_time = []
        position_lon = []
        position_lat = []

        for ii in range(100): # orbit track for 100 min in future
            newTime = start_time + ephem.minute*ii
            xrism.compute(newTime)
            position_time.append(newTime)
            position_lon.append(xrism.sublong*180.0/math.pi)
            position_lat.append(xrism.sublat*180.0/math.pi)

        xrism_track = [position_time, position_lon, position_lat]

        plt.plot(position_lon, position_lat, color='blue', transform=ccrs.Geodetic())        
        if showSC:
            scBox = OffsetImage(sc, zoom=0.5)
            scBox.image.axes = ax
            ab = AnnotationBbox(scBox, [position_lon[0], position_lat[0]], pad=0, frameon=False)
            ax.add_artist(ab)
        else:
            plt.plot(position_lon[0], position_lat[0], color='blue', mew=2, marker='+', markersize=15, transform=ccrs.PlateCarree())
            ax.text(position_lon[0]+1, position_lat[0]-5, 'XRISM', color='b', size=20, transform=ccrs.PlateCarree())

        elevation = []
        for ii in range(60):
            for jj in range(60):
                obs = ephem.Observer()
                obs.lon = str(position_lon[0] + (ii-30))
                obs.lat = str(position_lat[0] + (jj-30))
                obs.date = start_time
                obs.elevation = 0
        
                xrism.compute(obs)
                elevation.append(xrism.alt*180.0/math.pi)

        altitude = np.array(elevation)
        x = np.linspace(position_lon[0]-30, position_lon[0]+30, 60)
        y = np.linspace(position_lat[0]-30, position_lat[0]+30, 60)
        X, Y = np.meshgrid(x, y)
        Z = altitude.reshape(60,60)
        levels = [0.0, 90.0]
        #ax.contour(X, Y, Z.T, levels, colors='b', transform=ccrs.PlateCarree(), transform_first=True)
        ax.contourf(X, Y, Z.T, levels, colors='b', alpha=0.2, transform=ccrs.PlateCarree(), transform_first=True)

        if showEvents:
            self.insertEvent(eventList, xrism_track)

        if showSAA:
            self.drawSAA()
        
        self.canvas.draw()

    def closeApp(self):
        self.close()

showEvents = True
if len(sys.argv) == 1:
    showEvents = False
elif len(sys.argv) == 2:
    eventList = []
    eventFilename = sys.argv[1]
    with open(eventFilename, 'r') as f:
        eventList = f.readlines()
    f.close()

showSAA = True
if os.path.isfile(saa_file):
    df = pd.read_csv(saa_file, header=3, names=["alt", "lon", "lat"])
    saa_lon, saa_lat = df["lon"].to_numpy(), df["lat"].to_numpy()
else:
    showSAA = False

showSC = True
if os.path.isfile(sc_image):
    sc = mpimg.imread(sc_image)
else:
    showSC = False
    
app = QApplication(sys.argv)
main = Window()
main.show()
sys.exit(app.exec_())
