from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import os
import socket
import sys


class Matrix:
    def __init__(self, s):
        self.size = s
        self.data = []


class Worker(QObject):
    finished = pyqtSignal(str)
    connection_error = pyqtSignal()

    def __init__(self, message, address, matrix_size):
        super().__init__()
        self.message = message
        self.address = address
        self.matrix_size = matrix_size

    def run(self):
        """
        Connects to the server, sends matrices data and receive the final result.
        :return: None
        """
        format = 'cp437'
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect(self.address)
        except Exception as e:
            self.connection_error.emit()
            print(e)
            return

        result = ''
        try:
            for chunk in [self.message[i:i+100] for i in range(0, len(self.message), 100)]:
                if len(chunk) < 100:
                    formatted_chunk = chunk + ' ' * (100-len(chunk))
                    total_sent = 0
                    while total_sent < 100:
                        sent = client.send(formatted_chunk[total_sent:].encode(format))
                        if sent == 0:
                            raise RuntimeError("socket connection broken")
                        total_sent = total_sent + sent
                else:
                    client.send(chunk.encode(format))

            numbers_counter = 0
            while numbers_counter < self.matrix_size * self.matrix_size:
                bytes_received = 0
                chunks = []
                while bytes_received < 100:
                    chunk = client.recv(100 - bytes_received).decode(format, errors='ignore')
                    if chunk == '':
                        raise RuntimeError("socket connection broken")
                    chunks.append(chunk)
                    bytes_received = bytes_received + len(chunk)
                received = ''.join(chunks)

                numbers_counter += received.count(' ')
                result += received

        except Exception as e:
            self.connection_error.emit()
            print(e)
            return

        self.finished.emit(result)


class UIMainWindow(object):
    def __init__(self, main_window):
        # Setting up GUI
        main_window.setObjectName("Mnożenie macierzy")
        main_window.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(main_window)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox_connection = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_connection.setGeometry(QtCore.QRect(10, 10, 771, 101))
        self.groupBox_connection.setObjectName("groupBox_connection")
        self.label_ip = QtWidgets.QLabel(self.groupBox_connection)
        self.label_ip.setGeometry(QtCore.QRect(20, 30, 111, 21))
        self.label_ip.setObjectName("label_ip")
        self.lineEdit_ip = QtWidgets.QLineEdit(self.groupBox_connection)
        self.lineEdit_ip.setGeometry(QtCore.QRect(130, 30, 301, 22))
        self.lineEdit_ip.setObjectName("lineEdit_ip")
        self.lineEdit_port = QtWidgets.QLineEdit(self.groupBox_connection)
        self.lineEdit_port.setGeometry(QtCore.QRect(130, 60, 301, 22))
        self.lineEdit_port.setText("")
        self.lineEdit_port.setObjectName("lineEdit_port")
        self.label_port = QtWidgets.QLabel(self.groupBox_connection)
        self.label_port.setGeometry(QtCore.QRect(20, 60, 111, 21))
        self.label_port.setObjectName("label_port")
        self.groupBox_inputType = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_inputType.setGeometry(QtCore.QRect(10, 130, 281, 181))
        self.groupBox_inputType.setObjectName("groupBox_inputType")
        self.label_size = QtWidgets.QLabel(self.groupBox_inputType)
        self.label_size.setGeometry(QtCore.QRect(10, 140, 221, 21))
        self.label_size.setObjectName("label_size")
        self.pushButton_size = QtWidgets.QPushButton(self.groupBox_inputType)
        self.pushButton_size.setGeometry(QtCore.QRect(200, 133, 71, 31))
        self.pushButton_size.setObjectName("pushButton_size")
        self.pushButton_inputType = QtWidgets.QPushButton(self.groupBox_inputType)
        self.pushButton_inputType.setGeometry(QtCore.QRect(200, 50, 71, 51))
        self.pushButton_inputType.setObjectName("pushButton_inputType")
        self.radioButton_fileInput = QtWidgets.QRadioButton(self.groupBox_inputType)
        self.radioButton_fileInput.setGeometry(QtCore.QRect(10, 80, 181, 20))
        self.radioButton_fileInput.setObjectName("radioButton_fileInput")
        self.radioButton_manualInput = QtWidgets.QRadioButton(self.groupBox_inputType)
        self.radioButton_manualInput.setGeometry(QtCore.QRect(10, 50, 181, 20))
        self.radioButton_manualInput.setObjectName("radioButton_manualInput")
        self.label_inputType = QtWidgets.QLabel(self.groupBox_inputType)
        self.label_inputType.setGeometry(QtCore.QRect(10, 20, 271, 16))
        self.label_inputType.setObjectName("label_inputType")
        self.spinBox_size = QtWidgets.QSpinBox(self.groupBox_inputType)
        self.spinBox_size.setGeometry(QtCore.QRect(130, 141, 61, 21))
        self.spinBox_size.setMinimum(1)
        self.spinBox_size.setMaximum(5)
        self.spinBox_size.setObjectName("spinBox_size")
        self.groupBox_input = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_input.setEnabled(True)
        self.groupBox_input.setGeometry(QtCore.QRect(10, 330, 281, 221))
        self.groupBox_input.setObjectName("groupBox_input")
        self.gridLayoutWidget = QtWidgets.QWidget(self.groupBox_input)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 40, 261, 141))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.lineEdit_m34 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m34.setObjectName("lineEdit_m34")
        self.gridLayout.addWidget(self.lineEdit_m34, 2, 3, 1, 1)
        self.lineEdit_m42 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m42.setObjectName("lineEdit_m42")
        self.gridLayout.addWidget(self.lineEdit_m42, 3, 1, 1, 1)
        self.lineEdit_m44 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m44.setObjectName("lineEdit_m44")
        self.gridLayout.addWidget(self.lineEdit_m44, 3, 3, 1, 1)
        self.lineEdit_m31 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m31.setObjectName("lineEdit_m31")
        self.gridLayout.addWidget(self.lineEdit_m31, 2, 0, 1, 1)
        self.lineEdit_m12 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m12.setObjectName("lineEdit_m12")
        self.gridLayout.addWidget(self.lineEdit_m12, 0, 1, 1, 1)
        self.lineEdit_m13 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m13.setObjectName("lineEdit_m13")
        self.gridLayout.addWidget(self.lineEdit_m13, 0, 2, 1, 1)
        self.lineEdit_m21 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m21.setObjectName("lineEdit_m21")
        self.gridLayout.addWidget(self.lineEdit_m21, 1, 0, 1, 1)
        self.lineEdit_m32 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m32.setObjectName("lineEdit_m32")
        self.gridLayout.addWidget(self.lineEdit_m32, 2, 1, 1, 1)
        self.lineEdit_m23 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m23.setObjectName("lineEdit_m23")
        self.gridLayout.addWidget(self.lineEdit_m23, 1, 2, 1, 1)
        self.lineEdit_m22 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m22.setObjectName("lineEdit_m22")
        self.gridLayout.addWidget(self.lineEdit_m22, 1, 1, 1, 1)
        self.lineEdit_m45 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m45.setObjectName("lineEdit_m45")
        self.gridLayout.addWidget(self.lineEdit_m45, 3, 4, 1, 1)
        self.lineEdit_m25 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m25.setObjectName("lineEdit_m25")
        self.gridLayout.addWidget(self.lineEdit_m25, 1, 4, 1, 1)
        self.lineEdit_m52 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m52.setObjectName("lineEdit_m52")
        self.gridLayout.addWidget(self.lineEdit_m52, 4, 1, 1, 1)
        self.lineEdit_m54 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m54.setObjectName("lineEdit_m54")
        self.gridLayout.addWidget(self.lineEdit_m54, 4, 3, 1, 1)
        self.lineEdit_m43 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m43.setObjectName("lineEdit_m43")
        self.gridLayout.addWidget(self.lineEdit_m43, 3, 2, 1, 1)
        self.lineEdit_m24 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m24.setObjectName("lineEdit_m24")
        self.gridLayout.addWidget(self.lineEdit_m24, 1, 3, 1, 1)
        self.lineEdit_m15 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m15.setObjectName("lineEdit_m15")
        self.gridLayout.addWidget(self.lineEdit_m15, 0, 4, 1, 1)
        self.lineEdit_m51 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m51.setObjectName("lineEdit_m51")
        self.gridLayout.addWidget(self.lineEdit_m51, 4, 0, 1, 1)
        self.lineEdit_m35 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m35.setObjectName("lineEdit_m35")
        self.gridLayout.addWidget(self.lineEdit_m35, 2, 4, 1, 1)
        self.lineEdit_m41 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m41.setObjectName("lineEdit_m41")
        self.gridLayout.addWidget(self.lineEdit_m41, 3, 0, 1, 1)
        self.lineEdit_m53 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m53.setObjectName("lineEdit_m53")
        self.gridLayout.addWidget(self.lineEdit_m53, 4, 2, 1, 1)
        self.lineEdit_m55 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m55.setObjectName("lineEdit_m55")
        self.gridLayout.addWidget(self.lineEdit_m55, 4, 4, 1, 1)
        self.lineEdit_m14 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m14.setObjectName("lineEdit_m14")
        self.gridLayout.addWidget(self.lineEdit_m14, 0, 3, 1, 1)
        self.lineEdit_m33 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m33.setObjectName("lineEdit_m33")
        self.gridLayout.addWidget(self.lineEdit_m33, 2, 2, 1, 1)
        self.lineEdit_m11 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_m11.setObjectName("lineEdit_m11")
        self.gridLayout.addWidget(self.lineEdit_m11, 0, 0, 1, 1)
        self.label_matrix = QtWidgets.QLabel(self.groupBox_input)
        self.label_matrix.setGeometry(QtCore.QRect(10, 20, 281, 16))
        self.label_matrix.setObjectName("label_matrix")
        self.pushButton_calculate = QtWidgets.QPushButton(self.groupBox_input)
        self.pushButton_calculate.setGeometry(QtCore.QRect(90, 190, 93, 21))
        self.pushButton_calculate.setObjectName("pushButton_calculate")
        self.groupBox_output = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_output.setGeometry(QtCore.QRect(320, 130, 461, 421))
        self.groupBox_output.setObjectName("groupBox_output")
        self.textBrowser_output = QtWidgets.QTextBrowser(self.groupBox_output)
        self.textBrowser_output.setGeometry(QtCore.QRect(10, 20, 451, 391))
        self.textBrowser_output.setObjectName("textBrowser_output")
        main_window.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(main_window)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 26))
        self.menubar.setObjectName("menubar")
        main_window.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(main_window)
        self.statusbar.setObjectName("statusbar")
        main_window.setStatusBar(self.statusbar)

        self.set_gui_element_names(main_window)
        QtCore.QMetaObject.connectSlotsByName(main_window)
        self.enable_matrix_input_size(False)

        # Creating initial matrices
        self.matrix1 = None
        self.matrix2 = None
        self.is_first_matrix_imputed = False

        self.input = []
        self.input.append([self.lineEdit_m11, self.lineEdit_m12, self.lineEdit_m13, self.lineEdit_m14,
                           self.lineEdit_m15])
        self.input.append([self.lineEdit_m21, self.lineEdit_m22, self.lineEdit_m23, self.lineEdit_m24,
                           self.lineEdit_m25])
        self.input.append([self.lineEdit_m31, self.lineEdit_m32, self.lineEdit_m33, self.lineEdit_m34,
                           self.lineEdit_m35])
        self.input.append([self.lineEdit_m41, self.lineEdit_m42, self.lineEdit_m43, self.lineEdit_m44,
                           self.lineEdit_m45])
        self.input.append([self.lineEdit_m51, self.lineEdit_m52, self.lineEdit_m53, self.lineEdit_m54,
                           self.lineEdit_m55])

        # Connecting buttons to their actions
        self.pushButton_inputType.clicked.connect(self.submit_input_type)
        self.pushButton_size.clicked.connect(self.submit_matrix_size)
        self.pushButton_calculate.clicked.connect(self.submit_matrix)
        self.radioButton_manualInput.setChecked(True)
        self.groupBox_input.setEnabled(False)

    def enable_matrix_input_size(self, enabled):
        self.label_size.setEnabled(enabled)
        self.spinBox_size.setEnabled(enabled)
        self.pushButton_size.setEnabled(enabled)

    def show_error_message(self, message):
        """
        Displays error dialog window with the specific message.
        :param message: (str) message that will be displayed
        :return: None
        """
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle('Error')
        msg.exec_()

    def submit_input_type(self):
        if self.radioButton_manualInput.isChecked():
            self.enable_matrix_input_size(True)
        else:
            self.enable_matrix_input_size(False)
            self.groupBox_input.setEnabled(False)
            self.open_file()

    def enable_input(self, matrix):
        """
        Sets enable adequate number of matrices line inputs (dependent on size of the matrix).
        :param matrix: specific matrix
        :return: None
        """
        self.is_first_matrix_imputed = False
        self.groupBox_input.setEnabled(True)
        for i, row in enumerate(self.input):
            for j, element in enumerate(row):
                if i > matrix.size - 1 or j > matrix.size - 1:
                    element.setEnabled(False)
                else:
                    element.setEnabled(True)

    def submit_matrix_size(self):
        self.clear_input()
        size = self.spinBox_size.text()
        self.matrix1 = Matrix(int(size))
        self.matrix2 = Matrix(int(size))
        self.enable_input(self.matrix1)

    def clear_input(self):
        """
        Clears matrices line inputs.
        :return: None
        """
        for row in self.input:
            for element in row:
                element.setText('')

    def pass_data_to_matrix(self, matrix):
        """
        Saves manually provided data in the correct matrix.
        :param matrix: matrix in which the data will be saved
        :return: None
        """
        matrix.data = []
        for i in range(MAX_SIZE):
            if i < matrix.size:
                matrix.data.append([])
                for j in range(MAX_SIZE):
                    if j < matrix.size:
                        matrix.data[-1].append(int(self.input[i][j].text()))

    def submit_matrix(self):
        """
        Validates and changes labels after clicking button responsible for submitting matrix.
        :return: None
        """
        if not self.is_first_matrix_imputed:
            for i in range(MAX_SIZE):
                for j in range(MAX_SIZE):
                    if self.input[i][j].isEnabled() and not self.input[i][j].text().isnumeric():
                        self.show_error_message('Nieporawne dane!')
                        return

            # if there is no error in the data
            self.pass_data_to_matrix(self.matrix1)
            self.label_matrix.setText('Wprowadź drugą macierz:')
            self.pushButton_calculate.setText('Oblicz')
            self.is_first_matrix_imputed = True
        else:
            for i in range(MAX_SIZE):
                for j in range(MAX_SIZE):
                    if self.input[i][j].isEnabled() and not self.input[i][j].text().isnumeric():
                        self.show_error_message('Nieporawne dane!')
                        return

            # if there is no error in the data
            self.pass_data_to_matrix(self.matrix2)
            self.get_answer()
            self.is_first_matrix_imputed = False
            self.clear_input()
            self.pushButton_calculate.setText('Potwierdź')
            self.label_matrix.setText('Wprowadź pierwszą macierz:')

    def show_result(self, result):
        """
        Displays the final result in a correct form.
        :param result: string containing final result
        :return: None
        """
        formatted_result = self.format_result(result)
        self.textBrowser_output.setText(formatted_result)

    def get_answer(self):
        """
        Validates server data and creates a new thread responsible for sending matrices and receiving the final result.
        :return: None
        """
        port = self.lineEdit_port.text()
        if port == '':
            self.show_error_message('Nie podano numeru portu!')
            return
        port = int(port)

        ip = self.lineEdit_ip.text()
        if ip == '':
            self.show_error_message('Nie podano adresu ip!')
            return
        address = (ip, port)

        message = str(self.matrix1.size) + ' ' + str(self.matrix1.data) + ' ' + str(self.matrix2.data) + '\0'
        message = message.replace('[', '')
        message = message.replace(']', '')
        message = message.replace(',', '')

        self.thread = QThread()
        self.worker = Worker(message, address, self.matrix1.size)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.show_result)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.connection_error.connect(self.report_connection_error)
        self.thread.start()

    def report_connection_error(self):
        self.show_error_message('Nie udało się połączyć z serwerem!')

    def format_result(self, result):
        """
        Formats the final result to the correct form.
        :param result: string containing initial result
        :return: string containing formatted result
        """
        formatted_result = ''
        matrix_size = self.matrix1.size
        spaces_conuter = 0
        for i in range(len(result)):
            if result[i] == ' ':
                spaces_conuter += 1
                if spaces_conuter == matrix_size:
                    formatted_result += '\n'
                    spaces_conuter = 0
                else:
                    formatted_result += result[i]
            else:
                formatted_result += result[i]
        return formatted_result

    def load_data(self, lines):
        """
        Validates the data and transforms it to the matrix form.
        :param lines: List of strings containing matrices data.
        :return: None
        """
        if len(lines) % 2 == 1:
            self.show_error_message('Dane w podanym pliku są niepoprawne!')
            return
        self.matrix1 = Matrix(len(lines) // 2)
        self.matrix2 = Matrix(len(lines) // 2)
        matrix = self.matrix1
        for i, line in enumerate(lines):
            if i == matrix.size:
                matrix = self.matrix2
            try:
                matrix.data.append(list(map(int, line.split(';'))))
            except ValueError:
                self.matrix1 = None
                self.matrix2 = None
                self.show_error_message('Dane w podanym pliku są niepoprawne!')
                return

    def open_file(self):
        """
        Opens choosing file dialog and the chosen file
        :return: None
        """
        name = QtWidgets.QFileDialog.getOpenFileName(
            caption='Wybierz plik z danymi',
            directory=os.getcwd(),
            filter='Excel File (*.csv)')
        if name[0] != '':
            try:
                with open(name[0]) as file:
                    lines = file.readlines()
                    self.load_data(lines)
                    self.get_answer()
            except OSError:
                self.show_error_message('Wybrano zły plik!')

    def set_gui_element_names(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("main_window", "MainWindow"))
        self.groupBox_connection.setTitle(_translate("main_window", "Połączenie"))
        self.label_ip.setText(_translate("main_window", "Adres ip serwera:"))
        self.label_port.setText(_translate("main_window", "Numer portu:"))
        self.groupBox_inputType.setTitle(_translate("main_window", "Sposób wprowadzania danych"))
        self.label_size.setText(_translate("main_window", "Rozmiar macierzy:"))
        self.pushButton_size.setText(_translate("main_window", "Potwierdź"))
        self.pushButton_inputType.setText(_translate("main_window", "Potwierdż"))
        self.radioButton_fileInput.setText(_translate("main_window", "Wprowadź dane z pliku"))
        self.radioButton_manualInput.setText(_translate("main_window", "Wprowadź dane ręcznie"))
        self.label_inputType.setText(_translate("main_window", "Wybierz sposób wprowadzania danych:"))
        self.groupBox_input.setTitle(_translate("main_window", "Ręczne wprowadzanie danych"))
        self.label_matrix.setText(_translate("main_window", "Wprowadź pierwszą macierz:"))
        self.pushButton_calculate.setText(_translate("main_window", "Potwierdź"))
        self.groupBox_output.setTitle(_translate("main_window", "Wyniki"))


if __name__ == "__main__":
    MAX_SIZE = 5  # Maximum size of matrix that does not come from a file
    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    main_window.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinimizeButtonHint)
    ui = UIMainWindow(main_window)
    main_window.show()
    sys.exit(app.exec_())

