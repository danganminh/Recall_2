import pandas as pd

from os import makedirs, path
import undetected_chromedriver as uc

from function.get_links import find_links
from function.process_variations import process_variation

"""
change phone number and pass word in function/check_login.py

                !!! PLEASE WAIT SOME MINUTES WHEN FIRST RUN TO SOLVE CAPTCHA !!!
"""

def create_folder(folder_path):
    if not path.exists(folder_path):
        makedirs(folder_path)

def Maping():
    
    # Create necessary folders
    create_folder("data")

    name_csv = input("Enter name of csv file: ")
    data = pd.read_csv(name_csv)
    
    
    driver = uc.Chrome(headless=False, use_subprocess=True)

    for i in range(len(data)):   


        content = data["contents"][i]
        total_pages = int(data["total_pages"][i])
        model_names = str(data["model_names"][i].replace(" ", "").split(","))
        no_brand = bool(data["no_brand"][i])
        skip_content = str(data["skip_content"][i])
        attention = str(data["attention"][i])
        id = str(data["id"][i])
        method = data["method"][i]
        url = data["url"][i]

        driver = find_links(driver=driver, url=url,total_pages=total_pages, content_keywords=content, skip_content=skip_content, method=method, id=id)
        driver = process_variation(driver=driver, model_names=model_names, attention=attention, no_brand=no_brand, method=method, id=id)
    

    driver.quit()


if __name__ == "__main__":
    Maping()
