# AnimeGenreAnalyst 🎌

Anime dünyasının gizli kalmış tür sırlarını ortaya çıkaran profesyonel analiz aracı

## 📊 Proje Hakkında

Not: Çalışmış hali de eklenmiştir.

AnimeGenreAnalyst, anime türlerinin derinlemesine analizini yapan ve en iyi tür kombinasyonlarını keşfeden bir veri analizi projesidir. Bu araç sayesinde:

🏆 En yüksek puanlı türleri keşfedin
💫 Türler arası mükemmel kombinasyonları bulun
🎬 Her tür için en iyi anime önerilerini alın
📈 İstatistiksel olarak kanıtlanmış sonuçlar görün

Bu proje için kullanılan veri seti: [Anime Recommendations Database - Kaggle](https://www.kaggle.com/datasets/CooperUnion/anime-recommendations-database/data)

---

## 🚀 Özellikler

### Temel Özellikler

* Tür bazlı puan analizi
* Yan tür kombinasyon önerileri
* Görsel raporlama ve grafikler
* Otomatik Markdown rapor oluşturma
* Profesyonel veri görselleştirme

---

## 📦 Kurulum

```

# Gereksinimler

Python 3.8+ yüklü olmalıdır.

# Tüm bağımlılıkları yüklemek için

pip install -r requirements.txt

# Repoyu klonla

git clone [https://github.com/username/AnimeGenreAnalyst.git](https://github.com/username/AnimeGenreAnalyst.git)
cd AnimeGenreAnalyst

# Çalıştır

python main.py
```

---

## 🎯 Kullanım

```

# Otomatik analiz başlatma

from AnimeGenreAnalyst import analyze\_anime\_data

results = analyze\_anime\_data('./dataset/anime.csv')
print(results.generate\_report())

```

---

## 📑 Örnek Çıktı

🏆 **Top 3 Tür:**

1. Josei (8.45 ⭐)
2. Thriller (8.32 ⭐)
3. Mystery (8.28 ⭐)

💫 **En İyi Kombinasyonlar:**

* Josei + Drama (8.67 ⭐)
* Thriller + Mystery (8.53 ⭐)

📊 **Örnek Analiz Sonuçları**

| Tür      | Ortalama Puan | Anime Sayısı | Popülerlik |
| -------- | ------------- | ------------ | ---------- |
| Josei    | 8.45 ⭐        | 47           | Yüksek     |
| Thriller | 8.32 ⭐        | 156          | Çok Yüksek |
| Mystery  | 8.28 ⭐        | 289          | Yüksek     |

---

## 🎨 Görsel Özellikler

### Otomatik Oluşturulan Görseller

* Tür dağılım grafikleri
* Puan kıyaslama tabloları
* Kombinasyon heatmap'leri
* Trend analizleri

---

## 🔧 Teknoloji Stack'i

* **Python 3.8+**
* **Pandas** - Veri işleme
* **Matplotlib/Seaborn** - Görselleştirme
* **Tabulate** - Tablo oluşturma
* **NumPy** - Matematiksel işlemler

---

## 📁 Proje Yapısı

```
AnimeGenreAnalyst/
├── 📊 dataset/
│   └── anime.csv
├── 📝 results/
│   ├── comprehensive\_report.md
│   ├── charts/
│   └── tables/
├── ⚙️ requirements.txt
├── 📖 README.md
└── ▶️ main.py
```

---

## 🌟 Katkıda Bulunma

### Katkı İlkeleri

1. Fork'la ve clone'la
2. Feature branch oluştur (feature/amazingFeature)
3. Commit'le (Add amazing feature)
4. Push'la branch'e
5. Pull Request aç

---

## 📜 Lisans

MIT License - Anime severler için özgür yazılım ❤️

---

## 👨‍💻 Geliştirici

Ferivonus

---

*"Veriye bakış açını değiştir, anime dünyasını keşfet!"* 🎌

