

if getattr(sys, "frozen", False):
    # Running as packaged executable, driver is in same directory
    base_path = sys._MEIPASS
else:
    # Running as normal script, driver is in parent directory
    base_path = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.dirname(base_path)
chromedriver_path = os.path.join(base_path, 'chromedriver.exe')
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.path.join(base_path, 'chrome', 'win64-118.0.5993.70', 'chrome-win64',
                                              'chrome.exe')

service = Service(chromedriver_path)

try:
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://www.graphicart.ch/shop/de/")
except Exception as e:
    print(f"An error occurred: {e}")
    return