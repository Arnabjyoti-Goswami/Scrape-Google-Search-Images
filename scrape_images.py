import os
import socket
import time
import urllib

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

nb_dir = os.path.abspath("")


def generate_google_images_url(query):
    base_url = "https://www.google.com/search"

    query = query.replace(" ", "+")

    # In a Google search URL, the "tbm" parameter stands for "To Be Matched." It is used to specify the type of search you want to perform. For Google Images search, you typically set the "tbm" parameter to "isch," which is short for "Images Search."
    params = {
        "q": query,
        "tbm": "isch",
    }
    query_string = "&".join(
        [f"{key}={value}" for key, value in params.items()]
    )  # iterates through the key-value pairs in the params dictionary and creates a list of strings in the format "key=value" for each pair. query_string is constructed by joining the list of strings created in this step with the "&" character. This creates a query string that can be appended to the base URL.
    url = f"{base_url}?{query_string}"
    return url


def make_folder(query):
    """
    Make a different folder for each query
    """
    folder_name = query
    if not os.path.isdir(folder_name):
        os.makedirs(folder_name)

    folder_dir = os.path.join(nb_dir, folder_name)
    return folder_dir


def init_driver(url, headless=False):
    """
    Initialize the driver and return it
    """
    if headless:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
    else:
        driver = webdriver.Chrome()

    driver.get(url)

    return driver


def find_total_images(page_html):
    """
    Returns the total number of images on the driver's current page, calculated using beautiful soup
    """
    attribute_name = "class"
    attribute_value = "islir"
    attribute_dict = {attribute_name: attribute_value}

    doc = BeautifulSoup(page_html, "html.parser")
    containers = doc.findAll("div", attribute_dict)
    num_images = len(containers)
    print("Total number of images on the webpage is: ", num_images)

    return num_images


def required_scroll(driver, num_images):
    """
    Calculate the number of times the driver needs to scroll to the bottom of the page to load all the required number of images
    """
    scroll_pause_time = 5
    last_count = 0
    num_scrolls = 0

    while True:
        current_count = find_total_images(page_html=driver.page_source)

        if current_count >= num_images:
            break

        # If the count of images remains the same for consecutive scrolls, break the loop
        if current_count == last_count:
            break

        last_count = current_count

        # Scroll to the bottom of the page
        script = "window.scrollTo(0, document.body.scrollHeight);"
        driver.execute_script(script)

        # Wait for some time to let the images load
        time.sleep(scroll_pause_time)

        num_scrolls += 1

    # Scroll back to the top of the page after all the images have been loaded
    script = "window.scrollTo(0, 0);"
    driver.execute_script(script)

    print("Number of scrolls that were required: ", num_scrolls)

    return driver


def download_image(url, dir_path, num):
    """
    file.write(response.content) method using requests, just skips a lot of files in the cases where image preview couldn't be loaded in the specified maximum time (due to internet speed or internet firewall), because in most cases the preview images are just gstatic images that can't be saved that way.
    So, this method is used.
    """
    download_timeout = 3
    filename = f"image{num}.jpg"
    filepath = os.path.join(dir_path, filename)
    try:
        with urllib.request.urlopen(url, timeout=3) as response, open(
            filepath, "wb"
        ) as f:
            f.write(response.read())
            print(f"Image {num} downloaded successfully! URL: ({url})")
    except urllib.error.URLError as e:
        if isinstance(e.reason, socket.timeout):
            print(
                f"Timeout of {download_timeout} seconds reached while trying to download image {num}, will move onto the next one"
            )
        else:
            print(f"Failed to download image {num} due to error {e}")
    except Exception as e:
        print(f"Failed to download image {num} due to error {e}")


def download_all_images(
    driver,
    folder_dir,
    num_images,
    low_res_upon_timeout=True,
    safe_search="ON",
    timeout_time=5,
):
    # If you need to turn off safe search to view the results in the browser, then you will need to manually pass the captcha for being not a robot in this wait_safe_search duration number of seconds of time. Go to the safe search drop down box and set it to off. Then click on 'I am not a robot' and solve the captcha.
    if safe_search == "OFF":
        wait_safe_search = 30
        time.sleep(wait_safe_search)

    for i in range(1, num_images):
        # Every 25 images, there is a 'related searches' element. So skip it.
        if i % 25 == 0:
            continue

        # Find the preview image url as we will compare it with the actual image url later
        preview_image_element_xpath = f"/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div/div[1]/div[1]/span/div[1]/div[1]/div[{i}]/a[1]/div[1]/img"
        preview_image_element = driver.find_element(
            "xpath", preview_image_element_xpath
        )
        preview_image_url = preview_image_element.get_attribute("src")

        preview_image_element_container_xpath = f"/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div/div[1]/div[1]/span/div[1]/div[1]/div[{i}]"
        preview_image_element_container = driver.find_element(
            "xpath", preview_image_element_container_xpath
        )
        preview_image_element_container.click()

        # Make a while loop so that the program waits a maximum amount of a specified number of seconds so that the actual image url may be loaded
        start_time = time.time()
        while True:
            # Wait for the image popup on the right side to load
            time.sleep(0.4)
            image_element_xpath = f"/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/c-wiz/div/div/div/div/div[3]/div[1]/a/img[1]"
            image_element = driver.find_element("xpath", image_element_xpath)
            image_url = image_element.get_attribute(
                "src"
            )  # this is the actual fully loaded image url after clicking on an element

            if (
                image_url != preview_image_url
            ):  # if the urls became different, break the loop
                break

            else:  # else keep running the code inside this else: block in each iteration of the loop until 5 seconds have passed from the beginning. This is a far more efficient approach compared to making the program wait for a specified same amount of time for loading each image, even though some images may not take so long to load
                current_time = time.time()
                if current_time - start_time > timeout_time:
                    if low_res_upon_timeout:
                        print(
                            "Timeout! Will download the lower resolution image and move onto the next one"
                        )
                        image_url = preview_image_url
                    else:
                        print(
                            "Timeout! Will not download the lower resolution image and move onto the next one"
                        )
                    break

        download_image(image_url, folder_dir, i)


def scrape_images(query, num_images, headless_browser=False):
    """
    Final function that calls all the previous functions to scrape all images related to the query
    """
    url = generate_google_images_url(query)
    folder_dir = make_folder(query)

    driver = init_driver(
        headless=headless_browser,
        url=url,
    )
    driver = required_scroll(driver, num_images)

    # Uncomment and set headless to False to view the driver's browser to see if any xpath change is there compared to the browser you used to inspect the elements' xpaths
    # time.sleep(100)

    download_all_images(
        driver=driver,
        num_images=num_images,
        folder_dir=folder_dir,
        low_res_upon_timeout=True,
        safe_search="ON",
        timeout_time=5,
    )

    driver.quit()


if __name__ == "__main__":
    query = input("Enter your google image search query: ")

    num_images = input("Enter the number of images you want to download: ")
    try:
        num_images = int(num_images)
    except Exception as e:
        print(
            "An error occurred while trying to convert the input number of images into an integer"
        )
        quit()

    scrape_images(
        query="cats",
        num_images=40,
        headless_browser=False,
    )
