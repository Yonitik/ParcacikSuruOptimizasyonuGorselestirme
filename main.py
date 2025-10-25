import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from pso_gui import PSOArayuz

if __name__ == '__main__':
    app = None
    try:
        app = QApplication(sys.argv)

        ex = PSOArayuz()
        ex.show()

        sys.exit(app.exec_())

    except Exception as e:
        if not app:
            app = QApplication(sys.argv)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(f"Uygulama başlatılırken kritik bir hata oluştu:\n\n{type(e).__name__}: {e}")

        detailed_traceback = traceback.format_exc()
        msg.setInformativeText("Detaylar için 'Show Details' butonuna basın.")
        msg.setWindowTitle("Başlatma Hatası")
        msg.setDetailedText(detailed_traceback)

        print("!!! UYGULAMA BAŞLATILAMADI !!!")
        print(detailed_traceback)

        msg.exec_()
        sys.exit(1)