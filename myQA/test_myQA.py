# -*- coding: utf-8 -*-
import sys 
from PyQt5.QtWidgets import *  
from myQA_v4 import Ui_Form

class mywindow(QWidget):  

    def __init__(self):  
        super(mywindow,self).__init__()  
        self.__ui=Ui_Form()
        self.__ui.setupUi(self)
 

app = QApplication(sys.argv)  
windows = mywindow()  
windows.show()  
sys.exit(app.exec_())  
