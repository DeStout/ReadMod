import sys
import math
import struct
import datetime
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QStackedWidget, QTextEdit, QApplication

class ReadWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.centralStackedWidget = QStackedWidget()
        self.modEdit = QTextEdit()

        self.centralStackedWidget.addWidget(self.modEdit)
        self.setCentralWidget(self.centralStackedWidget)

        self.modEdit.setStatusTip('Read an opened file')
        self.modEdit.setReadOnly(True)

        openFile = QAction('Open', self)
        openFile.setStatusTip('Open a File')
        openFile.triggered.connect(self.readFile)

        self.graphMod = QAction('Graph', self)
        self.graphMod.setStatusTip('Graph an opened .mod File')
        self.graphMod.triggered.connect(self.graphFile)
        self.graphMod.setDisabled(True)

        exitProgram = QAction('Quit', self)
        exitProgram.setStatusTip('Exit the application')
        exitProgram.triggered.connect(self.close)

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(self.graphMod)
        fileMenu.addAction(exitProgram)
        self.statusBar()

        self.setGeometry(150, 150, 900, 800)
        self.setWindowTitle('Read File')
        self.show()

    def readFile(self):
        fileAddress = QFileDialog.getOpenFileName(self, 'Open', 'O:\Prototype\Freeform', 'Mod or Dat (*.mod *.dat);;All Files (*.*)')

        if fileAddress[0]:
            if fileAddress[0].split('.')[-1].lower() == 'mod':
                self.modFile(fileAddress)
            elif fileAddress[0].split('.')[-1].lower() == 'dat':
                self.datFile(fileAddress)
            else:
                print("Unrecognized File")


    def modFile(self, modAddress):
        keyword_length = 'ASSESSMENT_LENGTH'
        keyword_numPoints = 'NUMBER_MOD_POINTS'
        keyword_coefficient = 'ASPHERIC_COEFF'
        keyword_radius = 'ASPHERIC_RADIUS'
        keyword_conicConst = 'ASPHERIC_K'
        keyword_EOR = 'EOR'
        keyword_EOF = 'EOF'

        modFile = open(modAddress[0], 'r')
        with modFile:
            modData = modFile.readlines()

        eorNum = 0
        scanLength = 0
        numScanPoints = 0
        coefficients = []
        self.scanPoints = [[], []]
        lensRadius = 0
        lensConicConstant = 0
        scanStart = 0
        scanStop = 0
        highPoint = None
        lowPoint = None

        for line in modData:
            self.modEdit.insertPlainText(line)

            if keyword_EOR in line:
                eorNum += 1

            if eorNum > 0 and eorNum < 2:
                if keyword_length in line:
                    scanLength = self.notationConversion(line.split(' ')[1])

                elif keyword_numPoints in line:
                    numScanPoints = int(self.notationConversion(line.split(' ')[1]))

                elif keyword_coefficient in line:
                    coefficient = self.notationConversion(line.split(' ')[1])
                    coefficients.append(coefficient)
                    #print('Coefficient ' + str(len(coefficients)) + ': ' + str(coefficient))

                elif keyword_radius in line:
                    lensRadius = self.notationConversion(line.split(' ')[1])

                elif keyword_conicConst in line:
                    lensConicConstant = self.notationConversion(line.split(' ')[1])

            elif keyword_EOR not in line and keyword_EOF not in line and eorNum > 1:
                scanPoint = self.notationConversion(line)

                if len(self.scanPoints[0]) < numScanPoints:
                    self.scanPoints[0].append(scanPoint)

                    if len(self.scanPoints[0]) == 1:
                        scanStart = scanPoint
                    elif len(self.scanPoints[0]) == numScanPoints:
                        scanStop = scanPoint
                else:
                    self.scanPoints[1].append(scanPoint)

                    if highPoint == None or highPoint < scanPoint:
                        highPoint = scanPoint
                    if lowPoint == None or lowPoint > scanPoint:
                        lowPoint = scanPoint
        rms = [0, 0]
        for dataPoint in self.scanPoints[1]:
            rms[0] += math.pow(dataPoint, 2)
            rms[1] += 1
        rms[0] /= rms[1]
        rms[0] = math.sqrt(rms[0])

        print('\nScan Data Points: ' + str(numScanPoints))
        print('Stored points: ' + str(len(self.scanPoints[0])) + ', ' + str(len(self.scanPoints[1])))
        print('\nRadius: ' + str(lensRadius))
        print('Conic Constant: ' + str(lensConicConstant))
        print('High Point: ' + str(highPoint * 1000) + ' um')
        print('Low Point: ' + str(lowPoint * 1000) + ' um')
        print('PV: ' + str((highPoint - lowPoint) * 1000) + ' um')
        print('RMS: ' + str(rms[0] * 1000) + ' um')
        print('Scan Length: ' + str(scanLength) + ' mm')
        print('Data Length: ' + str(scanStop - scanStart) + ' mm')

        self.graphMod.setDisabled(False)

    def datFile(self, datAddress):
        self.modEdit.clear()

        datFile = open(datAddress[0], 'rb')
        with datFile:
            datData = datFile.read()
            headInfo = struct.unpack('>ihi', datData[:10])
            numBodyBytes = struct.unpack('>i', datData[72:76])
            timeStamp = struct.unpack('>i', datData[76:80])
            self.modEdit.insertPlainText('Header Format: ' + str(headInfo[1]) + '\n')
            self.modEdit.insertPlainText('Header Byte Size: ' + str(headInfo[2]) + '\n')
            self.modEdit.insertPlainText('Body Byte Size: ' + str(numBodyBytes[0]) + '\n')
            self.modEdit.insertPlainText('Time Stamp: ' + str(datetime.datetime.fromtimestamp(timeStamp[0]).strftime('%m/%d/%y %H:%M:%S'))+ '\n')

            #File Structure PDF saved in Derek folder
            #Continue to read in .Dat file information (Aquired and Phased)

    def graphFile(self):
        print('Hah! Nice Try')
        self.plotGraph.plot(self.scanPoints[1], self.scanPoints[0])
        #Figure out how to plot graph and add to window
        #Data Points in Taly raw files are z values

    def notationConversion(self, sciNumber):
        baseNumber, exponent = sciNumber.split('e')
        baseNumber = float(baseNumber)
        exponent = int(exponent)

        return baseNumber * 10 ** exponent


if __name__ == '__main__':
    app = QApplication(sys.argv)
    readMod = ReadWindow()
    sys.exit(app.exec_())
