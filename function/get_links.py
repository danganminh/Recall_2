from os.path import exists
from os import makedirs
from re import sub
from bs4 import BeautifulSoup
from numpy import savetxt

# Update
import time
import random
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from function.check_login import check_login, check_captcha
from function.pass_tracking import pass_tracking
# Update


def remove_not_char(string):
    return sub(r'[^\w\s]', ' ', string)


def all_upper(my_list):
    return [x.upper() for x in my_list]


def extract_links(soup, content_keywords, skip_content, method):
    more_one_content = "," in content_keywords
    content_keywords = [val.strip() for val in content_keywords.split(",")] if more_one_content else [content_keywords]

    skip = True
    more_one_skip_content = "," in skip_content
    skip_content = [val.strip() for val in skip_content.split(",")] if more_one_skip_content else [skip_content]
    if skip_content == "dont":
        skip = False

    titles = []
    links = []

    if method == "may_love":
        class_ = soup.find_all('div', {'class': "shopee_ic contents"})
    else:
        class_ = soup.find_all('li', {'class': "col-xs-2-4 shopee-search-item-result__item"})

    for item in class_:
        link_tag = item.a
        if link_tag:
            link = link_tag.get('href')
            if link:
                content_text = item.a.img.get('alt')
                if content_text:
                    content_text = remove_not_char(content_text)
                    content_text = [val.upper() for val in content_text.split()]
                    title = []
                    # Remove duplicates in title
                    for val in content_text:
                        if val not in title:
                            title.append(val)

                    if skip:
                        skip_found = any(skip_key.upper() in title for skip_key in skip_content)
                        if skip_found:
                            continue

                    if more_one_content:
                        for content_key in content_keywords:
                            content_key = [key.upper() for key in content_key.split()]
                            count = sum(1 for key in content_key if key in title)
                            if count >= len(content_key):
                                link = "https://shopee.vn" + link
                                links.append(link)
                                titles.append(title)
                                break
                    else:
                        content_key = [key.upper() for key in content_keywords[0].split()]
                        count = sum(1 for key in content_key if key in title)
                        if count >= len(content_key):
                            link = "https://shopee.vn" + link
                            links.append(link)
                            titles.append(title)

    return links, titles


def find_links(driver, url, total_pages, content_keywords, skip_content, method, id):
    
    all_links = []
    all_titles = []
    login_bool = False
    captcha_bool = False

    try:
        for i in range(1, total_pages + 1):

            print(f"Fetching links for page {i}")

            if method == "may_love":
                new_url = sub(r'(pageNumber=\d+)', f'pageNumber={i}', url)
                x_path_body = 'div.N6hSDI.row'
                x_path_nav_page = 'div.shopee-page-controller'
            else:
                new_url = sub(r'(page=\d+)', f'page={i-1}', url)
                x_path_body = 'section.shopee-search-item-result'
                x_path_nav_page = 'nav.shopee-page-controller'
            
            driver.get(new_url)
            

            if not pass_tracking(driver=driver, link=new_url, list_css=[x_path_nav_page], timewait=20, loops=0):
                if not login_bool:
                    time.sleep(5)
                    if check_login(driver, login_auto=False):
                        login_bool = True
                
                if not captcha_bool:
                    time.sleep(5)
                    if check_captcha(driver):
                        time.sleep(60)
                        captcha_bool = True
                
                driver.get(new_url)


            # Scroll to load more content
            for _ in range(10):
                scroll_origin = ScrollOrigin.from_viewport(1920 // 2, 1080 // 2)
                ActionChains(driver).scroll_from_origin(scroll_origin, 0, 250).perform()
                time.sleep(random.uniform(0.1, 2))
                
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            links, titles = extract_links(soup, content_keywords, skip_content, method)
            check_new = []
            # Add unique links to the list
            for title, link in zip(titles, links):
                if title not in all_titles:
                    all_titles.append(title)
                    all_links.append(link)
                    check_new.append(link)
            if not check_new:
                break
            

            print(f"Total found {len(all_titles)} items")

    
    except Exception as e:
        print(f"Error in Processing Get Links: {e}")
    
    finally:
        folder_with_id = f"data/{id}"
        if not exists(folder_with_id):
            makedirs(folder_with_id)
    
        path_to_save = f"{folder_with_id}/{method}_raw_links_{id}.txt"
        savetxt(path_to_save, all_links, fmt='%s', encoding='utf-8')
        return driver
