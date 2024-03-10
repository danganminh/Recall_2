from bs4 import BeautifulSoup
from numpy import setdiff1d, loadtxt, argmax
from re import search

# Update
import time
import random
import pandas as pd
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from function.pass_tracking import pass_tracking
# Update


def remove_duplicates(input_string, check=False):

    input_list = list(input_string)
    length = len(input_list)
    temp = []
    for val in input_list:
        if val not in temp:
            temp.append(val)

    result = ''.join(temp)

    if not check:
        return result
    else:
        return len(list(result)) != length


def add_variation(model_names, button_class, double=False):
    if len(button_class) == 0:
        return 'no_variation'

    more_model_name = "," in model_names
    model_names = [val.strip() for val in model_names.split(",")] if more_model_name else model_names

    max_scores = []

    for variation_html in button_class:
        variation_text = variation_html.get_text().upper() if not double else variation_html
        count_true = 0
        for model in model_names:
            variation_text = remove_duplicates(variation_text) if not double and not remove_duplicates(model, check=True) else variation_text
            if more_model_name:
                for char_variation in variation_text:
                    for char_model in model:
                        if char_model.upper() in char_variation.upper():
                            count_true += 1
            else:
                for char_variation in variation_text:
                    if model.upper() in char_variation.upper():
                        count_true += 1

        max_scores.append(count_true)

    index_max_score = argmax(max_scores)
    return button_class[index_max_score].get_text() if not double else button_class[index_max_score]


def add_double_variation(model_names, button_class_1, button_class_2):

    if len(button_class_1) == 0 or len(button_class_2) == 0:
        return 'no_variation'
    
    variations_1 = [button.get_text() for button in button_class_1]
    variations_2 = [button.get_text() for button in button_class_2]
    variations_2 = setdiff1d(variations_2, variations_1)

    # Find best variations from each class
    best_variation_1 = add_variation(model_names, variations_1, double=True)
    best_variation_2 = add_variation(model_names, variations_2, double=True)

    return f"{best_variation_1}|||{best_variation_2}"


def get_item_id(link):
    match = search(r"\.(\d+\.\d+)\?", link)
    if match:
        return match.group(1).split('.')[-1]
    return None


def remove_same_link(links):
    if len(links) <= 1:
        return links
    unique_ids = []
    unique_links = []
    for link in links:
        item_id = get_item_id(link)
        if item_id not in unique_ids:
            unique_ids.append(item_id)
            unique_links.append(link)
    return unique_links


def check_brand_in_specifications_and_description(soup):
    check = ["THƯƠNG HIỆU", "BRAND"]
    spec_labels = [label.get_text().upper() for label in soup.find_all('div', class_="Gf4Ro0")[0].find_all("label")]
    desc_labels = [des.get_text().upper() for des in soup.find_all("div", class_="Gf4Ro0")[1].find_all("div", class_="e8lZp3")[0].find_all("p", class_="QN2lPu")]
    return any(check_item in spec_labels or check_item in desc_labels for check_item in check)


def process_variation(driver, model_names, attention, no_brand, method, id):

    link_path = f"data/{id}/{method}_raw_links_{id}.txt"
    links = loadtxt(link_path, dtype=str)
    links = remove_same_link(links)

    count = 1
    variation_list = []
    link_list = []
    title_list = []

    try:
        
        # download all raw link first
        for link in links:

            driver.get(link)

            # logic pass tracking wait title
            if not pass_tracking(driver=driver, link=link, list_css=['div.WBVL_7'], timewait=10, loops=0):
                time.sleep(60) # Resolve Capthcha by hand

            # Scroll random
            for _ in range(15):
                scroll_origin = ScrollOrigin.from_viewport(1920//2, 1080//2)
                ActionChains(driver).scroll_from_origin(scroll_origin, 0, 500).perform()
                time.sleep(random.uniform(0.1, 1))


            # logic pass tracking wait final page
            if not pass_tracking(driver=driver, link=link, list_css=['div.v-center'], timewait=30, loops=3):
                continue

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Check if using no_brand
            if no_brand: # if using no brand and has brand in label skip
                if check_brand_in_specifications_and_description(soup):
                    continue
            
            # Add title
            title = soup.find('div', class_='WBVL_7').text.strip() if soup.find('div', class_='WBVL_7') else ''
            title_list.append(title)

            if not title_list:
                continue

            class_bodies = soup.find_all("div", {"class": "j7HL5Q"})
            url = link

            if len(class_bodies) < 1:
                value = 'no_variation'
            elif len(class_bodies) == 1:
                button_class = class_bodies[0].find_all('button')
                value = add_variation(model_names, button_class)
            else:
                button_class_1 = class_bodies[0].find_all('button')
                button_class_2 = class_bodies[1].find_all('button')
                value = add_double_variation(model_names, button_class_1, button_class_2)
                
            if attention != "dont":
                more_attention = "," in attention 
                attention = [val.strip() for val in attention.split(",")] if more_attention else [attention]
                if value == 'no_variation':
                    variation_list.append(value)
                    link_list.append(url)
                else:
                    if more_attention:
                        for value_check in attention:
                            if value_check.upper() in value.upper():
                                variation_list.append(value)
                                link_list.append(url)
                                break
                    else:
                        if attention.upper() in value.upper():
                            variation_list.append(value)
                            link_list.append(url)
            else:
                variation_list.append(value)
                link_list.append(url)

            print(f"process_variations page {count}: {value}")
            count += 1

    except Exception as e:
        print(f"Error in Processing Variations: {e}")

    finally:
        path_save = f"data/{id}/{method}_{id}"
        df = pd.DataFrame({
            "link": link_list,
            "title": title_list,
            "variation": [str(val) for val in variation_list]
        })
        df.to_csv(f"{path_save}.csv", encoding='utf-8', index=False)
        return driver
