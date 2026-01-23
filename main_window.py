from PySide6 import QtCore, QtWidgets, QtGui

from downloader import Downloader

import sys


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Predsedaczdl")

        self.urlLabel = QtWidgets.QLabel("Odkaz:")
        self.url = QtWidgets.QLineEdit()
        self.url.setPlaceholderText("Odkaz videa")

        self.targetDirLabel = QtWidgets.QLabel("Adresář pro uložení:")
        self.targetDir = QtWidgets.QLineEdit()
        self.targetDir.setPlaceholderText("Adresář pro uložení stažených souborů")

        self.fileDialogButton = QtWidgets.QPushButton("Vybrat adresář")

        self.downloadButton = QtWidgets.QPushButton("Stáhnout")

        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setVisible(False)

        self.statusLabel = QtWidgets.QLabel("")
        self.statusLabel.setVisible(False)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.urlLabel, 0, 0)
        self.layout.addWidget(self.url, 0, 1)
        self.layout.addWidget(self.targetDirLabel, 1, 0)
        self.layout.addWidget(self.targetDir, 1, 1)
        self.layout.addWidget(self.fileDialogButton, 1, 2)
        self.layout.addWidget(self.downloadButton, 2, 1)
        self.layout.addWidget(self.progressBar, 3, 0, 1, 3)
        self.layout.addWidget(self.statusLabel, 4, 0, 1, 3)

        self.fileDialogButton.clicked.connect(self.selectDownloadDir)
        self.downloadButton.clicked.connect(self.downloadVideo)

        self.download_thread = None

    # Designed by Anthropic Claude AI
    def closeEvent(self, event: QtGui.QCloseEvent):
        """Handle window close event and clean up threads properly"""
        if (
            self.downloader
            and hasattr(self.downloader, "download_thread")
            and self.downloader.download_thread
        ):
            if self.downloader.download_thread.isRunning():
                # Ask user if they want to cancel the download
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Probíhá stahování",
                    "Stahování stále probíhá. Chcete ho zrušit a zavřít aplikaci?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No,
                )

                if reply == QtWidgets.QMessageBox.Yes:
                    # Force quit the thread and wait for it to finish
                    self.downloader.download_thread.quit()
                    self.downloader.download_thread.wait(3000)  # Wait up to 3 seconds

                    if self.downloader.download_thread.isRunning():
                        # If still running after 3 seconds, terminate it
                        self.downloader.download_thread.terminate()
                        self.downloader.download_thread.wait()

                    event.accept()
                else:
                    event.ignore()
                    return

        event.accept()

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
        if not self.url.text().strip():
            QtWidgets.QMessageBox.warning(
                self, "Velký špatný", "Zadejte odkaz na video."
            )
            return

        if not self.targetDir.text().strip():
            QtWidgets.QMessageBox.warning(
                self, "Velký špatný", "Vyberte adresář pro uložení."
            )
            return

        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        self.statusLabel.setVisible(True)
        self.statusLabel.setText("Připravuji stahování...")

        self.downloadButton.setEnabled(False)
        self.downloadButton.setText("Stahuji...")

        self.download_thread = Downloader(
            self.url.text().strip(), self.targetDir.text().strip()
        )

        self.download_thread.progress_update.connect(self.updateProgress)
        self.download_thread.status_update.connect(self.updateStatus)
        self.download_thread.download_finished.connect(self.downloadFinished)
        self.download_thread.download_error.connect(self.downloadError)

        self.download_thread.start_download()

    @QtCore.Slot(int, str)
    def updateProgress(self, percentage, speed_str):
        self.progressBar.setValue(percentage)
        if speed_str:
            self.statusLabel.setText(f"Stahuji... {percentage}% ({speed_str})")
        else:
            self.statusLabel.setText(f"Stahuji... {percentage}%")

    @QtCore.Slot(str)
    def updateStatus(self, status):
        self.statusLabel.setText(status)

    @QtCore.Slot(str)
    def downloadFinished(self, filename):
        self.progressBar.setValue(100)
        self.statusLabel.setText(f"Stahování dokončeno: {filename}")
        self.downloadButton.setEnabled(True)
        self.downloadButton.setText("Stáhnout")

        # Hide progress bar after 3 seconds
        QtCore.QTimer.singleShot(3000, lambda: self.progressBar.setVisible(False))
        QtCore.QTimer.singleShot(3000, lambda: self.statusLabel.setVisible(False))

        QtWidgets.QMessageBox.information(self, "Hotové", "Stahování dokončeno")

    @QtCore.Slot(str)
    def downloadError(self, err):
        self.progressBar.setVisible(False)
        self.statusLabel.setText(f"Velký špatný: {err}")
        self.downloadButton.setEnabled(True)
        self.downloadButton.setText("Stáhnout")

        QtWidgets.QMessageBox.critical(self, "Velký špatný", err)

        # Hide status after 5 seconds
        QtCore.QTimer.singleShot(5000, lambda: self.statusLabel.setVisible(False))


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    main_window = MainWindow()
    main_window.resize(800, 600)
    main_window.show()

    sys.exit(app.exec())
