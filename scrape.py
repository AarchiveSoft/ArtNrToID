"""
Scrape Gambio to generate a list of art-nr / gambio id pairs.
"""
import os
import sys

import sqlite3

from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QDate, QTime, QEasingCurve, QPropertyAnimation
from PyQt6.QtGui import QIcon, QFont, QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QTabWidget,
    QDialog,
    QTimeEdit,
    QCalendarWidget,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QMainWindow,
    QTreeWidget,
    QTreeWidgetItem, QGridLayout,
)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

email = "feigelluck@gmail.com"
password = "Graphicart#1"


class GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.title = "Gambio ID Konverter"
        self.height = 400
        self.width = 200
        self.top = 100
        self.left = 100

        self.category_data = {
            "Kamerasysteme + Objektive": {
                "Nikon"    : {
                    "Nikon Z"                 : {},
                    "Nikkor Z-Mount Objektive": {},
                    "Nikon DSLR"              : {},
                    "Nikkor F-Mount Objektive": {},
                    "Nikon Blitzgeräte"       : {},
                    "Nikon Coolpix"           : {},
                    "Nikon DSLR Zubehör"      : {},
                    "Nikon Objektivzubehör"   : {},
                },
                "Sony"     : {
                    "Sony E-Mount Kameras"        : {},
                    "Sony E-Mount Objektive"      : {},
                    "Sony E-Mount APS-C Kameras"  : {},
                    "Sony E-Mount APS-C Objektive": {},
                    "Sony E-Mount Zubehör"        : {},
                    "Sony Blitzgeräte"            : {},
                    "Sony Kompaktkameras"         : {},
                    "Sony XPERIA Smartphones"     : {},
                    "Sony A-Mount Kameras"        : {},
                    "Sony A-Mount Objektive"      : {},
                    "Sony A-Mount Zubehör"        : {},
                },
                "Phase One": {
                    "Phase One IQ Backs"                       : {},
                    "Phase One XF Camera System"               : {},
                    "Phase One XT Camera System"               : {},
                    "CPO Phase One IQ Backs für Phase One XF"  : {},
                    "CPO Phase One XF Kamerasysteme"           : {},
                    "CPO Phase One IQ Backs für Hasselblad"    : {},
                    "Phase One XF Kamerasysteme"               : {},
                    "Phase One XT Kamera und Objektive"        : {},
                    "Schneider Kreuznach Objektive (Blue Ring)": {},
                    "CPO Schneider Kreuznach Objektive"        : {},
                    "Capture One"                              : {},
                },
                "Cambo"    : {
                    "Cambo Wide RS"                : {},
                    "Cambo ACTUS"                  : {},
                    "Cambo Zubehör zu Phase One XT": {},
                    "Cambo Adapter"                : {},
                    "Cambo ACTUS DB"               : {},
                    "Cambo ACTUS-XL"               : {},
                },
                "Leica"    : {
                    "Leica M & Objektive"      : {},
                    "Leica Q"                  : {},
                    "Leica SL & Objektive"     : {},
                    "Leica S & Objektive"      : {},
                    "Leica TL / CL & Objektive": {},
                    "Leica V"                  : {},
                    "Leica X"                  : {},
                    "Leica SOFORT"             : {},
                },
            }
        }

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        main_layout = QVBoxLayout()

        # brand selection
        marken_label = QLabel("Marke", self)
        main_layout.addWidget(marken_label)

        # brand dropdown
        marken_combobox = QComboBox(self)
        marken_combobox.addItems(self.category_data["Kamerasysteme + Objektive"].keys())
        main_layout.addWidget(marken_combobox)

        # category selection
        kategorie_label = QLabel("Kategorie", self)
        main_layout.addWidget(kategorie_label)

        kategorie_combobox = QComboBox(self)
        main_layout.addWidget(kategorie_combobox)

        auswahl_layout = QGridLayout()

        """
        auswahl_label = QLabel("Auswahl")
        auswahl_layout.addWidget(auswahl_label, 0, 0)
        auswahl_marke_label = QLabel("Marke")
        auswahl_layout.addWidget(auswahl_marke_label, 1, 0)
        auswahl_marke = QLabel(marken_combobox.currentText())
        auswahl_layout.addWidget(auswahl_marke, 1, 1)
        auswahl_kategorie_label = QLabel("Kategorie")
        auswahl_layout.addWidget(auswahl_kategorie_label, 2, 0)
        auswahl_kategorie = QLabel(kategorie_combobox.currentText())
        auswahl_layout.addWidget(auswahl_kategorie, 2, 1)

        main_layout.addLayout(auswahl_layout)
        """

        main_layout.addStretch()

        self.update_subcategories(marken_combobox, kategorie_combobox)
        marken_combobox.currentTextChanged.connect(
            lambda: self.update_subcategories(marken_combobox, kategorie_combobox)
        )

        self.setLayout(main_layout)
        self.show()

    def update_subcategories(self, marken_combobox, categories_combobox):
        """
        Updates the subcategories in the categories_combobox based on the selected_marke in marken_combobox.

        :param marken_combobox: The combobox representing the selected brand.
        :type marken_combobox: QComboBox
        :param categories_combobox: The combobox to be updated with subcategories.
        :type categories_combobox: QComboBox
        :return: None
        :rtype: None
        """
        selected_marke = marken_combobox.currentText()
        categories_combobox.clear()
        if selected_marke in self.category_data["Kamerasysteme + Objektive"]:
            categories_combobox.addItems(
                self.category_data["Kamerasysteme + Objektive"][selected_marke].keys()
            )


class Scrape(QWidget):
    """
    :return: None
    """

    def main(self):
        """
        :return: None

        """
        self.setup_driver()
        self.login(email, password)
        self.setup_db()
        self.navigate_gambio()

    def setup_driver(self):
        """
        :return: None
        """
        if getattr(sys, "frozen", False):
            # Running as packaged executable, driver is in same directory
            base_path = sys._MEIPASS
        else:
            # Running as normal script, driver is in parent directory
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
        """
        :param driver:
        :param condition:
        :param time:
        :return:

        """
        return WebDriverWait(driver, 10).until(condition)

    def login(self, email, password):
        """
        :param email: Email address for login
        :param password: Password for login
        :return: None
        """
        # wait to load
        kundenlogin_button = self.wait(self.driver, EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'a.dropdown-toggle[title="Anmeldung"]')))
        kundenlogin_button.click()

        # enter email
        email_field = self.wait(self.driver,
                                EC.presence_of_element_located((By.ID, 'box-login-dropdown-login-username')))
        email_field.send_keys(email)

        # enter password
        password_field = self.wait(self.driver,
                                   EC.presence_of_element_located((By.ID, 'box-login-dropdown-login-password')))
        password_field.send_keys(password)

        # click login button
        login_button = self.wait(self.driver,
                                 EC.presence_of_element_located((By.XPATH, '//input[@value="Anmelden"]')))
        login_button.click()

    def navigate_gambio(self):
        """
        :return: None
        """
        # after login, get page to create new coupon directly
        self.driver.get("https://www.graphicart.ch/shop/admin/validproducts.php")

        """
        # wait for page to load
        anzeigen_link = self.wait(self.driver,
                                  EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='validproducts.php']")))
        anzeigen_link.click()
        """

        # wait for list to load
        self.wait(self.driver, EC.visibility_of_element_located((By.CSS_SELECTOR, ".pageHeading")))

        # get list container
        list_container = self.wait(self.driver, EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "body > table:nth-child(1) > tbody:nth-child(1)")))

        # get rows, excluding first 2 (first = header, second = column headers)
        rows = list_container.find_elements(By.CSS_SELECTOR, "tr")[2:]

        for row in rows:
            columns = row.find_elements(By.CSS_SELECTOR, "td")
            gambio_id = columns[0].text
            art_name = columns[1].text
            art_nr = columns[2].text
            """
            print(f"Gambio ID: {gambio_id}"
                  f"\nArtikelname: {art_name}"
                  f"\nArtikelnummer: {art_nr}")
            """

            self.c.execute("""
                INSERT OR IGNORE INTO gambioIDs (gambioID, bezeichnung, artNr)
                VALUES (?, ?, ?)
            """, (gambio_id, art_name, art_nr))
            self.conn.commit()

    def setup_db(self):
        """
        :Return: None
        """
        self.conn = sqlite3.connect("GambioIDs.db")
        self.c = self.conn.cursor()

        self.c.execute(
            """
            CREATE TABLE IF NOT EXISTS gambioIDs (
            gambioID INTEGER PRIMARY KEY ,
            bezeichnung TEXT,
            artNr TEXT
            )
            """
        )
        self.conn.commit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GUI()
    sys.exit(app.exec())
