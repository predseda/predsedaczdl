from PySide6 import QtCore, QtWidgets, QtGui

from downloader import Downloader

import sys


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.urlLabel = QtWidgets.QLabel("Odkaz:")
        self.url = QtWidgets.QLineEdit()
        self.url.setPlaceholderText("Odkaz videa")

        self.targetDirLabel = QtWidgets.QLabel("Adresář pro uložení:")
        self.targetDir = QtWidgets.QLineEdit()
        self.targetDir.setPlaceholderText("Adresář pro uložení stažených souborů")

        self.fileDialogButton = QtWidgets.QPushButton("Vybrat umístění")

        self.downloadButton = QtWidgets.QPushButton("Stáhnout")

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.urlLabel, 0, 0)
        self.layout.addWidget(self.url, 0, 1)
        self.layout.addWidget(self.targetDirLabel, 1, 0)
        self.layout.addWidget(self.targetDir, 1, 1)
        self.layout.addWidget(self.fileDialogButton, 1, 2)
        self.layout.addWidget(self.downloadButton, 2, 1)

        self.fileDialogButton.clicked.connect(self.selectDownloadDir)
        self.downloadButton.clicked.connect(self.downloadVideo)

    @QtCore.Slot()
    def selectDownloadDir(self):
        downloadDir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Vyberte adresář pro stažení souborů",
            QtCore.QDir.homePath(),
            QtWidgets.QFileDialog.ShowDirsOnly,
        )
        self.targetDir.setText(downloadDir)

    @QtCore.Slot()
    def downloadVideo(self):
        downloader = Downloader(self.url.text(), self.targetDir.text())
        downloader.download_video()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    main_window = MainWindow()
    main_window.resize(800, 600)
    main_window.show()

    sys.exit(app.exec())
