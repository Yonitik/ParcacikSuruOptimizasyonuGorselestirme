
import numpy as np
import traceback
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QDoubleSpinBox, QPushButton, QGroupBox, QSpinBox,
    QMessageBox, QSlider
)
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.cm as cm
from pso_core import Parcacik, PSO

def sphere_function(x, y):
    return x ** 2 + y ** 2

class PSOArayuz(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D PSO Görselleştirme")
        self.setGeometry(100, 100, 1000, 950)
        self.pso_optimizer = None
        self.timer = QTimer()
        self.timer.setInterval(20)
        self.timer.timeout.connect(self._guncelleme_adimi)
        self.iterasyon_sayaci = 0
        self.gorunen_gbest_pos = np.zeros(2)
        self.gecikme_sayaci = 0
        self.X_grid = None
        self.Y_grid = None
        self.Z_grid = None
        self.init_ui()
        self._arkaplani_hazirla_ve_ciz()

    def init_ui(self):
        ana_layout = QHBoxLayout()
        kontrol_paneli = self._create_kontrol_paneli()
        ana_layout.addWidget(kontrol_paneli)
        gorsel_alan = self._create_gorsellestirme_alani()
        ana_layout.addWidget(gorsel_alan, stretch=1)
        self.setLayout(ana_layout)

    def _create_int_slider_spinbox(self, layout, row, label_text, min_val, max_val, default_val):
        layout.addWidget(QLabel(label_text), row, 0)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)

        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)

        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)

        spinbox.setValue(default_val)

        layout.addWidget(slider, row, 1)
        layout.addWidget(spinbox, row, 2)

        return slider, spinbox

    def _create_float_slider_spinbox(self, layout, row, label_text, min_val, max_val, default_val, decimals=2):
        layout.addWidget(QLabel(label_text), row, 0)

        multiplier = 10 ** decimals

        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(min_val * multiplier), int(max_val * multiplier))

        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setDecimals(decimals)
        spinbox.setSingleStep(1 / multiplier)

        slider.valueChanged.connect(lambda value: spinbox.setValue(value / multiplier))
        spinbox.valueChanged.connect(lambda value: slider.setValue(int(value * multiplier)))

        spinbox.setValue(default_val)

        layout.addWidget(slider, row, 1)
        layout.addWidget(spinbox, row, 2)

        return slider, spinbox

    def _create_kontrol_paneli(self):
        panel_widget = QWidget()
        panel_layout = QVBoxLayout()
        panel_widget.setFixedWidth(380)

        param_group = QGroupBox("PSO Parametreleri")
        param_layout = QGridLayout()
        param_layout.setSpacing(10)

        self.aciklama_stili = "font-size: 9pt; color: #333; font-style: italic;"
        row = 0

        (self.slider_parcacik, self.spin_parcacik_sayisi) = self._create_int_slider_spinbox(
            param_layout, row, "Parçacık Sayısı:", 10, 500, 50)
        row += 1
        self._add_aciklama(param_layout, row, "Sürüdeki toplam çözüm adayı (parçacık) sayısı.")
        row += 1

        (self.slider_w, self.spin_w) = self._create_float_slider_spinbox(
            param_layout, row, "İnertya (w):", 0.1, 1.0, 0.729, 3)
        row += 1
        self._add_aciklama(param_layout, row, "Parçacığın mevcut hızını (momentumunu) koruma oranı.")
        row += 1

        (self.slider_c1, self.spin_c1) = self._create_float_slider_spinbox(
            param_layout, row, "Bilişsel (c1):", 0.1, 3.0, 1.494, 3)
        row += 1
        self._add_aciklama(param_layout, row, "Parçacığın 'kendi' en iyisine (pbest) güveni.")
        row += 1

        (self.slider_c2, self.spin_c2) = self._create_float_slider_spinbox(
            param_layout, row, "Sosyal (c2):", 0.1, 3.0, 1.494, 3)
        row += 1
        self._add_aciklama(param_layout, row, "Parçacığın 'sürünün' en iyisine (gbest) güveni.")
        row += 1

        (self.slider_calisma_alani, self.spin_calisma_alani) = self._create_float_slider_spinbox(
            param_layout, row, "Çalışma Alanı (±):", 1.0, 100.0, 5.0, 1)
        self.spin_calisma_alani.valueChanged.connect(self._sifirla)
        row += 1
        self._add_aciklama(param_layout, row, "Optimizasyonun yapılacağı kare alan (Örn: 5 = -5 ila +5).")
        row += 1

        (self.slider_opaklik, self.spin_opaklik) = self._create_float_slider_spinbox(
            param_layout, row, "Arka Plan Opaklığı:", 0.1, 1.0, 0.7, 2)
        self.spin_opaklik.valueChanged.connect(self._sifirla)
        row += 1
        self._add_aciklama(param_layout, row, "Grafik arka planının şeffaflığı.")
        row += 1

        (self.slider_gecikme, self.spin_gecikme) = self._create_int_slider_spinbox(
            param_layout, row, "İterasyon Gecikmesi:", 1, 50, 1)
        row += 1
        self._add_aciklama(param_layout, row,
                           "PSO mantığının kaç karede bir çalışacağını belirler. (1 = en hızlı).")
        row += 1

        param_group.setLayout(param_layout)
        panel_layout.addWidget(param_group)

        buton_layout = QHBoxLayout()
        self.btn_baslat = QPushButton("Başlat")
        self.btn_baslat.clicked.connect(self._baslat)
        self.btn_durdur = QPushButton("Durdur")
        self.btn_durdur.setEnabled(False)
        self.btn_durdur.clicked.connect(self._durdur)
        self.btn_sifirla = QPushButton("Sıfırla")
        self.btn_sifirla.clicked.connect(self._sifirla)

        buton_layout.addWidget(self.btn_baslat)
        buton_layout.addWidget(self.btn_durdur)
        buton_layout.addWidget(self.btn_sifirla)
        panel_layout.addLayout(buton_layout)

        result_group = QGroupBox("Sonuçlar")
        result_layout = QGridLayout()
        self.lbl_iterasyon = self._add_label_and_widget(result_layout, "İterasyon:", QLabel("0"), 0, is_label=True)
        self.lbl_gbest_val = self._add_label_and_widget(result_layout, "En İyi Değer:", QLabel("N/A"), 1, is_label=True)
        self.lbl_gbest_pos = self._add_label_and_widget(result_layout, "En İyi Konum:", QLabel("N/A"), 2, is_label=True)
        self.lbl_basari_yuzdesi = self._add_label_and_widget(result_layout, "Başarı Yüzdesi:", QLabel("0.0 %"), 3,
                                                             is_label=True)

        result_group.setLayout(result_layout)
        panel_layout.addWidget(result_group)

        panel_layout.addStretch()
        panel_widget.setLayout(panel_layout)
        return panel_widget

    def _add_aciklama(self, layout, row, text):
        desc_label = QLabel(text)
        desc_label.setStyleSheet(self.aciklama_stili)
        desc_label.setWordWrap(True)
        desc_label.setTextFormat(Qt.RichText)
        layout.addWidget(desc_label, row, 0, 1, 3)

    def _add_label_and_widget(self, layout, text, widget, row, is_label=False):
        layout.addWidget(QLabel(text), row, 0)
        if is_label:
            widget.setAlignment(Qt.AlignRight)
        layout.addWidget(widget, row, 1, 1, 2)
        return widget

    def _create_gorsellestirme_alani(self):
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        return self.canvas

    def _arkaplani_hazirla_ve_ciz(self):
        self.ax.clear()

        alan = self.spin_calisma_alani.value()
        min_s = -alan
        max_s = alan
        opaklik = self.spin_opaklik.value()

        x = np.linspace(min_s, max_s, 100)
        y = np.linspace(min_s, max_s, 100)
        self.X_grid, self.Y_grid = np.meshgrid(x, y)

        func = sphere_function

        self.Z_grid = func(self.X_grid, self.Y_grid)

        self.ax.contourf(self.X_grid, self.Y_grid, self.Z_grid, levels=50,
                         cmap=cm.viridis, zorder=1, alpha=opaklik)

        self.ax.set_xlim(min_s, max_s)
        self.ax.set_ylim(min_s, max_s)
        self.ax.set_aspect('equal')

        self.scatter_gbest, = self.ax.plot([], [], 'r*', markersize=12,
                                           label="gbest", zorder=10)

        self.scatter_parcaciklar = self.ax.scatter([], [], s=20,
                                                   edgecolors='k', facecolors='w',
                                                   alpha=0.8, label="Parçacıklar",
                                                   zorder=11)

        self.ax.legend(loc="upper right")
        self.canvas.draw()

    def _baslat(self):
        if self.pso_optimizer is None:
            try:
                parcacik_sayisi = self.spin_parcacik_sayisi.value()
                w = self.spin_w.value()
                c1 = self.spin_c1.value()
                c2 = self.spin_c2.value()
                alan = self.spin_calisma_alani.value()
                min_s = -alan
                max_s = alan
                min_sinirlar = [min_s, min_s]
                max_sinirlar = [max_s, max_s]
                func = sphere_function

                self.pso_optimizer = PSO(parcacik_sayisi, w, c1, c2, min_sinirlar, max_sinirlar, func)
                self.iterasyon_sayaci = 0
                self.gecikme_sayaci = 0
                self.gorunen_gbest_pos = np.copy(self.pso_optimizer.kuresel_en_iyi_pozisyon)

            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Başlatma hatası: {e}\n\n{traceback.format_exc()}")
                return

        self.timer.start()
        self.btn_baslat.setEnabled(False)
        self.btn_durdur.setEnabled(True)

    def _durdur(self):
        self.timer.stop()
        self.btn_baslat.setEnabled(True)
        self.btn_durdur.setEnabled(False)

    def _sifirla(self):
        self._durdur()
        self.pso_optimizer = None
        self.iterasyon_sayaci = 0
        self.gorunen_gbest_pos = np.zeros(2)

        self._arkaplani_hazirla_ve_ciz()

        self.lbl_iterasyon.setText("0")
        self.lbl_gbest_val.setText("N/A")
        self.lbl_gbest_pos.setText("N/A")
        self.lbl_basari_yuzdesi.setText("0.0 %")

    def _guncelleme_adimi(self):
        if self.pso_optimizer is None:
            return

        try:
            self.gecikme_sayaci += 1
            iterasyon_gecikmesi = self.spin_gecikme.value()

            if self.gecikme_sayaci >= iterasyon_gecikmesi:
                self.gecikme_sayaci = 0
                self.pso_optimizer.Adim()
                self.iterasyon_sayaci += 1

                gbest_val = self.pso_optimizer.kuresel_en_iyi_uygunluk_degeri
                gbest_pos = self.pso_optimizer.kuresel_en_iyi_pozisyon

                basarili_parcacik_sayisi = 0
                parcacik_sayisi_toplam = len(self.pso_optimizer.suru)

                if parcacik_sayisi_toplam > 0:
                    TOLERANS = 0.01
                    for parcacik in self.pso_optimizer.suru:
                        mevcut_uygunluk = self.pso_optimizer.uygunluk_fonksiyonu(
                            parcacik.pozisyon[0], parcacik.pozisyon[1]
                        )
                        if mevcut_uygunluk <= (gbest_val + TOLERANS):
                            basarili_parcacik_sayisi += 1
                    basari_yuzdesi = (basarili_parcacik_sayisi / parcacik_sayisi_toplam) * 100
                else:
                    basari_yuzdesi = 0.0

                self.lbl_iterasyon.setText(str(self.iterasyon_sayaci))
                self.lbl_gbest_val.setText(f"{gbest_val:.6f}")
                self.lbl_gbest_pos.setText(f"({gbest_pos[0]:.3f}, {gbest_pos[1]:.3f})")
                self.lbl_basari_yuzdesi.setText(f"{basari_yuzdesi:.1f} %")

            TEMEL_YUMUSATMA = 0.25

            if iterasyon_gecikmesi > 0:
                YUMUSATMA = TEMEL_YUMUSATMA / iterasyon_gecikmesi
            else:
                YUMUSATMA = TEMEL_YUMUSATMA

            tum_gorunen_pozisyonlar = []

            for parcacik in self.pso_optimizer.suru:
                parcacik.gorunen_pozisyon = parcacik.gorunen_pozisyon + \
                                            (parcacik.pozisyon - parcacik.gorunen_pozisyon) * YUMUSATMA
                tum_gorunen_pozisyonlar.append(parcacik.gorunen_pozisyon)

            gbest_hedef = self.pso_optimizer.kuresel_en_iyi_pozisyon
            self.gorunen_gbest_pos = self.gorunen_gbest_pos + \
                                     (gbest_hedef - self.gorunen_gbest_pos) * YUMUSATMA

            pozisyonlar_dizisi = np.array(tum_gorunen_pozisyonlar)
            self.scatter_parcaciklar.set_offsets(pozisyonlar_dizisi)
            self.scatter_gbest.set_data([self.gorunen_gbest_pos[0]], [self.gorunen_gbest_pos[1]])

            self.canvas.draw_idle()

        except Exception as e:
            self._durdur()
            QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {e}\n\n{traceback.format_exc()}")