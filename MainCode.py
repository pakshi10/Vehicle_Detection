"""
@author: Akshay Kumar
"""

from PyQt5.QtWidgets import QApplication, QFileDialog,QMainWindow,QDialog
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, Qt,QCoreApplication
from PyQt5.QtGui import QPixmap,QImage

import numpy as np
import cv2
import pafy

import qimage2ndarray
from UI import Ui_MainWindow
from  code_logic import yolo
from Dialogbox import Ui_Dialog

class ProcessingThread(QThread):
    UpdateSignal = pyqtSignal(QImage,int,int,int) #1st Qimage in for video
    #2nd for
    
    def __init__(self,media_path):
        QThread.__init__(self)
        self.flag = False            #in starting no video so set flag is zero
        self.media_path = media_path
       
    def run(self):      #thread run
        cap = cv2.VideoCapture(self.media_path)
        self.frames = 0
        self.flag = True
        while self.flag:
            ret, image = cap.read()
            if ret:
                
                frame,total, high_risk, safe=yolo(image)
                qtimg = qimage2ndarray.array2qimage(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))  #image to qimage so that pyqt can read
                self.UpdateSignal.emit(qtimg,total, high_risk, safe)
        
        cap.release()  #frame over so stop
        
        
    def stop(self):
        self.flag = False


class MainCode(QMainWindow,Ui_MainWindow,Ui_Dialog):
    
    
    def __init__(self):  #button
        super().__init__()
        self.setupUi(self)  #accesing UI-Vechicle Detector
        
        #self.actionVideo.triggered.connect(self.OpenFileFormatVideo)
        #self.actionImage.triggered.connect(self.OpenFileFormatImage)
        #self.actionCam_Feed.triggered.connect(self.OpenExternalDevice)

        self.pushButton_folder.clicked.connect(self.OpenFileFormatVideo)
        self.pushButton_Link.clicked.connect(self.OpenExternalDevice)
        self.pushButton_webcam.clicked.connect(self.Openwebcam)

    
    def releaseFrame(self):  #for stop so thread will be stop
        self.thread.stop()
        self.thread.terminate # try intechanginh posritions
          
    def ThreadFunc(self,media_path):
        self.thread = ProcessingThread(media_path)
        self.pushButton_start.clicked.connect(self.thread.start)  #when you hit start so thread will start

        self.thread.UpdateSignal.connect(self.img_Qpixmap)  #to update our variable
        self.pushButton_stop.clicked.connect(self.releaseFrame)  #when hit enter stop the thread
        
    @pyqtSlot(QImage,int,int,int)
    def img_Qpixmap(self,qtimg,total, high_risk, safe):
        pixmap_Frm = QPixmap.fromImage(qtimg)
        #print(pixmap_Frm.size())
        pixmap_Scld = pixmap_Frm.scaled(1100, 620, Qt.KeepAspectRatio) if pixmap_Frm.width()>1065 and pixmap_Frm.height()>615 else pixmap_Frm
        #pixmap_Scld = pixmap_Frm.scaled(1070, 615, Qt.KeepAspectRatio)
        self.label_3_MediaFrame.setPixmap(pixmap_Scld)
        self.Total_lcdNumber_2.setProperty("intValue", total)
        self.safe_lcdNumber_4.setProperty("intValue", safe)
        self.Low_lcdNumber_3.setProperty("intValue", high_risk)

         
    #def OpenFileFormatImage(self):  #to show on gui
     #  path = filename[0]
      #  image = cv2.imread(path)
      #  image = cv2.resize(image,(640,800),interpolation = cv2.INTER_AREA ) if image.shape[0]>1100 and image.shape[1]>620 else image
      # qtimg = qimage2ndarray.array2qimage(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
       # self.img_Qpixmap(qtimg,_,total_p, low_risk_p, high_risk_p, safe_p)
        
    def OpenFileFormatVideo(self):
        filename = QFileDialog.getOpenFileName(None, "Select Video File", "", "Video (*.mp4 *.avi *.flv)")#,options=QFileDialog.DontUseNativeDialog
        path = filename[0]
        self.ThreadFunc(path)

    def Openwebcam(self):

        path = 0
        self.ThreadFunc(path)

        
        
    def OpenExternalDevice(self):
        Dialog = QDialog()
        self.Dialog = QDialog()
        self.ui = Ui_Dialog()
        self.ui.setupUi(Dialog)
        Dialog.show()
        self.ui.pushButton_2.clicked.connect(self.OpenFileFormatURL)
        self.ui.pushButton_2.clicked.connect(Dialog.close)
        Dialog.exec_()
        
        
    def OpenFileFormatURL(self,url):
        self.url = self.ui.lineEdit.text()
        #'https://www.youtube.com/watch?v=fWZkkDYTLSI'
        vPafy = pafy.new(self.url)
        play = vPafy.getbest(preftype="mp4")
        self.ThreadFunc(play.url)
        

        
        
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    #app.setStyle('Fusion')
    Form = MainCode()
    Form.show()
    sys.exit(app.exec_())
        