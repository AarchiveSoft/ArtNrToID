import os
import sqlite3
import sys
from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit,
    QMessageBox, QProgressBar, QDialog, QCheckBox, QPlainTextEdit, QComboBox, QLineEdit, QFrame
)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Load credentials
email = "feigelluck@gmail.com"
password = "Graphicart#1"


def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    else:
        return os.path.join(os.path.dirname(__file__), relative_path)


DB_PATH = resource_path("GambioIDs.db")


def setup_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS gambioIDs (
            gambioID INTEGER PRIMARY KEY,
            bezeichnung TEXT,
            artNr TEXT
            )
            """
        )
        conn.commit()


class GUI(QWidget):
    def __init__(self, scrape):
        super().__init__()
        setup_db()
        self.setWindowTitle("Gambio ID Konverter")
        self.setGeometry(100, 100, 782, 600)
        self.scraper = scrape
        self.include_duplicates = False
        self.category_data = {
            "Kamerasysteme + Objektive": {
                "Nikon": {"Nikon Z": {"initials": "NIVOA"}, "Nikon DSLR": {"initials": "NIVBA"}},
                "Sony" : {"Sony E-Mount Kameras": {"initials": "SOILCE"}, "Sony Video Kameras": {"initials": "SOILME"}}
            }
        }
        self.brand_data = {
            "Marken": {
                "Nikon": {"NIVOA", "NIJMA", "NIVBA", "NIJAA"},
                "Sony" : {"SOILCE", "SOSEL", "SOLA", "SOILME", "SOZV", "SODSC"}
            }
        }
        self.main_icon_path = resource_path('main_icon.ico')
        self.loading_icon_path = resource_path('loading_icon.ico')
        self.setWindowIcon(QIcon(self.main_icon_path))
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        rescrape_button = QPushButton("Datenbank aktualisieren", self)
        rescrape_button.setStyleSheet("QPushButton { padding: 7px; }")
        rescrape_button.clicked.connect(self.open_progress_window)
        main_layout.addWidget(rescrape_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.last_updated_label = QLabel(self)
        self.last_updated_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.last_updated_label.setStyleSheet("QLabel { border-radius: 5px; padding: 5px; }")
        main_layout.addWidget(self.last_updated_label)

        self.refresh_last_updated_label()

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tabs.addTab(self.create_liste_tab(), "Liste")
        self.tabs.addTab(self.create_kategorie_tab(), "Kategorie mit Ausnahmen")
        self.tabs.addTab(self.create_marke_tab(), "Marke mit Ausnahmen")
        self.tabs.addTab(self.create_nikon_ohne_occ_tab(), "Nikon ohne OCC, mit Ausnahmen")
        self.tabs.addTab(self.create_sony_ohne_occ_tab(), "Sony ohne OCC, mit Ausnahmen")

        convert_button = QPushButton("Konvertieren", self)
        convert_button.clicked.connect(self.convert_articles)
        main_layout.addWidget(convert_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.result_textbox = QTextEdit(self)
        self.result_textbox.setReadOnly(True)
        main_layout.addWidget(self.result_textbox)

        self.missing_numbers_button = QPushButton("Fehlende Nummern anzeigen", self)
        self.missing_numbers_button.clicked.connect(self.show_missing_numbers)
        self.missing_numbers_button.setVisible(False)
        main_layout.addWidget(self.missing_numbers_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        output_layout = QHBoxLayout()
        format_button = QPushButton("Format ändern", self)
        format_button.clicked.connect(self.change_format)
        output_layout.addWidget(format_button)
        copy_button = QPushButton("In Zwischenablage kopieren", self)
        copy_button.clicked.connect(self.copy_to_clipboard)
        output_layout.addWidget(copy_button)
        main_layout.addLayout(output_layout)

        self.include_duplicates_checkbox = QCheckBox("Doppelte Artikelnummern einschliessen", self)
        self.include_duplicates_checkbox.stateChanged.connect(self.toggle_include_duplicates)
        main_layout.addWidget(self.include_duplicates_checkbox, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(main_layout)
        self.tabs.currentChanged.connect(self.reset_output_on_tab_change)

    def toggle_include_duplicates(self):
        self.include_duplicates = self.include_duplicates_checkbox.isChecked()

    def refresh_last_updated_label(self):
        db_path = DB_PATH

        if not os.path.exists(db_path):
            self.last_updated_label.setText("Datenbank wurde noch nicht erstellt.")
            return

        try:
            mod_time = os.path.getmtime(db_path)
            readable = datetime.fromtimestamp(mod_time).strftime("%d.%m.%Y, %H:%M")
            self.last_updated_label.setText(f"Datenbank zuletzt aktualisiert: <b>{readable}</b>")
        except Exception as e:
            self.last_updated_label.setText("Letztes Update: unbekannt")
            print(f"[Fehler beim Lesen des Datums] {e}")

    def paste_from_clipboard(self):
        """Paste content from clipboard into the 'Liste' input."""
        clipboard = QApplication.clipboard()
        self.liste_input.setPlainText(clipboard.text())

    def update_subcategories(self):
        selected_brand = self.marken_combobox.currentText()
        self.kategorie_combobox.clear()
        if selected_brand in self.category_data["Kamerasysteme + Objektive"]:
            self.kategorie_combobox.addItems(self.category_data["Kamerasysteme + Objektive"][selected_brand].keys())

    def create_liste_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.liste_input = QPlainTextEdit(self)
        self.liste_input.setPlaceholderText("Artikelnummern einfügen: (eine pro Zeile).")
        layout.addWidget(self.liste_input)

        paste_button = QPushButton("Aus Zwischenablage einfügen", self)
        paste_button.clicked.connect(self.paste_from_clipboard)
        layout.addWidget(paste_button)

        tab.setLayout(layout)
        return tab

    def create_kategorie_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.marken_combobox = QComboBox(self)
        self.marken_combobox.addItems(self.category_data["Kamerasysteme + Objektive"].keys())
        layout.addWidget(QLabel("Marke"))
        layout.addWidget(self.marken_combobox)

        self.kategorie_combobox = QComboBox(self)
        layout.addWidget(QLabel("Kategorie"))
        layout.addWidget(self.kategorie_combobox)

        self.update_subcategories()
        self.marken_combobox.currentTextChanged.connect(self.update_subcategories)

        self.exclude_input = QLineEdit(self)
        self.exclude_input.setPlaceholderText("Artikelnummern (getrennt mit Kommas)")
        layout.addWidget(QLabel("<b>Ausschliessen:</b>"))
        layout.addWidget(self.exclude_input)

        tab.setLayout(layout)
        return tab

    def create_marke_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.marken_only_combobox = QComboBox(self)
        self.marken_only_combobox.addItems(self.brand_data["Marken"].keys())
        layout.addWidget(QLabel("Marke"))
        layout.addWidget(self.marken_only_combobox)

        self.marken_exclude_input = QLineEdit(self)
        self.marken_exclude_input.setPlaceholderText("Artikelnummern (getrennt mit Kommas)")
        layout.addWidget(QLabel("<b>Ausschliessen:</b>"))
        layout.addWidget(self.marken_exclude_input)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def create_nikon_ohne_occ_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        nikon_frame = QFrame()
        nikon_frame_layout = QVBoxLayout()
        nikon_frame.setStyleSheet("""
            QFrame {
                background-color: #FFE100;
                color: #000000;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 76))
        nikon_frame.setGraphicsEffect(shadow)

        nikon_frame.setLayout(nikon_frame_layout)
        title_label_1 = QLabel("<b>Alle 'NI%' (Nikon) Artikel</b>")
        title_label_2 = QLabel("mit Ausnahme von 'NIOCC%' (Nikon Occasionen) und ausgeschlossene Artikeln")
        title_label_1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        nikon_frame_layout.addWidget(title_label_1)
        nikon_frame_layout.addWidget(title_label_2)
        layout.addWidget(nikon_frame)

        layout.addStretch()
        self.marken_exclude_input = QLineEdit(self)
        self.marken_exclude_input.setPlaceholderText("Artikelnummern (getrennt mit Kommas)")
        layout.addWidget(QLabel("<b>Ausschliessen:</b>"))
        layout.addWidget(self.marken_exclude_input)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_sony_ohne_occ_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        sony_frame = QFrame()
        sony_frame_layout = QVBoxLayout()
        sony_frame.setStyleSheet("""
            QFrame {
                background-color: #dc9018;
                color: #000000;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 76))
        sony_frame.setGraphicsEffect(shadow)

        sony_frame.setLayout(sony_frame_layout)
        title_label_1 = QLabel("<b>Alle 'SO%' (Sony) Artikel</b>")
        title_label_2 = QLabel("mit Ausnahme von 'OCCSO%' (Sony Occasionen) und ausgeschlossene Artikeln")
        title_label_1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sony_frame_layout.addWidget(title_label_1)
        sony_frame_layout.addWidget(title_label_2)
        layout.addWidget(sony_frame)

        layout.addStretch()
        self.marken_exclude_input = QLineEdit(self)
        self.marken_exclude_input.setPlaceholderText("Artikelnummern (getrennt mit Kommas)")
        layout.addWidget(QLabel("<b>Ausschliessen:</b>"))
        layout.addWidget(self.marken_exclude_input)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def convert_articles(self):
        try:
            self.result_textbox.clear()
            if hasattr(self, 'status_label'):
                self.status_label.setText("")

            active_tab_index = self.tabs.currentIndex()

            if active_tab_index == 0:
                if input_data := self.liste_input.toPlainText().splitlines():
                    self.query_database(input_data)
                else:
                    QMessageBox.warning(self, "Warnung", "Bitte geben Sie Artikelnummern ein.")

            elif active_tab_index == 1:
                selected_brand = self.marken_combobox.currentText()
                selected_category = self.kategorie_combobox.currentText()
                if not selected_brand or not selected_category:
                    QMessageBox.warning(self, "Warnung", "Bitte wählen Sie eine Marke und Kategorie aus.")
                    return
                initials = self.category_data["Kamerasysteme + Objektive"][selected_brand][selected_category]["initials"]
                excluded_articles = [art.strip() for art in self.exclude_input.text().split(",") if art.strip()]
                self.query_database_with_exclusions(initials, excluded_articles)

            elif active_tab_index == 2:
                selected_brand = self.marken_only_combobox.currentText()
                if not selected_brand:
                    QMessageBox.warning(self, "Warnung", "Bitte wähle eine Marke aus.")
                    return
                initials_list = list(self.brand_data["Marken"][selected_brand])
                excluded_articles = [art.strip() for art in self.marken_exclude_input.text().split(",") if art.strip()]
                self.query_database_brands_with_exclusions(initials_list, excluded_articles)

            elif active_tab_index == 3:
                excluded_articles = [art.strip() for art in self.marken_exclude_input.text().split(",") if art.strip()]
                self.query_database_all_nikon_with_exclusions(excluded_articles)

            elif active_tab_index == 4:
                excluded_articles = [art.strip() for art in self.marken_exclude_input.text().split(",") if art.strip()]
                self.query_database_all_sony_with_exclusions(excluded_articles)

        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def query_database(self, article_numbers):
        filtered_numbers = list({num.strip() for num in article_numbers if num.strip()})
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            query = """
                SELECT {} gambioID, artNr
                FROM gambioIDs
                WHERE artNr IN ({})
            """.format("" if self.include_duplicates else "DISTINCT", ",".join("?" for _ in filtered_numbers))
            c.execute(query, filtered_numbers)
            results = c.fetchall()

            found_art_numbers = [row[1] for row in results]
            missing_numbers = [num for num in filtered_numbers if num not in found_art_numbers]

            if self.include_duplicates:
                values = [str(row[0]) for row in results]
            else:
                unique_results = {}
                for gambio_id, art_nr in results:
                    if art_nr not in unique_results:
                        unique_results[art_nr] = str(gambio_id)
                values = list(unique_results.values())

            expected_count = len(filtered_numbers)
            output_count = len(values)

            self.update_output_box(
                "\n".join(values),
                expected_count,
                output_count,
                missing_numbers,
                excluded_count=0,
                raw_results=results
            )

    def query_database_with_exclusions(self, initials, excluded_articles):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            query = f"""
                SELECT {"DISTINCT" if not self.include_duplicates else ""} gambioID, artNr
                FROM gambioIDs
                WHERE artNr LIKE ?
            """
            parameters = [f"{initials}%"]

            if excluded_articles:
                placeholders = ", ".join("?" for _ in excluded_articles)
                query += f" AND artNr NOT IN ({placeholders})"
                parameters.extend(excluded_articles)

            c.execute(query, parameters)
            results = c.fetchall()

            # Fetch all possible numbers for comparison
            c.execute("SELECT DISTINCT artNr FROM gambioIDs WHERE artNr LIKE ?", [f"{initials}%"])
            all_possible_numbers = [row[0] for row in c.fetchall()]
            found_art_numbers = [row[1] for row in results]
            missing_numbers = [num for num in all_possible_numbers if num not in found_art_numbers]

            actually_excluded = [art for art in excluded_articles if art in all_possible_numbers]

            if self.include_duplicates:
                values = [str(row[0]) for row in results]
            else:
                unique_results = {}
                for gambio_id, art_nr in results:
                    if art_nr not in unique_results:
                        unique_results[art_nr] = str(gambio_id)
                values = list(unique_results.values())

            expected_count = len(all_possible_numbers) - len(actually_excluded)
            output_count = len(values)

            self.update_output_box(
                "\n".join(values),
                expected_count,
                output_count,
                missing_numbers,
                excluded_count=len(actually_excluded),
                raw_results=results
            )

    def query_database_brands_with_exclusions(self, initials_list, excluded_articles):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()

            like_clauses = " OR ".join(["artNr LIKE ?"] * len(initials_list))
            query = f"""
                SELECT {"DISTINCT" if not self.include_duplicates else ""} gambioID, artNr
                FROM gambioIDs
                WHERE ({like_clauses})
            """
            parameters = [f"{initial}%" for initial in initials_list]

            if excluded_articles:
                placeholders = ", ".join("?" for _ in excluded_articles)
                query += f" AND artNr NOT IN ({placeholders})"
                parameters.extend(excluded_articles)

            c.execute(query, parameters)
            results = c.fetchall()

            # All possible article numbers
            all_possible_numbers_query = f"""
                SELECT DISTINCT artNr
                FROM gambioIDs
                WHERE ({like_clauses})
            """
            c.execute(all_possible_numbers_query, [f"{initial}%" for initial in initials_list])
            all_possible_numbers = [row[0] for row in c.fetchall()]

            found_art_numbers = [row[1] for row in results]
            actually_excluded = [art for art in excluded_articles if art in all_possible_numbers]
            missing_numbers = [
                num for num in all_possible_numbers
                if num not in found_art_numbers and num not in actually_excluded
            ]

            if self.include_duplicates:
                values = [str(row[0]) for row in results]
            else:
                unique_results = {}
                for gambio_id, art_nr in results:
                    if art_nr not in unique_results:
                        unique_results[art_nr] = str(gambio_id)
                values = list(unique_results.values())

            expected_count = len(all_possible_numbers) - len(actually_excluded)
            output_count = len(values)

            self.update_output_box(
                "\n".join(values),
                expected_count,
                output_count,
                missing_numbers,
                excluded_count=len(actually_excluded),
                raw_results=results
            )

    def query_database_all_nikon_with_exclusions(self, excluded_articles):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            query = f"""
                SELECT {"DISTINCT" if not self.include_duplicates else ""} gambioID, artNr
                FROM gambioIDs
                WHERE artNr LIKE 'NI%' AND artNr NOT LIKE 'NIOCC%'
            """
            parameters = []

            if excluded_articles:
                placeholders = ", ".join("?" for _ in excluded_articles)
                query += f" AND artNr NOT IN ({placeholders})"
                parameters.extend(excluded_articles)

            c.execute(query, parameters)
            results = c.fetchall()

            c.execute("SELECT DISTINCT artNr FROM gambioIDs WHERE artNr LIKE 'NI%' AND artNr NOT LIKE 'NIOCC%'")
            all_possible_numbers = [row[0] for row in c.fetchall()]

            found_art_numbers = [row[1] for row in results]
            actually_excluded = [art for art in excluded_articles if art in all_possible_numbers]
            missing_numbers = [
                num for num in all_possible_numbers
                if num not in found_art_numbers and num not in actually_excluded
            ]

            if self.include_duplicates:
                values = [str(row[0]) for row in results]
            else:
                unique_results = {}
                for gambio_id, art_nr in results:
                    if art_nr not in unique_results:
                        unique_results[art_nr] = str(gambio_id)
                values = list(unique_results.values())

            expected_count = len(all_possible_numbers) - len(actually_excluded)
            output_count = len(values)

            self.update_output_box(
                "\n".join(values),
                expected_count,
                output_count,
                missing_numbers,
                excluded_count=len(actually_excluded),
                raw_results=results
            )

    def query_database_all_sony_with_exclusions(self, excluded_articles):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            query = f"""
                SELECT {"DISTINCT" if not self.include_duplicates else ""} gambioID, artNr
                FROM gambioIDs
                WHERE artNr LIKE 'SO%'
            """
            parameters = []

            if excluded_articles:
                placeholders = ", ".join("?" for _ in excluded_articles)
                query += f" AND artNr NOT IN ({placeholders})"
                parameters.extend(excluded_articles)

            c.execute(query, parameters)
            results = c.fetchall()

            c.execute("SELECT DISTINCT artNr FROM gambioIDs WHERE artNr LIKE 'SO%'")
            all_possible_numbers = [row[0] for row in c.fetchall()]

            found_art_numbers = [row[1] for row in results]
            actually_excluded = [art for art in excluded_articles if art in all_possible_numbers]
            missing_numbers = [
                num for num in all_possible_numbers
                if num not in found_art_numbers and num not in actually_excluded
            ]

            if self.include_duplicates:
                values = [str(row[0]) for row in results]
            else:
                unique_results = {}
                for gambio_id, art_nr in results:
                    if art_nr not in unique_results:
                        unique_results[art_nr] = str(gambio_id)
                values = list(unique_results.values())

            expected_count = len(all_possible_numbers) - len(actually_excluded)
            output_count = len(values)

            self.update_output_box(
                "\n".join(values),
                expected_count,
                output_count,
                missing_numbers,
                excluded_count=len(actually_excluded),
                raw_results=results
            )

    def update_output_box(
            self,
            results_text,
            expected_count,
            output_count,
            missing_numbers=None,
            excluded_count=0,
            raw_results=None
    ):
        self.result_textbox.setText(results_text)

        if not hasattr(self, 'status_label'):
            self.status_label = QLabel(self)
            self.status_label.setTextFormat(Qt.TextFormat.RichText)
            self.layout().insertWidget(self.layout().indexOf(self.result_textbox), self.status_label)
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        base_style = """
        QTextEdit {{
            background-color: #1e1e1e;
            border-radius: 8px;
            padding: 5px;
            border: 2px solid {border_color};
        }}
        QScrollBar:vertical {{
            background: #2b2b2b;
            width: 10px;
            margin: 2px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: #5a5a5a;
            border-radius: 5px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #888888;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        """

        if self.include_duplicates_checkbox.isChecked():
            results_text = "<br>".join(str(row[0]) for row in raw_results)
            output_count = len(raw_results)
            expected_count += len([row for row in raw_results if row[1] in [r[1] for r in raw_results]])  # estimate
            duplicate_notice = ""  # no warning when duplicates are allowed
        else:
            unique_results = {row[1]: str(row[0]) for row in raw_results}
            results_text = "<br>".join(unique_results.values())
            output_count = len(unique_results)
            from collections import Counter
            artnr_counts = Counter(row[1] for row in raw_results)
            duplicates = [artnr for artnr, count in artnr_counts.items() if count > 1]
            if duplicates:
                total_extras = sum(count - 1 for artnr, count in artnr_counts.items() if count > 1)
                duplicate_notice = (
                    f"<br>\u26a0\ufe0f <b>{len(duplicates)}</b> doppelte Artikelnummern erkannt \u26a0\ufe0f"
                    f"<br>(<b>{total_extras}</b> zusätzliche Einträge, nur jeweils erste übernommen)"
                )
            else:
                duplicate_notice = ""

        self.result_textbox.setText(results_text)

        total_display = output_count + excluded_count if self.include_duplicates_checkbox.isChecked() else expected_count + excluded_count

        if self.include_duplicates_checkbox.isChecked():
            self.result_textbox.setStyleSheet(base_style.format(border_color="green"))
            self.status_label.setStyleSheet("color: green;")
            summary = (
                f"Total: <b>{output_count + excluded_count}</b> | Ausgeschlossen: <b>{excluded_count}</b> | Output: <b>{output_count}</b>")
            self.status_label.setText(f"Alle Nummern Konvertiert<br>{summary}")
            self.missing_numbers_button.setVisible(False)
        else:
            if expected_count == output_count:
                self.result_textbox.setStyleSheet(base_style.format(border_color="green"))
                self.status_label.setStyleSheet("color: green;")
            else:
                self.result_textbox.setStyleSheet(base_style.format(border_color="red"))
                self.status_label.setStyleSheet("color: red;")

            summary = (
                f"Total: <b>{expected_count + excluded_count}</b> | Ausgeschlossen: <b>{excluded_count}</b> | Output: <b>{output_count}</b>")
            self.status_label.setText(
                f"Erwartet: <b>{expected_count}</b> / Konvertiert: <b>{output_count}</b><br>{summary}{duplicate_notice}"
            )
            self.missing_numbers_button.setVisible(expected_count != output_count)

        self.missing_numbers = missing_numbers or []

    def show_missing_numbers(self):
        """Display missing numbers in a pop-up window."""
        if not self.missing_numbers:
            QMessageBox.information(self, "Information", "Es fehlen keine Nummern.")
            return

        missing_text = "\n".join(self.missing_numbers)
        dialog = QDialog(self)
        dialog.setWindowTitle("Fehlende Nummern")
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit(dialog)
        text_edit.setPlainText(missing_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        close_button = QPushButton("Schliessen", dialog)
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec()

    def reset_output_on_tab_change(self):
        """Reset the output box and status label when switching tabs."""
        self.result_textbox.clear()
        if hasattr(self, 'status_label'):
            self.status_label.setText("")

    def change_format(self):
        """Format result output."""
        current_text = self.result_textbox.toPlainText()
        formatted_text = ", ".join(line.strip() for line in current_text.splitlines() if line.strip())
        self.result_textbox.setPlainText(formatted_text)

    def copy_to_clipboard(self):
        """Copy the result to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_textbox.toPlainText())

    def open_progress_window(self):
        """Open the progress window for scraping operations."""
        self.progress_window = ProgressWindow(self.loading_icon_path, parent=self)  # Use the correct icon path
        self.progress_window.show()

        # Start the scrape thread
        self.scrape_thread = ScrapeThread(self.scraper)
        self.scrape_thread.progress_updated.connect(self.progress_window.progress_bar.setValue)
        self.scrape_thread.scraping_completed.connect(self.progress_window.show_completion_message)
        self.scrape_thread.error_occurred.connect(self.show_error_message)
        self.scrape_thread.start()

    def show_error_message(self, error_message):
        """
        Display an error message in a message box.

        Args:
            error_message (str): The error message to display.
        """
        QMessageBox.critical(self, "Fehler", error_message)


class ProgressWindow(QDialog):
    """
    Progress window for displaying scraping progress.

    This class creates a dialog that shows the progress of the scraping operation,
    including a progress bar and completion messages.
    """

    def __init__(self, loading_icon_path, parent=None):
        super().__init__()
        self.loading_icon_path = loading_icon_path
        self.initUI()
        self.setWindowIcon(QIcon(self.loading_icon_path))

        # Center the window on the right side of the screen
        self.center_on_right_half()

    def initUI(self):
        """
        Initialize the user interface components for the progress window.
        """
        self.setWindowTitle("Scraping Progress")
        self.setFixedSize(400, 200)

        # Progress bar setup
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 50, 300, 30)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #111111;
                border-radius: 5px;
                background: #222222;
                text-align: center;
                font-size: 16px;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #00ff00;
                box-shadow: 0 0 15px #00ff00;
            }
        """)

        # Layout for progress bar and optional buttons
        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def center_on_right_half(self):
        """
        Center the window on the right half of the primary screen.
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        # Calculate the position for the right half of the screen
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        window_width = self.width()
        window_height = self.height()

        x = screen_width // 2 + (screen_width // 2 - window_width) // 2
        y = (screen_height - window_height) // 2

        # Move the window to the calculated position
        self.move(x, y)

    def show_completion_message(self):
        """
        Display a completion message when the scraping is finished.
        """
        # Remove all widgets from the current layout
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Add success label
        completion_label = QLabel("✅ Datenbank erfolgreich aktualisiert!", self)
        completion_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00aa00;")
        completion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(completion_label)

        # Add close button
        close_button = QPushButton("Schliessen", self)
        close_button.clicked.connect(self.close)
        self.layout().addWidget(close_button)

        # Trigger label refresh in parent (if exists)
        if self.parent() and hasattr(self.parent(), 'refresh_last_updated_label'):
            self.parent().refresh_last_updated_label()


class ScrapeThread(QThread):
    """Thread for performing scraping operations."""
    progress_updated = pyqtSignal(int)
    scraping_completed = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, scraper):
        super().__init__()
        self.scraper = scraper

    def run(self):
        """Execute the scraping operations."""
        try:
            self.scraper.setup_driver()
            self.scraper.login(email, password)
            self.scraper.navigate_gambio(self.progress_updated)
            self.scraping_completed.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            if hasattr(self.scraper, 'driver'):
                self.scraper.driver.quit()


class Scrape:
    """Scrape class for handling web scraping operations."""

    def setup_driver(self):
        """Set up the web driver for scraping."""
        base_path = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
        chromedriver_path = os.path.join(base_path, 'chromedriver.exe')
        chrome_binary_path = os.path.join(base_path, 'chrome', 'win64-118.0.5993.70', 'chrome-win64', 'chrome.exe')

        options = webdriver.ChromeOptions()
        options.binary_location = chrome_binary_path  # Use the specific Chrome binary
        service = Service(chromedriver_path)

        self.driver = webdriver.Chrome(service=service, options=options)

    def login(self, email, password):
        """Log in to the website."""
        self.driver.get("https://www.graphicart.ch/shop/de/")
        kundenlogin_button = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.dropdown-toggle[title="Anmeldung"]'))
        )
        kundenlogin_button.click()
        self.driver.find_element(By.ID, "box-login-dropdown-login-username").send_keys(email)
        self.driver.find_element(By.ID, "box-login-dropdown-login-password").send_keys(password)
        self.driver.find_element(By.XPATH, '//input[@value="Anmelden"]').click()

    def navigate_gambio(self, progress_signal):
        """Navigate to the Gambio admin page and scrape data."""
        with sqlite3.connect(DB_PATH) as conn:

            c = conn.cursor()
            self.driver.get("https://www.graphicart.ch/shop/admin/validproducts.php")
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table:nth-child(1) tr")[2:]
            total_rows = len(rows)

            for index, row in enumerate(rows):
                cols = row.find_elements(By.TAG_NAME, "td")
                gambio_id = cols[0].text
                art_name = cols[1].text
                art_nr = cols[2].text
                c.execute("INSERT OR IGNORE INTO gambioIDs (gambioID, bezeichnung, artNr) VALUES (?, ?, ?)",
                          (gambio_id, art_name, art_nr))
                if index % 10 == 0 or index == total_rows - 1:
                    conn.commit()
                progress_signal.emit(int((index + 1) / total_rows * 100))

            conn.commit()
        c.execute("UPDATE gambioIDs SET artNr = artNr WHERE gambioID = (SELECT gambioID FROM gambioIDs LIMIT 1)")
        conn.commit()
        self.driver.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    setup_db()
    scraper = Scrape()
    gui = GUI(scraper)
    gui.show()
    sys.exit(app.exec())
