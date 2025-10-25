import numpy as np


class Parcacik:
    def __init__(self, min_sinirlar, max_sinirlar):
        self.pozisyon = np.random.uniform(low=min_sinirlar, high=max_sinirlar, size=2)
        self.hiz = np.random.uniform(low=-1, high=1, size=2)
        self.gorunen_pozisyon = np.copy(self.pozisyon)
        self.en_iyi_pozisyon = np.copy(self.pozisyon)
        self.en_iyi_uygunluk_degeri = float('inf')

class PSO:

    def __init__(self, parcacik_sayisi, w, c1, c2, min_sinirlar, max_sinirlar, uygunluk_fonksiyonu):
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.min_sinirlar = np.array(min_sinirlar)
        self.max_sinirlar = np.array(max_sinirlar)
        self.uygunluk_fonksiyonu = uygunluk_fonksiyonu
        self.kuresel_en_iyi_pozisyon = np.zeros(2)
        self.kuresel_en_iyi_uygunluk_degeri = float('inf')
        self.suru = []
        self._initializasyon(parcacik_sayisi)

    def _initializasyon(self, parcacik_sayisi):
        for _ in range(parcacik_sayisi):
            parcacik = Parcacik(self.min_sinirlar, self.max_sinirlar)
            uygunluk = self.uygunluk_fonksiyonu(parcacik.pozisyon[0], parcacik.pozisyon[1])
            parcacik.en_iyi_uygunluk_degeri = uygunluk
            if uygunluk < self.kuresel_en_iyi_uygunluk_degeri:
                self.kuresel_en_iyi_uygunluk_degeri = uygunluk
                self.kuresel_en_iyi_pozisyon = np.copy(parcacik.pozisyon)
            self.suru.append(parcacik)

    def Adim(self):
        for parcacik in self.suru:
            r1, r2 = np.random.rand(2), np.random.rand(2)
            parcacik.hiz = (self.w * parcacik.hiz) + \
                           (self.c1 * r1 * (parcacik.en_iyi_pozisyon - parcacik.pozisyon)) + \
                           (self.c2 * r2 * (self.kuresel_en_iyi_pozisyon - parcacik.pozisyon))

            parcacik.pozisyon += parcacik.hiz
            parcacik.pozisyon = np.clip(parcacik.pozisyon, self.min_sinirlar, self.max_sinirlar)

            yeni_uygunluk = self.uygunluk_fonksiyonu(parcacik.pozisyon[0], parcacik.pozisyon[1])

            if yeni_uygunluk < parcacik.en_iyi_uygunluk_degeri:
                parcacik.en_iyi_uygunluk_degeri = yeni_uygunluk
                parcacik.en_iyi_pozisyon = np.copy(parcacik.pozisyon)

            if parcacik.en_iyi_uygunluk_degeri < self.kuresel_en_iyi_uygunluk_degeri:
                self.kuresel_en_iyi_uygunluk_degeri = parcacik.en_iyi_uygunluk_degeri
                self.kuresel_en_iyi_pozisyon = np.copy(parcacik.en_iyi_pozisyon)