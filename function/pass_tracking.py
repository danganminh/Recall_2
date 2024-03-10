import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By


def pass_tracking(driver, link, list_css, timewait, loops=5):
    for css in list_css:
        try:
            WebDriverWait(driver, timewait).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, css))
            )
        except TimeoutException:
            for i in range(loops):
                print(f"Try reload: {i+1}")
                driver.get(link)
                try:
                    WebDriverWait(driver, timewait).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, css))
                    )
                    break  # Break the loop if element is found
                except TimeoutException:                 
                    time.sleep(30)
            else:
                # If element is not found after retries, return False
                return False
    # If all elements are found, return True
    return True