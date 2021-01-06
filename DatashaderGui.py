import sys
import os
import io
import ctypes
import pyarrow
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

import datashader as ds
from functools import partial
from datashader.utils import export_image
from datashader.colors import colormap_select, Greys9
from datashader.utils import lnglat_to_meters as webm
import datashader.transfer_functions as tf
import pandas as pd
import folium
from folium.plugins import Draw

class openImage(QWidget):
    def __init__(self):
        super().__init__()
        window = QVBoxLayout()
        path = os.path.dirname(__file__)
        imagePath = path +"/export/Export.png"
        self.ImageLabel = QLabel(self)
        self.pixmap = QPixmap(imagePath)
        self.ImageLabel.setPixmap(self.pixmap)
        self.resize(self.pixmap.width(),self.pixmap.height())
        self.setWindowTitle(imagePath)
        self.setStyleSheet("background-color: #141414")
        window.addWidget(self.ImageLabel)
        self.setLayout(window)
        self.show()

class datashaderGUI(QWidget):
    def __init__(self, parent = None):
        super().__init__()
        path = os.path.dirname(__file__)
        self.img = None
        self.setWindowIcon(QIcon(path + '\images\Icon.png')) 
        self.setWindowTitle('Datashader GUI')
        self.setStyleSheet("background-color: #141414")
        self.setGeometry(300,50,600,800)
        self.createUI()
        self.show()

    def createUI(self):
        fontSize = 12
        font = 'Arial'
        leftPanelX = 50
        self.getDropdowns()
        self.createTable()

        self.fileLabel = QLabel(self)
        self.fileLabel.setText("Select a parquet file to create your visualization")
        self.fileLabel.move(leftPanelX,25)
        self.fileLabel.setFont(QFont(font, fontSize))
        self.fileLabel.setStyleSheet("color: white")

        self.filePath = QLineEdit(self)
        self.filePath.move(leftPanelX, 50)
        self.filePath.resize(450, 30)
        self.filePath.setStyleSheet("background-color: white; color: black")

        self.browse = QPushButton(self)
        self.browse.setText("Browse")
        self.browse.move(520, 50)
        self.browse.resize(50,30)
        self.browse.setStyleSheet("QPushButton{background-color: #141414; color: white; border: 1px solid white; font-weight: 600}""QPushButton::hover""{""background-color: #e200e2; color: black""}")

        self.browse.clicked.connect(self.browseFile)

        self.bboxLabel = QLabel(self)
        self.bboxLabel.setText("Click on the 'Get Bounding Box' Button to get coordinates")
        self.bboxLabel.move(leftPanelX,200)
        self.bboxLabel.setFont(QFont(font, fontSize))
        self.bboxLabel.setStyleSheet("color: white")

        self.bboxButton = QPushButton(self)
        self.bboxButton.setText("Get Bounding Box")
        self.bboxButton.move(leftPanelX, 230)
        self.bboxButton.resize(450,30)
        self.bboxButton.setFont(QFont(font, fontSize))
        self.bboxButton.setStyleSheet("QPushButton{background-color: #141414; color: white; border: 1px solid white; font-weight: 600}""QPushButton::hover""{""background-color: #e200e2; color: black""}")

        self.bgroundText = QLabel(self)
        self.bgroundText.setText("Select background color for output:")
        self.bgroundText.move(leftPanelX,280)
        self.bgroundText.setFont(QFont(font,fontSize))
        self.bgroundText.setStyleSheet("color: white")

        self.backgroundPick = QComboBox(self)
        self.backgroundPick.move(320,280)
        self.backgroundPick.resize(100, 20)
        self.backgroundPick.addItems(['white','black'])
        self.backgroundPick.setStyleSheet("background-color: white; color: black")

        self.xPlotLabel = QLabel(self)
        self.xPlotLabel.setText("Image Width (Pixels):")
        self.xPlotLabel.move(leftPanelX,320)
        self.xPlotLabel.setFont(QFont(font,fontSize))
        self.xPlotLabel.setStyleSheet("color: white")

        self.xPlotEdit = QLineEdit(self)
        self.xPlotEdit.move(200, 320)
        self.xPlotEdit.resize(75,20)
        self.xPlotEdit.setStyleSheet("background-color: white; color: black")

        self.yPlotLabel = QLabel(self)
        self.yPlotLabel.setText("Image Height (Pixels):")
        self.yPlotLabel.move(300,320)
        self.yPlotLabel.setFont(QFont(font,fontSize))
        self.yPlotLabel.setStyleSheet("color: white")

        self.yPlotEdit = QLineEdit(self)
        self.yPlotEdit.move(460, 320)
        self.yPlotEdit.resize(75,20)
        self.yPlotEdit.setStyleSheet("background-color: white; color: black")

        self.aggPickText = QLabel(self)
        self.aggPickText.setText("Select visual style for output:")
        self.aggPickText.move(leftPanelX,600)
        self.aggPickText.setFont(QFont(font,fontSize))
        self.aggPickText.setStyleSheet("color: white")

        self.aggPick = QComboBox(self)
        self.aggPick.move(320,600)
        self.aggPick.resize(100, 20)
        self.aggPick.addItems(['linear','log','eq_hist'])
        self.aggPick.setStyleSheet("background-color: white; color: black")

        self.bboxButton.clicked.connect(self.openMapWindow)

        self.exportButton = QPushButton(self)
        self.exportButton.setText("Export Image!")
        self.exportButton.move(leftPanelX, 640)
        self.exportButton.resize(450,30)
        self.exportButton.setFont(QFont(font, fontSize))
        self.exportButton.setStyleSheet("QPushButton{background-color: #141414; color: white; border: 1px solid white; font-weight: 600}""QPushButton::hover""{""background-color: #e200e2; color: black""}")
        self.exportButton.clicked.connect(self.exportData)

    def browseFile(self):
        self.fileName = QFileDialog.getOpenFileName(parent=self, caption='Find csv File...')
        if self.fileName:
            self.filePath.setText(self.fileName[0])
        self.parq = pd.read_parquet(self.fileName[0], engine='pyarrow')
        self.xPick.clear()
        self.yPick.clear()
        self.cPick.clear()
        for d in self.parq.columns:
            self.xPick.addItem(d)
            self.yPick.addItem(d)
            self.cPick.addItem(d)
        self.cPick.activated.connect(lambda: self.getCatColumn())
        
    def openMapWindow(self, checked):
        m = folium.Map(
            location = [41.850033, -87.6500523], zoom_start = 4, max_zoom = 12
        )
        directionsHTML = '''<h4 align = center> Use the Draw tool to create a rectangle polygon. After creating the rectangle polygon, click the "Export" button <b>twice</b>.</h4>'''
        draw = Draw(export = True, filename = 'boundingbox.geojson',position='topleft',
        draw_options={'polyline': False, 'polygon': False, 'circle': False, 'marker': False, 'circlemarker': False})
        draw.add_to(m)
        m.get_root().html.add_child(folium.Element(directionsHTML))
        mapData = io.BytesIO()
        m.save(mapData, close_file = False)
        
        self.mapView = QWebEngineView()
        self.mapView.page().profile().downloadRequested.connect(self.getgeoJson)
        self.mapView.setHtml(mapData.getvalue().decode())
        self.mapView.resize(1000,750)
        self.mapView.setWindowTitle("Draw a Polygon to get Bounding Box coordinates")
        self.mapView.show()
    
    def getgeoJson(self, download):
        path = os.path.dirname(__file__) + "/boundingbox.geojson"
        download.path()
        if path:
            download.setPath(path)
            download.accept()
        import json
        f = open(path)
        bb = json.load(f)
        feature = bb['features'][0]
        geometry= feature['geometry']
        coordinates = geometry['coordinates']
        latList = []
        longList = []
        for item in coordinates[0]:
            latList.append(item[1])
            longList.append(item[0])
        self.bb_coordinates = ((min(longList),max(longList)),(min(latList),max(latList)))
        f.close()

    def getDropdowns(self):
        self.xLabel = QLabel(self)
        self.xLabel.setText("Select X coordinate (Longitude) field:")
        self.xLabel.setFont(QFont('Arial',12))
        self.xLabel.setStyleSheet("color: white")
        self.xLabel.move(50, 100)
        self.xPick = QComboBox(self)
        self.xPick.move(320,100)
        self.xPick.resize(100,20)
        self.xPick.setStyleSheet("background-color: white; color: black")

        self.yLabel = QLabel(self)
        self.yLabel.setText("Select Y coordinate (Latitude) field:")
        self.yLabel.setFont(QFont('Arial',12))
        self.yLabel.setStyleSheet("color: white")
        self.yLabel.move(50, 130)
        self.yPick = QComboBox(self)
        self.yPick.move(320,130)
        self.yPick.resize(100,20)
        self.yPick.setStyleSheet("background-color: white; color: black")

        self.cLabel = QLabel(self)
        self.cLabel.setText("Select a category field from your data:")
        self.cLabel.setFont(QFont('Arial',12))
        self.cLabel.setStyleSheet("color: white")
        self.cLabel.move(50, 160)
        self.cPick = QComboBox(self)
        self.cPick.move(320,160)
        self.cPick.resize(100,20)
        self.cPick.setStyleSheet("background-color: white; color: black")

    def getCatColumn(self):
        self.cCheck = self.cPick.currentText()
        self.parq[self.cCheck] = self.parq[self.cCheck].astype('category')
        self.catItems = self.parq[self.cCheck].unique()
        count = 0
        for c in self.catItems:
            self.colorTable.setItem(count,0, QTableWidgetItem(c))
            count = count + 1
        self.color_key = {}
        for i in list(range(5)):
            self.listItem = self.colorTable.item(i,0)
            if self.listItem is not None and self.listItem.text() != '':
                self.color_key[self.listItem.text()] = 'blank'
        self.colorTable.itemChanged.connect(self.editTable)

    def createTable(self):
        self.tLabel = QLabel(self)
        self.tLabel.setText("Use the Table to customize your colors")
        self.tLabel.move(50, 360)
        self.tLabel.setFont(QFont("Arial", 12))
        self.tLabel.setStyleSheet("color: white")

        self.colorTable = QTableWidget(self)
        self.colorTable.setRowCount(6)
        self.colorTable.setColumnCount(2)
        self.item1 = QTableWidgetItem('Name')
        self.item2 = QTableWidgetItem('Color')
        self.colorTable.setHorizontalHeaderItem(0,self.item1)
        self.colorTable.setHorizontalHeaderItem(1,self.item2)
        self.colorTable.move(50,390)
        self.colorTable.setStyleSheet("background-color: white; color: black")
        self.colorTable.horizontalHeader().setStyleSheet("background-color: white; color: black")
        self.colorTable.verticalHeader().setVisible(False)
        self.colorTable.verticalScrollBar().setStyleSheet("background-color: white; color: black")
        
    def editTable(self, item):
        for i in list(range(5)):
            self.listColorItem = self.colorTable.item(i,1)
            if self.listColorItem is not None and self.listColorItem.text() != '':
                self.color_key[self.colorTable.item(i,0).text()] = self.listColorItem.text()
        
    def exportData(self):
        path = os.path.dirname(__file__)
        exportPath = path + "/export"
        if self.backgroundPick.currentText() == 'black':
            self.color_key
        else:
            self.color_key
            
        self.x_range,self.y_range = [list(r) for r in webm(*self.bb_coordinates)]

        self.export = partial(export_image, background = self.backgroundPick.currentText(), export_path= exportPath)

        def create_image(longitude_range, latitude_range, w=int(self.xPlotEdit.text()), h=int(self.yPlotEdit.text())):
            self.x_range,self.y_range = (longitude_range,latitude_range)
            cvs = ds.Canvas(plot_width=w, plot_height=h, x_range=self.x_range, y_range=self.y_range)
            agg = cvs.points(self.parq, self.xPick.currentText(), self.yPick.currentText(), ds.count_cat(self.cPick.currentText()))
            img = tf.shade(agg, color_key=self.color_key, how = self.aggPick.currentText())
            return img
        
        self.export(create_image(*self.bb_coordinates),"Export")

        self.activateImage()

    def activateImage(self):
        if self.img is None:
            self.img = openImage()
        else:
            self.img = openImage()
        
if __name__ == '__main__':
    path = os.path.dirname(__file__)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    trayIcon = QSystemTrayIcon(QIcon(path+'\images\Icon.png'), parent = app) 
    trayIcon.setToolTip("Datashader GUI")
    trayIcon.show()

    taskbarApproval = 'mycompany.myproduct.subproduct.version'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(taskbarApproval)
    
    ui = datashaderGUI()

    sys.exit(app.exec_())