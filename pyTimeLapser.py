# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from PyQt4 import uic, QtGui, QtCore

import numpy as np
import cv2

reload(sys)
sys.setdefaultencoding('utf-8')

class Webcam():
  def __init__(self):
    self.conf = QtCore.QSettings()
    self.MainWindow = uic.loadUi('gui.ui')
    self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    self.eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

    self.autoSet = False
    self.autoSetCycles = 0

    self.cam = cv2.VideoCapture(1)
    self.targetW = 1080
    self.targetH = 1920
    #Set Full HD 1080p resolution
    self.cam.set(3,1920)
    self.cam.set(4,1080)
    #Set HD 720p resolution
#    self.cam.set(3,1280)
#    self.cam.set(4,720)
    #Set HD 720p resolution
    self.cam.set(3,1280)
    self.cam.set(4,960)
    self.ancho = self.cam.get(4)
    self.alto = self.cam.get(3)
    self.zoom = 1
    if self.ancho == 0:
      self.camOk = False
      msg = QtGui.QMessageBox(QtGui.QMessageBox.Critical, "Cámara no encontrada","Verifique la conexión", QtGui.QMessageBox.Ok, self.MainWindow)
      msg.exec_()
    else:
      self.camOk = True
      print "Camera resolution: %dx%d" % (self.ancho, self.alto)
      print "Target resolution: %dx%d" % (self.targetW, self.targetH)
      self.min_zoom = max(self.targetW/float(self.ancho),self.targetH/float(self.alto))
      print "Zoom: ", self.min_zoom
      self.roi = ROI.fromWH((self.ancho - self.targetW)/2, (self.alto  - self.targetH)/2, self.targetW, self.targetH, self.ancho, self.alto)
    self.take = False

    self.toma = 0

    self.simple_gui(not self.conf.value("gui/full").toBool())
    self.MainWindow.action_simple_gui.setChecked(not self.fullGUI)

    self.MainWindow.dfecha.setDate(QtCore.QDate().currentDate())

    self.timer = QtCore.QTimer(self.MainWindow)
    self.MainWindow.connect(self.timer, QtCore.SIGNAL('timeout()'), self.show_frame)
    self.timer.start(1)
    self.MainWindow.action_simple_gui.triggered.connect(self.change_gui_mode)
    self.MainWindow.b_start.clicked.connect(self.act_capt)
    self.MainWindow.b_go.clicked.connect(self.capture)
    self.MainWindow.b_finish.clicked.connect(self.limpia)
    self.MainWindow.b_recap.clicked.connect(self.recap)
    self.MainWindow.b_next.clicked.connect(self.captureNext)
    self.MainWindow.s_moveCapX.valueChanged.connect(self.move_cap_x)
    self.MainWindow.s_moveCapY.valueChanged.connect(self.move_cap_y)
#    self.MainWindow.connect(self.MainWindow.b_start, QtCore.SIGNAL('clicked()'), self.act_capt)
    customControl(self.MainWindow.liveView).connect(self.liveClicked)
    clickable(self.MainWindow.left).connect(self.pictureClicked)
    clickable(self.MainWindow.front).connect(self.pictureClicked)
    clickable(self.MainWindow.right).connect(self.pictureClicked)
    trackMouse(self.MainWindow.l_detail).connect(self.mouseTracked)
    self.MainWindow.dock_detail.hide()


  def change_gui_mode(self, enable):
    self.simple_gui(enable)

  def simple_gui(self, enable):
    self.fullGUI = not enable
    self.conf.setValue("gui/full",  self.fullGUI)
    self.MainWindow.s_moveCapX.setVisible(self.fullGUI)
    self.MainWindow.s_moveCapY.setVisible(self.fullGUI)

  def decorar(self, frame, type):
    color=(233,107,46)
    self.horizontal(frame, color)
    if type == 'f':
      self.vertical_frontal(frame, color)
    else:
      self.vertical_lateral(frame, color)
    return frame

  def cvFrame2pixmap(self, frame):
    data = frame.tostring()
    height, width, channels = frame.shape
    image = QtGui.QImage(data, width, height, channels * width, QtGui.QImage.Format_RGB888)
    pixmap = QtGui.QPixmap()
    pixmap.convertFromImage(image.rgbSwapped())
    return pixmap

  def recap(self):
    self.toma = self.toma_t
    self.MainWindow.dock_detail.hide()

  def pictureClicked(self, obj):
    #TODO: GUI retro
    if   obj == self.MainWindow.left:
      toma = 'i'
    elif obj == self.MainWindow.front:
      toma = 'f'
    elif obj== self.MainWindow.right:
      toma = 'd'
    else:
      return
    self.detailView(toma, False)
  def mouseTracked(self, obj, x, y):
    capture  = self.detail_img.copy()
    capture  = self.decorar(capture, self.toma_t)
    self.raya_vertical(capture, x, (0,0,255))
    self.raya_horizontal(capture, y, (0,0,255))
    pixmap   = self.cvFrame2pixmap(capture)
    self.MainWindow.l_detail.setPixmap(pixmap)

  def detailView(self, toma, new):
    self.toma_t = toma
    location = self.ruta + self.expediente +"_"+ toma + ".jpg"
    capture  = cv2.imread(location)
    self.detail_img = capture
    capture  = self.decorar(capture, toma)
    pixmap   = self.cvFrame2pixmap(capture)

    self.MainWindow.l_detail.setPixmap(pixmap)
    if not self.MainWindow.dock_detail.isVisible():
      self.MainWindow.dock_detail.show()
      self.MainWindow.dock_detail.setFloating(True)
    self.MainWindow.b_next.setVisible(new)

  def captureNext(self):
    if self.toma == 'i':
      self.toma = 'd'
    elif self.toma == 'f':
      self.toma = 'i'
    elif self.toma == 'd':
#      self.toma='f'
      self.toma=''
      self.MainWindow.b_finish.setEnabled(True)

    self.MainWindow.dock_detail.hide()

#    self.toma_t = toma
    #Alex
#    obj.setStyleSheet("""
#      .QWidget {
#         border: 2px solid blue;
#         border-radius: 2px;
#         background-color: rgb(255, 255, 255);
#        }
#      """)

  def liveClicked(self, type, x, y, delta):
    max_speed = 15
    if type == customControlOps.actionCapture:
      self.capture()
    elif type == customControlOps.actionZoom:	#zoom
      zoom_old = self.zoom
      print delta
      self.zoom *= 1+delta/float(1000)
      if self.zoom > 1:
        self.zoom = 1
      elif self.zoom < self.min_zoom:
        self.zoom = self.min_zoom
      zoom_delta = zoom_old - self.zoom
      if zoom_delta == 0:
        return
      if self.zoom != 1:
        ancho = self.ancho*self.zoom 
        alto  = self.alto*self.zoom
        print "Zoom camera resolution: %dx%d" % (ancho, alto)
        self.roi.zoomTo(x, y, zoom_delta, ancho, alto)
      else:
        self.roi = ROI.fromWH((self.ancho - self.targetW)/2, (self.alto  - self.targetH)/2, self.targetW, self.targetH, self.ancho, self.alto)
    elif type == customControlOps.actionMouseMove:
      if self.fullGUI:
        self.MainWindow.s_moveCapX.setValue(self.MainWindow.s_moveCapX.value()+(x-.5)*2*max_speed)
        self.MainWindow.s_moveCapY.setValue(self.MainWindow.s_moveCapY.value()-(y-.5)*2*max_speed)
    elif type == customControlOps.actionKbMove:
      self.roi.moveX(x*2*max_speed)
      self.roi.moveY(y*2*max_speed)

  def move_cap_x(self, value):
    self.roi.moveToPartX(value)
  def move_cap_y(self, value):
    self.roi.moveToPartY(value)

  def act_capt(self):
    fecha	= str(self.MainWindow.dfecha.date().toString("dd-MM-yyyy"))
    nombre	= unicode(self.MainWindow.lNom.text().toUtf8(), encoding="UTF-8")
    freq	= 1000/self.MainWindow.spShotss.value()

    if len(nombre)<2:
      msg = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Información incompleta","Por favor ingrese todos los campos", QtGui.QMessageBox.Ok, self.MainWindow)
      retval = msg.exec_()
      return

    self.MainWindow.b_go.setEnabled(True)
    self.MainWindow.b_start.setEnabled(False)
    self.MainWindow.b_finish.setEnabled(True)
    self.MainWindow.dfecha.setEnabled(False)
    self.MainWindow.lNom.setEnabled(False)
    self.MainWindow.spShotss.setEnabled(False)

    self.ruta = './fotos/'+ nombre + "/"
    if not os.path.exists(self.ruta):
      os.makedirs(self.ruta)

    self.ruta += fecha + ("_%d"%freq) + "/"
    if not os.path.exists(self.ruta):
      os.makedirs(self.ruta)
    else:
      msg = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Sobrescribir?","Ya existe un registro para el usuario esta seguro de continuar, se sobreescribirán los registros ...", QtGui.QMessageBox.Ok, self.MainWindow)
      retval = msg.exec_()
    self.toma = 0

    self.timer2 = QtCore.QTimer(self.MainWindow)
 #   self.timer2.setSingleShot(True)
    self.MainWindow.connect(self.timer2, QtCore.SIGNAL('timeout()'), self.capture)
    self.timer2.start(freq)
    print freq

  def capture(self):
    self.take = True

  def limpia(self):
    #TODO: Use for
    self.timer2.stop()
    self.MainWindow.lNom.setText("")
    self.MainWindow.lNom.setEnabled(True)
    self.MainWindow.spShotss.setEnabled(True)
    self.MainWindow.b_start.setEnabled(True)
    self.MainWindow.b_finish.setEnabled(False)
    self.MainWindow.b_go.setEnabled(False)
    pixmap = QtGui.QPixmap()
    self.MainWindow.left.setPixmap(pixmap)
    self.MainWindow.front.setPixmap(pixmap)
    self.MainWindow.right.setPixmap(pixmap)
    self.toma = 0
    self.MainWindow.dock_detail.hide()

  def show_frame(self):
    if not self.camOk:
      return
    # Capture frame-by-frame
    ret, frame = self.cam.read()

    #Zoom Adjustment
    if self.zoom != 1:
#      frame = cv2.resize(frame, fx=self.zoom, fy=self.zoom)
#      frame = cv2.resize(frame, dsize=(int(self.zoom*self.ancho), int(self.zoom*self.alto)))
      frame = cv2.resize(frame, dsize=(int(self.zoom*self.alto), int(self.zoom*self.ancho)), interpolation=cv2.INTER_AREA)
    frame = frame[self.roi.start_X:self.roi.end_X, self.roi.start_Y:self.roi.end_Y]
    #VOLTEA LA IMAGEN CV
    frame = cv2.transpose(frame)
    frame = cv2.flip(frame,1)

    if self.take :
      cv2.imwrite(self.ruta + ("%05d" %self.toma) + ".jpg", frame)
      self.toma += 1
#      self.detailView(self.toma, True)

#    frame  = self.decorar(frame, self.toma)
    pixmap = self.cvFrame2pixmap(frame)

#TODO: Hacer en openCV antes de generar pixmap
    pixmap = pixmap.scaledToWidth(self.targetW/2)

    self.MainWindow.liveView.setPixmap(pixmap)

    if self.take :
#      if self.toma == 'i':
#        updateGUI = self.MainWindow.left
#      elif self.toma == 'f':
#        updateGUI = self.MainWindow.front
#      elif self.toma == 'd':
#        updateGUI = self.MainWindow.right

#      updateGUI.setPixmap(pixmap.scaledToWidth(120))
      self.take = False

  def raya_vertical(self, frame, x, color = (0,0,0)):
    cv2.line(frame,(int(x),0),(int(x),int(self.targetH)),color,2)

  def raya_horizontal(self, frame, y, color =(0,0,0)):
    cv2.line(frame,(0,int(y)),(int(self.targetW),int(y)),color,2)

  def vertical_frontal(self, frame, color = (0,0,0)):
    self.raya_vertical(frame, self.targetW/2,	color)
    self.raya_vertical(frame, (self.targetW/2)+120,	color)
    self.raya_vertical(frame, (self.targetW/2)-120,	color)
    self.raya_vertical(frame, (self.targetW/2)+144,	color)
    self.raya_vertical(frame, (self.targetW/2)-144,	color)

  def vertical_lateral(self, frame, color = (0,0,0)):
    self.raya_vertical(frame, (self.targetW/2)+144, color)
    self.raya_vertical(frame, (self.targetW/2)-144, color)

  def horizontal(self, frame, color = (0,0,0)):
    self.raya_horizontal(frame, 253,	color)
    self.raya_horizontal(frame, 287,	color)
    self.raya_horizontal(frame, 322,	color)

  def __del__(self):
    print "Terminando..."
    self.cam.release()

class customControlOps:
  actionMouseMove = 0
  actionCapture = 1
  actionKbMove = 2
  actionZoom = 3

def customControl(widget):
  class Filter(QtCore.QObject):
    modify = QtCore.pyqtSignal(int, float, float, float)
#    move_X = 0.03
    def eventFilter(self, obj, event):
      if obj == widget:
        if event.type() == QtCore.QEvent.MouseButtonRelease:
          self.p_X = -1
        elif event.type() == QtCore.QEvent.MouseButtonPress or event.type() == QtCore.QEvent.MouseMove:
          if obj.rect().contains(event.pos()):
            width  = obj.rect().width()
            height = obj.rect().height()
            x = event.pos().x()
            y = event.pos().y()
            self.p_X = x/float(width)
            self.p_Y = y/float(height)

            self.modify.emit(customControlOps.actionMouseMove, self.p_X,self.p_Y, 0)
            return True
        elif event.type() == QtCore.QEvent.Paint:
          try:
            if self.p_X != -1:
              self.modify.emit(actionKbMove,self.p_X,self.p_Y, 0)
          except:
            pass
        elif event.type() == QtCore.QEvent.KeyPress:
          p_X = 0
          p_Y = 0
          if event.isAutoRepeat():
            self.move_X *= 1.2
            if self.move_X > 3:
              self.move_X *= 3
          else:
            p_X = 0
            p_Y = 0
            self.move_X = 0.05
          if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.modify.emit(customControlOps.actionCapture, p_X, p_Y, 0)
            return True
          if event.key() == QtCore.Qt.Key_Left:
            p_X = -self.move_X
          elif event.key() == QtCore.Qt.Key_Right: 
            p_X = self.move_X
          if event.key() == QtCore.Qt.Key_Up:
            p_Y = self.move_X
          elif event.key() == QtCore.Qt.Key_Down:
            p_Y = -self.move_X
          self.modify.emit(customControlOps.actionKbMove,p_X,p_Y, 0)
          return True
        elif event.type() == QtCore.QEvent.Wheel:
          self.modify.emit(customControlOps.actionZoom, event.pos().x(), event.pos().y(), event.delta())
#        else:
#          print event.type()
      return False
  filter = Filter(widget)
  widget.installEventFilter(filter)
  return filter.modify

def clickable(widget):
  class Filter(QtCore.QObject):
    clicked = QtCore.pyqtSignal(QtCore.QObject)
    def eventFilter(self, obj, event):       
      if obj == widget:
        if event.type() == QtCore.QEvent.MouseButtonPress:
#        if event.type() == QtCore.QEvent.MouseButtonDblClick:
          if obj.rect().contains(event.pos()):
            self.clicked.emit(obj)
            return True
      return False
  filter = Filter(widget)
  widget.installEventFilter(filter)
  return filter.clicked

def trackMouse(widget):
  class Filter(QtCore.QObject):
    motion = QtCore.pyqtSignal(QtCore.QObject, int, int)
    def eventFilter(self, obj, event):
      if obj == widget:
        if event.type() == QtCore.QEvent.MouseMove:
          if obj.rect().contains(event.pos()):
            x = event.pos().x()
            y = event.pos().y()
            self.motion.emit(obj, x, y)
            return True
      return False
  filter = Filter(widget)
  widget.installEventFilter(filter)
  return filter.motion

class ROI():
  def __init__(self,start_X, end_X, start_Y, end_Y, max_X, max_Y):
    self.start_X = int(start_X)
    self.end_X   = int(end_X)
    self.start_Y = int(start_Y)
    self.end_Y   = int(end_Y)
    self.width   = int(end_X-start_X)
    self.height  = int(end_Y-start_Y)
    self.max_X   = int(max_X)
    self.max_Y   = int(max_Y)

  @classmethod
  def fromWH(cls, start_X, start_Y, width, height, max_X, max_Y):
    end_X = start_X + width
    end_Y = start_Y + height
    return cls(start_X, end_X, start_Y, end_Y, max_X, max_Y)

  def moveToCenter(self):
    width  = end_X-start_X
    height = end_Y-start_Y 
    self.start_X = (max_X-width)/2
    self.end_X   = (max_X+width)/2
    self.start_Y = (max_Y-height)/2
    self.end_Y   = (max_Y+height)/2

  def moveToXY(self, x, y, center = False):
    x = int(x)
    y = int(y)
    if center:
      x = x-self.width/2
      y = y-self.height/2
    if x>self.max_X:
      x = self.max_X-self.width
    elif x<0:
      x=0
    if y>self.max_Y:
      y = self.max_Y-self.height
    elif y<0:
      y=0
    self.start_X = x
    self.end_X = self.start_X + self.width
    self.start_Y = y
    self.end_Y = self.start_Y + self.height


  def moveToPartX(self, value):
    if value>100:
      value = 100
    elif value<0:
      value=0
    to = int(value*(self.max_X-self.width)/100)
    self.start_X = to
    self.end_X = self.start_X + self.width
  def moveX(self, n):
    if n<0:
      self.moveLeft(-n)
    else:
      self.moveRight(n)
  def moveLeft(self, n):
    self.start_X -= n
    if self.start_X < 0:
      self.start_X=0
    self.end_X = self.start_X + self.width
  def moveRight(self, n):
    self.end_X += n
    if self.end_X > self.max_X:
      self.end_X=self.max_X
    self.start_X = self.end_X - self.width

  def moveToPartY(self, value):
    if value>100:
      value = 100
    elif value<0:
      value=0
    to = int(value*(self.max_Y-self.height)/100)
    self.start_Y = to
    self.end_Y = self.start_Y + self.height
  def moveY(self, n):
    if n<0:
      self.moveUp(-n)
    else:
      self.moveDown(n)
  def moveUp(self, n):
    self.start_Y -= n
    if self.start_Y < 0:
      self.start_Y=0
    self.end_Y = self.start_Y + self.height
  def moveDown(self, n):
    self.end_Y += n
    if self.end_Y > self.max_Y:
      self.end_Y=self.max_Y
    self.start_Y = self.end_Y - self.height

#  def __init__(self,start_X, end_X, start_Y, end_Y, max_X, max_Y):
  def zoomTo(self, x, y, zoom, ancho, alto):
    print "Zoom"
#Calcular ¿?
    self.max_X   = int(self.max_X*zoom)
    self.max_Y   = int(self.max_Y*zoom)
    if self.max_X != ancho or self.max_Y != alto:
      print "Resolution Bug...  Fixme"
      self.max_X   = int(ancho)
      self.max_Y   = int(alto)

    self.start_X = int(zoom*(self.start_X-x)+x)
    if self.start_X < 0:
      self.start_X = 0
    self.end_X   = self.start_X + self.width
    if self.end_X > self.max_X:
      self.end_X = self.max_X
      self.start_X = self.end_X - self.width

    self.start_Y = int(zoom*(self.start_Y-y)+y) 
    if self.start_Y < 0:
      self.start_Y = 0
    self.end_Y   = self.start_Y + self.height
    if self.end_Y > self.max_Y:
      self.end_Y = self.max_Y
      self.start_Y = self.end_Y - self.height

if __name__ == "__main__":
  QtCore.QCoreApplication.setOrganizationName("División Científica")
  QtCore.QCoreApplication.setOrganizationDomain("pf.gob.mx");
  QtCore.QCoreApplication.setApplicationName("BioCapture");
  app = QtGui.QApplication(sys.argv)
  webcam = Webcam()
  webcam.MainWindow.showMaximized()
  app.exec_()
