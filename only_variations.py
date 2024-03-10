from bs4 import BeautifulSoup, Comment
from numpy import setdiff1d, savetxt, argmax
from re import search
from os import listdir

from function.logic_folder import remove_item


def get_SoupHTML(html_file):
    with open(html_file, "r", encoding="utf-8") as open_file:
        soup = BeautifulSoup(open_file.read(), "html.parser")
    return soup


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
    model_names = model_names.split(", ") if more_model_name else model_names

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
                            count_true += -1
            else:
                for char_variation in variation_text:
                    if model.upper() in char_variation.upper():
                        count_true += 1
                    else:
                        count_true += -1

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


def process_variation(folder_path, model_names, attention, no_brand, method, id):

    try:
            
        variation_list = []
        link_list = []
        
        # Main process all html files
        file_html = listdir(folder_path)
        for file in file_html:
            
            if ".html" not in file or ".htm" not in file:
                continue
            
            file_path = f"{folder_path}/{file}"
            soup = get_SoupHTML(file_path)
            # Check if using no_brand
            if no_brand: # if using no brand and has brand in label skip
                if check_brand_in_specifications_and_description(soup):
                    continue

            class_body = soup.find_all("h3", {"class": "Dagtcd"})
            comment = soup.find_all(string=lambda text: isinstance(text, Comment))[0]
            url = comment[22:].split()[0]
            if len(class_body) <= 2:
                value = 'no_variation'
            elif len(class_body) == 3:
                button_class = soup.find_all("button", {"class": "SkhBL1"})
                value = add_variation(model_names, button_class)
            else:
                button_class_1 = soup.find_all("button", {"class": "SkhBL1"})
                button_class_2 = soup.find_all("button", {"class": "sApkZm"})
                value = add_double_variation(model_names, button_class_1, button_class_2)
                
            if attention != "dont":
                more_attention = "," in attention 
                attention = attention.split(",") if more_attention else attention
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

            print(variation_list[-1])
            # remove after process file
            remove_item(file_path)


        path_save = f"data/{id}/{method}_"
        savetxt(f'{path_save}link_{id}.txt', link_list, fmt='%s', encoding='utf-8')
        savetxt(f'{path_save}variation_{id}.txt', variation_list, fmt='%s', encoding='utf-8')
        
    except Exception as e:
        print(f"Error in Processing Variations: {e}")


if __name__ == "__main__":
    folder_path = "data/temp"
    model_names = "Móc treo kẹp chổi"
    attention = "dont"
    no_brand = bool(0)
    method = "search"
    id = "kep_choi"
    process_variation(folder_path=folder_path, model_names=model_names, attention=attention, no_brand=no_brand, method=method, id=id)
