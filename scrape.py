"""
Scrape Gambio to generate a list of art-nr / gambio id pairs.
"""
import os
import sys
import time
import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QDialog,
    QGridLayout,
    QProgressBar, QMessageBox, QTextEdit, QHBoxLayout
)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

email = "feigelluck@gmail.com"
password = "Graphicart#1"


class GUI(QWidget):
    def __init__(self, scrape):
        super().__init__()
        self.title = "Gambio ID Konverter"
        self.height = 500  # Increased height to fit a larger progress bar
        self.width = 400
        self.top = 100
        self.left = 100

        self.scraper = scrape

        self.category_data = {
            "Kamerasysteme + Objektive": {
                "Nikon"    : {
                    "Nikon Z"                 : {"initials": "NIVOA"},
                    "Nikkor Z-Mount Objektive": {"initials": "NIJMA"},
                    "Nikon DSLR"              : {"initials": "NIVBA"},
                    "Nikkor F-Mount Objektive": {"initials": "NIJAA"},
                    "Nikon Blitzgeräte"       : {"initials": "NIFSA"},
                    "Nikon Coolpix"           : {"initials": "NIVQA"},
                    "Nikon DSLR Zubehör"      : {"initials": "n/a"},
                    "Nikon Objektivzubehör"   : {"initials": "n/a"},
                },
                "Sony"     : {
                    "Sony E-Mount Kameras"        : {"initials": "SOILCE"},
                    "Sony E-Mount Objektive"      : {"initials": "SOSEL"},
                    "Sony E-Mount APS-C Kameras"  : {"initials": "SOILCE"},
                    "Sony E-Mount APS-C Objektive": {"initials": "SOSEL"},
                    "Sony E-Mount Zubehör"        : {"initials": "n/a"},
                    "Sony Blitzgeräte"            : {"initials": "n/a"},
                    "Sony Kompaktkameras"         : {"initials": "SOZV & SODSC"},
                    "Sony XPERIA Smartphones"     : {"initials": "n/a"},
                    "Sony A-Mount Kameras"        : {"initials": "n/a"},
                    "Sony A-Mount Objektive"      : {"initials": "n/a"},
                    "Sony A-Mount Zubehör"        : {"initials": "n/a"},
                },
                "Fujifilm" : {
                    "Fujifilm GFX Kameras"  : {"initials": "FJ"},
                    "Fujifilm GFX Objektive": {"initials": "FJ"},
                    "Fujifilm X Kameras"    : {"initials": "FJ"},
                },
                "Phase One": {
                    "Phase One IQ Backs"                       : {"initials": "PO"},
                    "Phase One XF Camera System"               : {"initials": "PO"},
                    "Phase One XT Camera System"               : {"initials": "PO"},
                    "CPO Phase One IQ Backs für Phase One XF"  : {"initials": "PO"},
                    "CPO Phase One XF Kamerasysteme"           : {"initials": "PO"},
                    "CPO Phase One IQ Backs für Hasselblad"    : {"initials": "PO"},
                    "Phase One XF Kamerasysteme"               : {"initials": "PO"},
                    "Phase One XT Kamera und Objektive"        : {"initials": "PO"},
                    "Schneider Kreuznach Objektive (Blue Ring)": {"initials": "PO"},
                    "CPO Schneider Kreuznach Objektive"        : {"initials": "PO"},
                    "Capture One"                              : {"initials": "PO"},
                },
                "Cambo"    : {
                    "Cambo Wide RS"                : {"initials": "CA"},
                    "Cambo ACTUS"                  : {"initials": "CA"},
                    "Cambo Zubehör zu Phase One XT": {"initials": "CA"},
                    "Cambo Adapter"                : {"initials": "CA"},
                    "Cambo ACTUS DB"               : {"initials": "CA"},
                    "Cambo ACTUS-XL"               : {"initials": "CA"},
                },
                "Leica"    : {
                    "Leica M & Objektive"      : {"initials": "n/a"},
                    "Leica Q"                  : {"initials": "n/a"},
                    "Leica SL & Objektive"     : {"initials": "n/a"},
                    "Leica S & Objektive"      : {"initials": "n/a"},
                    "Leica TL / CL & Objektive": {"initials": "n/a"},
                    "Leica V"                  : {"initials": "n/a"},
                    "Leica X"                  : {"initials": "n/a"},
                    "Leica SOFORT"             : {"initials": "n/a"},
                },
            }
        }

        self.setup_db()
        self.initUI()

    def setup_db(self):
        # Set up a read-only database connection for querying data
        self.conn = sqlite3.connect("GambioIDs.db")
        self.c = self.conn.cursor()

    def initUI(self):
        """
        :return: None
        """
        # sourcery skip: extract-duplicate-method, inline-immediately-returned-variable
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        self.setWindowIcon(QIcon(os.path.join(base_path, 'main_icon.ico')))

        main_layout = QVBoxLayout()

        # Rescrape button
        rescrape_button = QPushButton("Datenbank aktualisieren")
        rescrape_button.clicked.connect(self.open_progress_window)
        main_layout.addWidget(rescrape_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Brand selection
        marken_label = QLabel("Marke", self)
        main_layout.addWidget(marken_label)

        # Brand dropdown
        self.marken_combobox = QComboBox(self)
        self.marken_combobox.addItems(self.category_data["Kamerasysteme + Objektive"].keys())
        main_layout.addWidget(self.marken_combobox)

        # Category selection
        kategorie_label = QLabel("Kategorie", self)
        main_layout.addWidget(kategorie_label)

        self.kategorie_combobox = QComboBox(self)
        main_layout.addWidget(self.kategorie_combobox)

        # Update subcategories based on brand selection
        self.update_subcategories(self.marken_combobox, self.kategorie_combobox)
        self.marken_combobox.currentTextChanged.connect(
            lambda: self.update_subcategories(self.marken_combobox, self.kategorie_combobox)
        )

        # Exclude input
        exclude_label = QLabel("<b>Ausschliessen:</b>")
        exclude_label.setToolTip("Artikelnummern (getrennt mit Kommas)")
        main_layout.addWidget(exclude_label)

        self.exclude_input = QLineEdit(self)
        self.exclude_input.setToolTip("Artikelnummern (getrennt mit Kommas)")
        main_layout.addWidget(self.exclude_input)

        # Convert button
        convert_button = QPushButton("Konvertieren", self)
        convert_button.clicked.connect(self.convert_articles)
        main_layout.addWidget(convert_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        main_layout.addStretch()

        # Result display area
        self.result_textbox = QTextEdit(self)
        self.result_textbox.setReadOnly(True)  # Make it read-only for display
        main_layout.addWidget(self.result_textbox)

        output_layout = QHBoxLayout()

        # change format button (\n to ,)
        self.format_button = QPushButton("Format ändern", self)
        self.format_button.clicked.connect(self.change_format)
        output_layout.addWidget(self.format_button)

        # Copy to Clipboard button
        self.copy_button = QPushButton("In Zwischenablage kopieren", self)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        output_layout.addWidget(self.copy_button)

        main_layout.addLayout(output_layout)

        main_layout.addStretch()

        self.setLayout(main_layout)
        self.show()

    def copy_to_clipboard(self):
        """
        Copies the content of the result_textbox to the clipboard.
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_textbox.toPlainText())

    def change_format(self):
        current_text = self.result_textbox.toPlainText()
        raw_text = current_text.split("\n")
        formatted_text = ", ".join(raw_text)
        self.result_textbox.setPlainText(formatted_text)
        return

    def update_subcategories(self, marken_combobox, categories_combobox):
        """
        :param marken_combobox: The combobox containing the list of available brands (QComboBox)
        :param categories_combobox: The combobox where subcategories will be updated based on the selected brand (QComboBox)
        :return: No return value
        """
        selected_marke = marken_combobox.currentText()
        categories_combobox.clear()
        if selected_marke in self.category_data["Kamerasysteme + Objektive"]:
            categories_combobox.addItems(
                self.category_data["Kamerasysteme + Objektive"][selected_marke].keys()
            )

    def convert_articles(self):  # sourcery skip: extract-method
        """
        :return: None
        """
        selected_brand = self.marken_combobox.currentText()
        selected_category = self.kategorie_combobox.currentText()
        excluded_articles = self.exclude_input.text()

        excluded_articles_list = [article.strip() for article in excluded_articles.split(",")]

        initials = self.category_data["Kamerasysteme + Objektive"][selected_brand][selected_category].get("initials",
                                                                                                          "n/a")

        if initials == "n/a":
            # Show message box if the selected category can't be used
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Kategorie nicht verwendbar")
            msg_box.setText("Die ausgewählte Kategorie kann nicht verwendet werden.")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Close)
            msg_box.exec()
        else:
            try:
                # Build the SQL query dynamically to include NOT IN clause for excluded articles
                query = "SELECT gambioID FROM gambioIDs WHERE artNr LIKE ?"
                parameters = [f"{initials}%"]

                # If there are exclusions, add them to the query
                if excluded_articles_list:
                    placeholders = ", ".join("?" for _ in excluded_articles_list)
                    query += f" AND artNr NOT IN ({placeholders})"
                    parameters.extend(excluded_articles_list)

                # Execute the query with parameters
                self.c.execute(query, parameters)
                gambio_ids = [str(row[0]) for row in self.c.fetchall()]

                # Display the gambio IDs in the text box
                self.result_textbox.setText("\n".join(gambio_ids))
            except Exception as e:
                print(f"An error occurred when pulling from DB: {e}")

    def open_progress_window(self):
        """
        Open the progress window and start the scraping process.

        :return: None
        """
        # Create the progress window
        self.progress_window = ProgressWindow()
        self.progress_window.show()

        # Start the scraping process and pass the progress window to Scrape
        self.scraper.main()


class ProgressWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        self.setWindowIcon(QIcon(os.path.join(base_path, 'loading_icon.ico')))

    def initUI(self):
        # Set up the progress window
        self.setWindowTitle("Scraping Progress")
        self.setFixedSize(400, 200)  # Increased size to fit the completion message better

        # Get the screen geometry and calculate position for centering in the right half of the screen
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        window_width = self.width()
        window_height = self.height()
        x = screen_width // 2 + (screen_width // 2 - window_width) // 2  # Centered on the right half
        y = (screen_height - window_height) // 2

        self.move(x, y)

        # Create the progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 50, 300, 30)  # Adjusted size for better visibility
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #111111;
                border-radius: 5px;
                background: #222222;  /* Dark background */
                text-align: center;
                font-size: 16px;
                color: #ffffff;  /* White text */
            }
            QProgressBar::chunk {
                background-color: #00ff00;  /* Bright green neon */
                box-shadow: 0 0 15px #00ff00;  /* Glow effect */
            }
        """)

        # Set the layout for the window
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.progress_bar)
        self.setLayout(self.layout)

    def show_completion_message(self):
        # Remove the progress bar and show a "Datenbank aktualisiert" message
        self.progress_bar.hide()
        completion_label = QLabel("Datenbank aktualisiert", self)
        completion_label.setStyleSheet("font-size: 20px; font-weight: bold; color: green;")
        completion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(completion_label)
        self.adjustSize()  # Adjust window size to fit the new label


class Scrape:
    def __init__(self, progress_window):
        self.progress_window = progress_window
        self.setup_db()

    def main(self):
        # Set up the driver and perform the login
        self.setup_driver()
        self.simulate_initial_setup()  # Simulate progress for initial setup
        self.login(email, password)
        self.navigate_gambio()  # Actual scraping process
        self.progress_window.show_completion_message()  # Show the completion message once done

    def simulate_initial_setup(self):
        # Simulate progress from 0% to 10% during setup (e.g., browser launch)
        for i in range(1, 11):
            time.sleep(0.6)  # Simulated delay
            self.progress_window.progress_bar.setValue(i)
            QApplication.processEvents()  # Keep the GUI responsive

    def setup_driver(self):
        # Set up Selenium WebDriver
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        chromedriver_path = os.path.join(base_path, 'chromedriver.exe')
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.path.join(base_path, 'chrome', 'win64-118.0.5993.70', 'chrome-win64',
                                                      'chrome.exe')

        service = Service(chromedriver_path)

        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.get("https://www.graphicart.ch/shop/de/")
        except Exception as e:
            print(f"An error occurred: {e}")
            return

    def wait(self, driver, condition, time=10):
        return WebDriverWait(driver, time).until(condition)

    def login(self, email, password):
        # Log in to the website
        kundenlogin_button = self.wait(self.driver, EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'a.dropdown-toggle[title="Anmeldung"]')))
        kundenlogin_button.click()

        email_field = self.wait(self.driver,
                                EC.presence_of_element_located((By.ID, 'box-login-dropdown-login-username')))
        email_field.send_keys(email)

        password_field = self.wait(self.driver,
                                   EC.presence_of_element_located((By.ID, 'box-login-dropdown-login-password')))
        password_field.send_keys(password)

        login_button = self.wait(self.driver,
                                 EC.presence_of_element_located((By.XPATH, '//input[@value="Anmelden"]')))
        login_button.click()

    def navigate_gambio(self):
        # After login, navigate to the product page
        self.driver.get("https://www.graphicart.ch/shop/admin/validproducts.php")

        # Wait for the list to load
        self.wait(self.driver, EC.visibility_of_element_located((By.CSS_SELECTOR, ".pageHeading")))

        # Get list container
        list_container = self.wait(self.driver, EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "body > table:nth-child(1) > tbody:nth-child(1)")))

        # Get rows, excluding first 2 (header rows)
        rows = list_container.find_elements(By.CSS_SELECTOR, "tr")[2:]
        total_rows = len(rows)

        # Actual scraping, updating the progress bar from 10% to 100%
        for index, row in enumerate(rows):
            columns = row.find_elements(By.CSS_SELECTOR, "td")
            gambio_id = columns[0].text
            art_name = columns[1].text
            art_nr = columns[2].text

            # Insert into database
            self.c.execute("""
                INSERT OR IGNORE INTO gambioIDs (gambioID, bezeichnung, artNr)
                VALUES (?, ?, ?)
            """, (gambio_id, art_name, art_nr))
            self.conn.commit()

            # Update progress bar
            progress_percentage = 10 + int((index + 1) / total_rows * 90)
            self.progress_window.progress_bar.setValue(progress_percentage)
            QApplication.processEvents()  # Keep the GUI responsive

    def setup_db(self):
        # Set up the SQLite database
        self.conn = sqlite3.connect("GambioIDs.db")
        self.c = self.conn.cursor()

        self.c.execute(
            """
            CREATE TABLE IF NOT EXISTS gambioIDs (
            gambioID INTEGER PRIMARY KEY,
            bezeichnung TEXT,
            artNr TEXT
            )
            """
        )
        self.conn.commit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    progress_window = ProgressWindow()
    scrape = Scrape(progress_window)
    ex = GUI(scrape)
    sys.exit(app.exec())
