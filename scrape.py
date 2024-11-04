import os
import sqlite3
import sys
import time
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QDialog, QProgressBar, QMessageBox,
    QTextEdit, QHBoxLayout
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
    """
    Resource path utility function.

    This function returns the absolute path of a resource file based on whether the application is running as a frozen executable or in a normal environment.

    Args:
        relative_path (str): The relative path of the resource file.

    Returns:
        str: The absolute path of the resource file.
    """
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)


def setup_db():
    """
    Set up the database schema if it does not already exist.

    This function creates a SQLite database and a table for storing Gambio IDs if they are not already present.

    Returns:
        None
    """
    with sqlite3.connect("GambioIDs.db") as conn:
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
    """
    GUI class for the Gambio ID Converter application.

    This class initializes the user interface for the application, allowing users to select brands and categories, exclude articles, and convert article numbers to Gambio IDs.

    Args:
        scrape: An instance of the Scrape class used for web scraping operations.
    """

    def __init__(self, scrape):
        super().__init__()
        self.title = "Gambio ID Konverter"
        self.height = 500
        self.width = 400
        self.top = 100
        self.left = 100

        self.scraper = scrape

        self.category_data = {
            "Kamerasysteme + Objektive"         : {
                "Nikon"                         : {
                    "Nikon Z"                   : {"initials": "NIVOA"},
                    "Nikkor Z-Mount Objektive"  : {"initials": "NIJMA"},
                    "Nikon DSLR"                : {"initials": "NIVBA"},
                    "Nikkor F-Mount Objektive"  : {"initials": "NIJAA"},
                    "Nikon Blitzgeräte"         : {"initials": "NIFSA"},
                    "Nikon Coolpix"             : {"initials": "NIVQA"}
                },
                "Sony"                          : {
                    "Sony E-Mount Kameras"      : {"initials": "SOILCE"},
                    "Sony E-Mount Objektive"    : {"initials": "SOSEL"},
                    "Sony Kompaktkameras"       : {"initials": "SOZV & SODSC"}
                },
                "Fujifilm"                      : {
                    "Fujifilm GFX Kameras"      : {"initials": "FJ"},
                    "Fujifilm GFX Objektive"    : {"initials": "FJ"},
                    "Fujifilm X Kameras"        : {"initials": "FJ"}
                },
                "Phase One"                     : {
                    "Phase One IQ Backs"        : {"initials": "PO"},
                    "Phase One XF Camera System": {"initials": "PO"}
                },
                "Cambo"                         : {
                    "Cambo Wide RS"             : {"initials": "CA"},
                    "Cambo ACTUS"               : {"initials": "CA"}
                },
                "Leica"                         : {
                    "Leica M & Objektive"       : {"initials": "n/a"},
                    "Leica Q"                   : {"initials": "n/a"}
                }
            }
        }

        self.main_icon_path = resource_path('main_icon.ico')
        self.loading_icon_path = resource_path('loading_icon.ico')

        self.initUI()

    def initUI(self):
        """
        Initialize the user interface components.

        This method sets up the main layout, buttons, dropdowns, and connects signals to their respective slots.

        Returns:
            None
        """
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowIcon(QIcon(self.main_icon_path))

        main_layout = QVBoxLayout()

        # Rescrape button
        rescrape_button = QPushButton("Datenbank aktualisieren")
        rescrape_button.clicked.connect(self.open_progress_window)
        main_layout.addWidget(rescrape_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Brand dropdown
        self.marken_combobox = QComboBox(self)
        self.marken_combobox.addItems(self.category_data["Kamerasysteme + Objektive"].keys())
        main_layout.addWidget(QLabel("Marke"))
        main_layout.addWidget(self.marken_combobox)

        # Category dropdown
        self.kategorie_combobox = QComboBox(self)
        main_layout.addWidget(QLabel("Kategorie"))
        main_layout.addWidget(self.kategorie_combobox)

        # Update subcategories based on brand selection
        self.update_subcategories()
        self.marken_combobox.currentTextChanged.connect(self.update_subcategories)

        # Exclude input
        self.exclude_input = QLineEdit(self)
        self.exclude_input.setToolTip("Artikelnummern (getrennt mit Kommas)")
        main_layout.addWidget(QLabel("<b>Ausschliessen:</b>"))
        main_layout.addWidget(self.exclude_input)

        # Convert button
        convert_button = QPushButton("Konvertieren", self)
        convert_button.clicked.connect(self.convert_articles)
        main_layout.addWidget(convert_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Result display area
        self.result_textbox = QTextEdit(self)
        self.result_textbox.setReadOnly(True)
        main_layout.addWidget(self.result_textbox)

        # Output layout for format change and copy buttons
        output_layout = QHBoxLayout()
        format_button = QPushButton("Format ändern", self)
        format_button.clicked.connect(self.change_format)
        output_layout.addWidget(format_button)
        copy_button = QPushButton("In Zwischenablage kopieren", self)
        copy_button.clicked.connect(self.copy_to_clipboard)
        output_layout.addWidget(copy_button)
        main_layout.addLayout(output_layout)

        main_layout.addStretch()
        self.setLayout(main_layout)
        self.show()

    def copy_to_clipboard(self):
        """
        Copy the text from the result textbox to the clipboard.

        This method retrieves the text from the result display area and sets it to the system clipboard.

        Returns:
            None
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_textbox.toPlainText())

    def change_format(self):
        """
        Change the format of the text in the result textbox.

        This method processes the current text, removing empty lines and formatting it into a comma-separated string.

        Returns:
            None
        """
        current_text = self.result_textbox.toPlainText()
        formatted_text = ", ".join([line for line in current_text.split("\n") if line])
        self.result_textbox.setPlainText(formatted_text)

    def update_subcategories(self):
        """
        Update the category dropdown based on the selected brand.

        This method clears the current categories and populates the dropdown with subcategories corresponding to the selected brand.

        Returns:
            None
        """
        selected_brand = self.marken_combobox.currentText()
        self.kategorie_combobox.clear()
        if selected_brand in self.category_data["Kamerasysteme + Objektive"]:
            self.kategorie_combobox.addItems(self.category_data["Kamerasysteme + Objektive"][selected_brand].keys())

    def convert_articles(self):
        """
        Convert selected articles to Gambio IDs.

        This method retrieves the selected brand and category, processes excluded articles, and queries the database for matching Gambio IDs.

        Returns:
            None
        """

        selected_brand = self.marken_combobox.currentText()
        selected_category = self.kategorie_combobox.currentText()
        excluded_articles = [article.strip() for article in self.exclude_input.text().split(",") if article.strip()]
        initials = self.category_data["Kamerasysteme + Objektive"][selected_brand][selected_category].get("initials")

        if initials == "n/a":
            QMessageBox.warning(self, "Kategorie nicht verwendbar",
                                "Die ausgewählte Kategorie kann nicht verwendet werden.")
            return

        try:
            with sqlite3.connect("GambioIDs.db") as conn:
                self.query_database(conn, initials, excluded_articles)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"An error occurred when pulling from DB: {e}")

    def query_database(self, conn, initials, excluded_articles):
        """
        Query the database for Gambio IDs based on the selected criteria.

        This method executes a SQL query to retrieve Gambio IDs while considering excluded articles.

        Args:
            conn: The database connection object.
            initials (str): The initials to filter Gambio IDs.
            excluded_articles (list): A list of articles to exclude from the results.

        Returns:
            None
        """
        c = conn.cursor()
        query = "SELECT gambioID FROM gambioIDs WHERE artNr LIKE ?"
        parameters = [f"{initials}%"]

        if excluded_articles:
            placeholders = ", ".join("?" for _ in excluded_articles)
            query += f" AND artNr NOT IN ({placeholders})"
            parameters.extend(excluded_articles)

        c.execute(query, parameters)
        gambio_ids = [str(row[0]) for row in c.fetchall()]
        self.result_textbox.setText("\n".join(gambio_ids))

    def open_progress_window(self):
        """
        Open the progress window for scraping operations.

        This method initializes and displays the progress window, connecting it to the scraping thread for updates.

        Returns:
            None
        """
        self.progress_window = ProgressWindow(self.loading_icon_path)  # Pass the icon path
        self.progress_window.show()
        self.scrape_thread = ScrapeThread(self.scraper)
        self.scrape_thread.progress_updated.connect(self.progress_window.progress_bar.setValue)
        self.scrape_thread.scraping_completed.connect(self.progress_window.show_completion_message)
        self.scrape_thread.error_occurred.connect(self.show_error_message)
        self.scrape_thread.start()

    def show_error_message(self, error_message):
        """
        Display an error message in a message box.

        This method shows a critical error message dialog with the provided error message.

        Args:
            error_message (str): The error message to display.

        Returns:
            None
        """
        QMessageBox.critical(self, "Fehler", error_message)


class ProgressWindow(QDialog):
    """
    Progress window for displaying scraping progress.

    This class creates a dialog that shows the progress of the scraping operation, including a progress bar and completion messages.

    Args:
        loading_icon_path (str): The path to the loading icon to be displayed in the window.
    """

    def __init__(self, loading_icon_path):
        super().__init__()
        self.loading_icon_path = loading_icon_path  # Store the icon path
        self.initUI()
        self.setWindowIcon(QIcon(self.loading_icon_path))

        self.center_on_right_half()

    def initUI(self):
        """
        Initialize the user interface components for the progress window.

        This method sets up the progress bar and its layout.

        Returns:
            None
        """
        self.setWindowTitle("Scraping Progress")
        self.setFixedSize(400, 200)
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
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.progress_bar)
        self.setLayout(self.layout)

    def center_on_right_half(self):
        """
        Center the progress window in the middle of the right half of the screen.

        This method calculates the appropriate position for the window and moves it accordingly.

        Returns:
            None
        """
        screen = QApplication.primaryScreen()  # Get the primary screen
        screen_geometry = screen.geometry()  # Get the geometry of the screen
        right_half_width = screen_geometry.width() // 2  # Width of the right half
        x = right_half_width + (right_half_width - self.width()) // 2  # Center in the right half
        y = (screen_geometry.height() - self.height()) // 2  # Center vertically
        self.move(x, y)  # Move to the calculated position

    def show_completion_message(self):
        """
        Display a completion message when the scraping is finished.

        This method hides the progress bar and shows a message indicating that the database has been updated.

        Returns:
            None
        """
        self.progress_bar.hide()
        completion_label = QLabel("Datenbank aktualisiert", self)
        completion_label.setStyleSheet("font-size: 20px; font-weight: bold; color: green;")
        completion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(completion_label)

        # Add a close button
        close_button = QPushButton("Schliessen", self)
        close_button.clicked.connect(self.close)  # Connect the 'clicked' signal to the window's close slot
        self.layout.addWidget(close_button)

        self.adjustSize()


class ScrapeThread(QThread):
    """
    Thread for performing scraping operations.

    This class handles the execution of scraping tasks in a separate thread, allowing the GUI to remain responsive during long-running operations.

    Args:
        scraper: An instance of the Scrape class used for web scraping operations.
    """
    progress_updated = pyqtSignal(int)
    scraping_completed = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, scraper):
        super().__init__()
        self.scraper = scraper

    def run(self):
        """
        Execute the scraping operations.

        This method runs the scraping process, including setting up the driver, logging in, and navigating to the target page.

        Returns:
            None
        """
        try:
            self.scraper.setup_driver()
            self.scraper.login(email, password)
            self.scraper.navigate_gambio(self.progress_updated)
            self.scraping_completed.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))


class Scrape:
    """
    Scrape class for handling web scraping operations.

    This class manages the setup of the web driver, login process, and data retrieval from the target website.

    Args:
        None
    """
    def setup_driver(self):
        """
        Set up the web driver for scraping.

        This method initializes the Chrome web driver with the appropriate options and navigates to the target website.

        Returns:
            None
        """
        base_path = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
        chromedriver_path = os.path.join(base_path, 'chromedriver.exe')
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.path.join(base_path, 'chrome', 'win64-118.0.5993.70', 'chrome-win64',
                                                      'chrome.exe')
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.get("https://www.graphicart.ch/shop/de/")

    def wait(self, condition, time=10):
        """
        Wait for a specific condition to be met.

        This method blocks execution until the specified condition is met or the timeout occurs.

        Args:
            condition: The condition to wait for.
            time (int): The maximum time to wait in seconds.

        Returns:
            The result of the condition when it is met.
        """
        return WebDriverWait(self.driver, time).until(condition)

    def login(self, email, password):
        """
        Perform login to the target website.

        This method interacts with the web elements to enter the email and password, and submits the login form.

        Args:
            email (str): The email address for login.
            password (str): The password for login.

        Returns:
            None
        """
        kundenlogin_button = self.wait(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.dropdown-toggle[title="Anmeldung"]')))
        kundenlogin_button.click()
        email_field = self.wait(EC.presence_of_element_located((By.ID, 'box-login-dropdown-login-username')))
        email_field.send_keys(email)
        password_field = self.wait(EC.presence_of_element_located((By.ID, 'box-login-dropdown-login-password')))
        password_field.send_keys(password)
        login_button = self.wait(EC.presence_of_element_located((By.XPATH, '//input[@value="Anmelden"]')))
        login_button.click()

    def navigate_gambio(self, progress_signal):
        """
        Navigate to the Gambio admin page and scrape data.

        This method retrieves product data from the Gambio admin page and emits progress updates.

        Args:
            progress_signal: A signal to update the progress bar.

        Returns:
            None
        """
        with sqlite3.connect("GambioIDs.db") as conn:
            c = conn.cursor()
            self.driver.get("https://www.graphicart.ch/shop/admin/validproducts.php")
            self.wait(EC.visibility_of_element_located((By.CSS_SELECTOR, ".pageHeading")))
            list_container = self.wait(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "body > table:nth-child(1) > tbody:nth-child(1)")))
            rows = list_container.find_elements(By.CSS_SELECTOR, "tr")[2:]
            total_rows = len(rows)

            if total_rows == 0:
                print("No rows found for scraping.")
                return

            for index, row in enumerate(rows):
                columns = row.find_elements(By.CSS_SELECTOR, "td")
                gambio_id = columns[0].text
                art_name = columns[1].text
                art_nr = columns[2].text
                c.execute("INSERT OR IGNORE INTO gambioIDs (gambioID, bezeichnung, artNr) VALUES (?, ?, ?)",
                          (gambio_id, art_name, art_nr))
                if index % 10 == 0 or index == total_rows - 1:
                    conn.commit()
                progress_percentage = int((index + 1) / total_rows * 100)
                progress_signal.emit(progress_percentage)

            conn.commit()
            self.driver.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    setup_db()
    scrape = Scrape()
    ex = GUI(scrape)
    sys.exit(app.exec())
