import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import os
import subprocess
import sys
from typing import List, Dict, Tuple, Any
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set Turkish locale for proper text display
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


class AnimeAnalyzer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df_anime = None
        self.df_expanded = None
        self.genre_summary = None
        self.top_genres = []
        self.analysis_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def load_and_clean_data(self) -> bool:
        """Load and clean the anime dataset"""
        try:
            logger.info("Loading dataset...")

            # Try different encodings and engines
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

            for encoding in encodings:
                try:
                    self.df_anime = pd.read_csv(self.file_path, sep=',', encoding=encoding)
                    logger.info(f"Dataset loaded successfully with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Failed with encoding {encoding}: {e}")
                    continue

            if self.df_anime is None:
                try:
                    self.df_anime = pd.read_csv(self.file_path, sep=',')
                    logger.info("Dataset loaded with default encoding")
                except Exception as e:
                    logger.error(f"Failed to load dataset: {e}")
                    return False

            logger.info(f"Dataset loaded successfully with {len(self.df_anime)} rows")

            # Basic data cleaning
            self.df_anime['rating'] = pd.to_numeric(self.df_anime['rating'], errors='coerce')

            # Check if essential columns exist
            essential_cols = ['rating', 'genre', 'name']
            missing_cols = [col for col in essential_cols if col not in self.df_anime.columns]

            if missing_cols:
                logger.error(f"Missing essential columns: {missing_cols}")
                return False

            # Remove rows with missing essential data
            initial_count = len(self.df_anime)
            self.df_anime = self.df_anime.dropna(subset=['rating', 'genre', 'name'])
            logger.info(f"Removed {initial_count - len(self.df_anime)} rows with missing data")

            # Clean and prepare genre list
            self.df_anime['genre_list'] = (
                self.df_anime['genre']
                .astype(str)
                .str.split(',')
                .apply(lambda x: [g.strip() for g in x if g.strip() and g.strip().lower() != 'nan'])
            )

            # Filter out rows with empty genre lists
            initial_count = len(self.df_anime)
            self.df_anime = self.df_anime[self.df_anime['genre_list'].map(len) > 0]
            logger.info(f"Removed {initial_count - len(self.df_anime)} rows with empty genre lists")
            logger.info(f"Final dataset has {len(self.df_anime)} valid rows")

            return True

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False

    def expand_genres(self):
        """Explode genres into separate rows"""
        try:
            self.df_expanded = (
                self.df_anime.drop('genre', axis=1, errors='ignore')
                .explode('genre_list')
                .rename(columns={'genre_list': 'genre'})
                .dropna(subset=['genre'])
            )
            logger.info("Genres expanded successfully")
        except Exception as e:
            logger.error(f"Error expanding genres: {e}")
            raise

    def analyze_genres(self, min_anime_count: int = 10):
        """Analyze genres and calculate statistics"""
        try:
            self.genre_summary = (
                self.df_expanded.groupby('genre')['rating']
                .agg(['mean', 'count', 'std'])
                .rename(columns={'mean': 'average_rating', 'count': 'anime_count', 'std': 'rating_std'})
            )

            # Filter and sort
            self.genre_summary = (
                self.genre_summary[self.genre_summary['anime_count'] >= min_anime_count]
                .sort_values(by='average_rating', ascending=False)
            )

            self.top_genres = self.genre_summary.head(10).index.tolist()
            logger.info(f"Found {len(self.genre_summary)} genres with at least {min_anime_count} anime")

        except Exception as e:
            logger.error(f"Error analyzing genres: {e}")
            raise

    def get_top_anime_for_genre(self, genre: str, top_n: int = 5) -> pd.DataFrame:
        """Get top anime for a specific genre"""
        try:
            genre_anime = self.df_anime[
                self.df_anime['genre_list'].apply(lambda x: genre in x)
            ].copy()

            if genre_anime.empty:
                return pd.DataFrame()

            genre_anime = genre_anime.sort_values('rating', ascending=False).head(top_n)

            # Select relevant columns that exist
            possible_cols = ['name', 'rating', 'episodes', 'type', 'members', 'score', 'popularity']
            available_cols = [col for col in possible_cols if col in genre_anime.columns]

            result = genre_anime[available_cols].copy()
            result = result.reset_index(drop=True)

            # Round numeric columns
            numeric_cols = result.select_dtypes(include=[np.number]).columns
            result[numeric_cols] = result[numeric_cols].round(2)

            return result

        except Exception as e:
            logger.error(f"Error getting top anime for {genre}: {e}")
            return pd.DataFrame()

    def analyze_side_genres(self, main_genre: str, min_count: int = 5) -> pd.DataFrame:
        """Analyze side genres that appear with the main genre"""
        try:
            main_genre_anime = self.df_anime[
                self.df_anime['genre_list'].apply(lambda x: main_genre in x)
            ].copy()

            if len(main_genre_anime) == 0:
                return pd.DataFrame()

            # Collect all side genres with their ratings
            side_genre_data = []
            for _, row in main_genre_anime.iterrows():
                for genre in row['genre_list']:
                    if genre != main_genre:
                        side_genre_data.append({
                            'genre': genre,
                            'rating': row['rating'],
                            'anime_name': row.get('name', 'Unknown')
                        })

            if not side_genre_data:
                return pd.DataFrame()

            # Create DataFrame and calculate statistics
            side_df = pd.DataFrame(side_genre_data)
            side_summary = (
                side_df.groupby('genre')
                .agg({
                    'rating': ['mean', 'count', 'std'],
                    'anime_name': lambda x: list(x)[:3]
                })
            )

            # Flatten column names
            side_summary.columns = ['average_rating', 'anime_count', 'rating_std', 'sample_anime']

            # Filter and sort
            side_summary = (
                side_summary[side_summary['anime_count'] >= min_count]
                .sort_values('average_rating', ascending=False)
                .head(10)
            )

            # Round numeric values
            side_summary['average_rating'] = side_summary['average_rating'].round(2)
            side_summary['rating_std'] = side_summary['rating_std'].round(2)

            return side_summary.reset_index()

        except Exception as e:
            logger.error(f"Error analyzing side genres for {main_genre}: {e}")
            return pd.DataFrame()

    def save_to_file(self, content: str, filename: str, subfolder: str = ""):
        """Save content to file"""
        try:
            if subfolder:
                os.makedirs(os.path.join(subfolder), exist_ok=True)
                filepath = os.path.join(subfolder, filename)
            else:
                filepath = filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"File saved: {filepath}")
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")

    def create_bar_chart(self, data: pd.DataFrame, title: str, filename: str,
                         x_label: str, y_label: str, x_col: str = 'genre', y_col: str = 'average_rating'):
        """Create and save bar chart with customizable column names"""
        try:
            plt.figure(figsize=(14, 8))

            if data.empty:
                plt.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=16)
                plt.title(title, fontsize=16, fontweight='bold')
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                plt.close()
                return

            # Check if required columns exist
            if x_col not in data.columns or y_col not in data.columns:
                logger.error(f"Required columns not found: {x_col} or {y_col}")
                plt.text(0.5, 0.5, 'Data format error', ha='center', va='center', fontsize=16)
                plt.title(title, fontsize=16, fontweight='bold')
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                plt.close()
                return

            bars = plt.bar(data[x_col], data[y_col],
                           color=sns.color_palette("husl", len(data)))

            plt.xlabel(x_label, fontsize=12)
            plt.ylabel(y_label, fontsize=12)
            plt.title(title, fontsize=16, fontweight='bold', pad=20)
            plt.xticks(rotation=45, ha='right')

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2., height + 0.02,
                         f'{height:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

        except Exception as e:
            logger.error(f"Error creating chart {filename}: {e}")

    def create_table_image(self, data: pd.DataFrame, title: str, filename: str):
        """Create and save table as image"""
        try:
            plt.figure(figsize=(16, 10))
            plt.axis('off')

            if data.empty:
                plt.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=16)
                plt.title(title, fontsize=16, fontweight='bold')
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                plt.close()
                return

            table = plt.table(cellText=data.values,
                              colLabels=data.columns,
                              cellLoc='center',
                              loc='center',
                              colColours=['#f0f0f0'] * len(data.columns))

            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 2)

            # Style header row
            for i in range(len(data.columns)):
                table[(0, i)].set_facecolor('#4F81BD')
                table[(0, i)].set_text_props(weight='bold', color='white')

            plt.title(title, fontsize=16, fontweight='bold', pad=20)
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

        except Exception as e:
            logger.error(f"Error creating table {filename}: {e}")

    def dataframe_to_markdown_table(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to Markdown table format"""
        if df.empty:
            return "*No data available*"

        # Create header
        headers = df.columns.tolist()
        header_line = "| " + " | ".join(headers) + " |"
        separator_line = "|" + "|".join(["---"] * len(headers)) + "|"

        # Create rows
        rows = []
        for _, row in df.iterrows():
            row_str = "| " + " | ".join(str(x) for x in row.values) + " |"
            rows.append(row_str)

        return "\n".join([header_line, separator_line] + rows)


def main():
    # Configuration
    DATA_PATH = './dataset/anime.csv'
    BASE_OUTPUT_DIR = './anime_analysis_output'
    MIN_ANIME_COUNT = 10
    TOP_N_GENRES = 5

    # Initialize analyzer
    analyzer = AnimeAnalyzer(DATA_PATH)

    # Create main output directory with timestamp
    main_output_dir = f"{BASE_OUTPUT_DIR}_{analyzer.analysis_time}"
    os.makedirs(main_output_dir, exist_ok=True)

    # Create subdirectories
    subdirs = {
        'charts': os.path.join(main_output_dir, 'charts'),
        'tables': os.path.join(main_output_dir, 'tables'),
        'text_reports': os.path.join(main_output_dir, 'text_reports'),
        'anime_lists': os.path.join(main_output_dir, 'anime_lists')
    }

    for subdir in subdirs.values():
        os.makedirs(subdir, exist_ok=True)

    # Load and clean data
    if not analyzer.load_and_clean_data():
        print("❌ Veri yüklenirken hata oluştu. Lütfen dosya yolunu kontrol edin.")
        sys.exit(1)

    # Expand genres and analyze
    try:
        analyzer.expand_genres()
        analyzer.analyze_genres(min_anime_count=MIN_ANIME_COUNT)
    except Exception as e:
        print(f"❌ Analiz sırasında hata oluştu: {e}")
        sys.exit(1)

    # Start building Markdown report
    md_report = []

    # Report header
    md_report.append("# 🎯 Anime Tür Analiz Raporu")
    md_report.append("")
    md_report.append(f"**Analiz Tarihi:** {analyzer.report_time}  ")
    md_report.append(f"**Toplam Anime Sayısı:** {len(analyzer.df_anime):,}  ")
    md_report.append(f"**Toplam Tür Sayısı:** {len(analyzer.genre_summary)}  ")
    md_report.append("")

    # Executive Summary
    md_report.append("## 📊 Executive Summary")
    md_report.append("")
    md_report.append(
        "Bu rapor, anime türlerinin popülerlik ve puan dağılımlarını analiz etmektedir. Analiz şu bileşenleri içerir:")
    md_report.append("- En yüksek puanlı türler")
    md_report.append("- Her tür için en popüler animeler")
    md_report.append("- Tür kombinasyonları analizi")
    md_report.append("- Yan tür önerileri")
    md_report.append("")

    # Top Genres Section
    md_report.append("## 🏆 En Yüksek Puanlı Türler")
    md_report.append("")

    top_genres_table = analyzer.genre_summary.head(TOP_N_GENRES).reset_index()
    top_genres_table['average_rating'] = top_genres_table['average_rating'].round(2)
    top_genres_display = top_genres_table[['genre', 'average_rating', 'anime_count']].copy()
    top_genres_display.columns = ['Tür', 'Ortalama Puan', 'Anime Sayısı']

    md_report.append(analyzer.dataframe_to_markdown_table(top_genres_display))
    md_report.append("")
    md_report.append(f"![Top Genres Chart](./charts/top_genres_chart.png)")
    md_report.append("")

    # Save top genres chart
    analyzer.create_bar_chart(
        top_genres_table,
        'En Yüksek Puanlı İlk 5 Tür',
        os.path.join(subdirs['charts'], 'top_genres_chart.png'),
        'Türler',
        'Ortalama Puan',
        'genre',
        'average_rating'
    )

    # Detailed Genre Analysis
    md_report.append("## 🎬 Detaylı Tür Analizleri")
    md_report.append("")

    for i, main_genre in enumerate(analyzer.top_genres[:TOP_N_GENRES], 1):
        md_report.append(f"### {i}. {main_genre}")
        md_report.append("")

        # Top Anime for this genre
        top_anime = analyzer.get_top_anime_for_genre(main_genre, top_n=5)
        if not top_anime.empty:
            md_report.append(f"#### 🎞️ {main_genre} Türündeki En İyi 5 Anime")
            md_report.append("")
            md_report.append(analyzer.dataframe_to_markdown_table(top_anime))
            md_report.append("")

            # Save anime list
            anime_text = tabulate(top_anime, headers='keys', tablefmt='grid', showindex=False, floatfmt=".2f")
            analyzer.save_to_file(anime_text, f'top_anime_{main_genre}.txt', subdirs['anime_lists'])

            # Save table image
            analyzer.create_table_image(
                top_anime,
                f'{main_genre} - En Popüler 5 Anime',
                os.path.join(subdirs['tables'], f'top_anime_{main_genre}.png')
            )

            md_report.append(f"![Top Anime for {main_genre}](./tables/top_anime_{main_genre}.png)")
            md_report.append("")

        # Side Genres Analysis
        side_genres = analyzer.analyze_side_genres(main_genre, min_count=3)
        if not side_genres.empty:
            md_report.append(f"#### 🌟 {main_genre} ile En İyi Kombinasyonlar")
            md_report.append("")

            side_display = side_genres[['genre', 'average_rating', 'anime_count']].copy()
            side_display.columns = ['Yan Tür', 'Ortalama Puan', 'Anime Sayısı']
            side_display['Ortalama Puan'] = side_display['Ortalama Puan'].round(2)

            md_report.append(analyzer.dataframe_to_markdown_table(side_display))
            md_report.append("")

            analyzer.create_bar_chart(
                side_genres,
                f'{main_genre} ile En Çok Sevilen Yan Türler',
                os.path.join(subdirs['charts'], f'side_genres_{main_genre}.png'),
                'Yan Türler',
                'Ortalama Puan',
                'genre',
                'average_rating'
            )

            md_report.append(f"![Side Genres for {main_genre}](./charts/side_genres_{main_genre}.png)")
            md_report.append("")

            # Sample Anime Recommendations
            md_report.append(f"#### 🎭 Örnek Anime Önerileri")
            md_report.append("")

            for _, side_row in side_genres.head(3).iterrows():
                side_genre = side_row['genre']
                md_report.append(f"**{main_genre} + {side_genre} kombinasyonu için öneriler:**  ")
                sample_anime = side_row['sample_anime'][:3]
                for anime in sample_anime:
                    md_report.append(f"- {anime}")
                md_report.append("")

        md_report.append("---")
        md_report.append("")

    # Statistics Section
    md_report.append("## 📈 İstatistiksel Özet")
    md_report.append("")

    stats_data = {
        'Metric': [
            'Toplam Anime',
            'Toplam Tür',
            'En Yüksek Puan',
            'En Düşük Puan',
            'Ortalama Puan',
            'Standart Sapma'
        ],
        'Value': [
            f"{len(analyzer.df_anime):,}",
            f"{len(analyzer.genre_summary)}",
            f"{analyzer.genre_summary['average_rating'].max():.2f}",
            f"{analyzer.genre_summary['average_rating'].min():.2f}",
            f"{analyzer.genre_summary['average_rating'].mean():.2f}",
            f"{analyzer.genre_summary['average_rating'].std():.2f}"
        ]
    }

    stats_df = pd.DataFrame(stats_data)
    md_report.append(analyzer.dataframe_to_markdown_table(stats_df))
    md_report.append("")

    # Methodology Section
    md_report.append("## 🔍 Metodoloji")
    md_report.append("")
    md_report.append("1. **Veri Temizleme:** Eksik ve geçersiz veriler kaldırıldı")
    md_report.append("2. **Tür Ayrıştırma:** Virgülle ayrılmış türler bireysel kayıtlara dönüştürüldü")
    md_report.append("3. **İstatistiksel Analiz:** Her tür için ortalama puan ve sayımlar hesaplandı")
    md_report.append("4. **Kombinasyon Analizi:** Türler arası ilişkiler incelendi")
    md_report.append("5. **Görselleştirme:** Grafikler ve tablolar oluşturuldu")
    md_report.append("")

    # Conclusion
    md_report.append("## 🎉 Sonuç")
    md_report.append("")
    md_report.append(
        "Bu analiz, anime türlerinin performansını ve birbirleriyle olan etkileşimlerini anlamak için kapsamlı bir bakış sunmaktadır. En yüksek puanlı türler ve bunların en iyi kombinasyonları, anime öneri sistemleri için değerli bilgiler sağlamaktadır.")
    md_report.append("")

    # Footer
    md_report.append("---")
    md_report.append("")
    md_report.append("*Bu rapor otomatik olarak oluşturulmuştur. Son güncelleme: {}*  ".format(analyzer.report_time))
    md_report.append("")
    md_report.append("### 📁 Dosya Yapısı")
    md_report.append("```")
    md_report.append(f"{main_output_dir}/")
    md_report.append("├── charts/                 # Grafikler (PNG)")
    md_report.append("├── tables/                 # Tablo görselleri (PNG)")
    md_report.append("├── text_reports/           # Metin raporları (TXT)")
    md_report.append("├── anime_lists/            # Anime listeleri (TXT)")
    md_report.append("└── comprehensive_report.md # Bu rapor")
    md_report.append("```")

    # Save Markdown report
    md_content = "\n".join(md_report)
    analyzer.save_to_file(md_content, 'comprehensive_report.md', main_output_dir)

    # Also save individual text files
    analyzer.save_to_file(tabulate(top_genres_display, headers='keys', tablefmt='grid'),
                          'top_genres.txt', subdirs['text_reports'])

    # Final output
    print(f"\n{'=' * 80}")
    print("✅ ANALİZ RAPORU TAMAMLANDI")
    print(f"{'=' * 80}")
    print(f"📁 Ana çıktı klasörü: {main_output_dir}")
    print(f"📄 Markdown Raporu: comprehensive_report.md")
    print(f"📊 Oluşturulan görseller: charts/ ve tables/ klasörlerinde")
    print("")

    # Open output folder
    try:
        if os.name == 'nt':
            os.startfile(os.path.abspath(main_output_dir))
            print("📂 Klasör otomatik olarak açılıyor...")
        elif os.name == 'posix':
            if sys.platform == 'darwin':
                subprocess.call(['open', main_output_dir])
            else:
                subprocess.call(['xdg-open', main_output_dir])
    except Exception as e:
        print(f"ℹ️ Klasör otomatik açılamadı: {e}")
        print(f"ℹ️ Lütfen manuel olarak açın: {os.path.abspath(main_output_dir)}")


if __name__ == "__main__":
    main()