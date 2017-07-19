# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'myQA.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from QAFromJson_v4 import *

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(502, 414)
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(50, 30, 91, 17))
        self.label.setObjectName("label")
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setGeometry(QtCore.QRect(350, 370, 99, 27))
        self.pushButton.setObjectName("pushButton")
        self.plainTextEdit = QtWidgets.QPlainTextEdit(Form)
        self.plainTextEdit.setGeometry(QtCore.QRect(40, 60, 401, 78))
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.textBrowser = QtWidgets.QTextBrowser(Form)
        self.textBrowser.setGeometry(QtCore.QRect(40, 200, 401, 151))
        self.textBrowser.setObjectName("textBrowser")
        self.pushButton_2 = QtWidgets.QPushButton(Form)
        self.pushButton_2.setGeometry(QtCore.QRect(40, 150, 99, 27))
        self.pushButton_2.setObjectName("pushButton_2")

        self.retranslateUi(Form)
        self.pushButton.clicked.connect(Form.close)
        self.pushButton_2.clicked.connect(self.read_text)
        QtCore.QMetaObject.connectSlotsByName(Form)
    
    def read_text(self):
        question = self.plainTextEdit.document().findBlockByLineNumber(0).text().encode('utf-8')
        answer = QAprosess(question)
        self.textBrowser.setText(answer)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "liverpoolQA"))
        self.label.setText(_translate("Form", "请输入问题:"))
        self.pushButton.setText(_translate("Form", "退出"))
        self.pushButton_2.setText(_translate("Form", "回答"))

