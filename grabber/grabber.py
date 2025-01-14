from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import requests
import time
import sys
import os
from datetime import datetime

# 目标页面
url = "https://www.weatherbug.com/traffic-cam/victoria-hong-kong-ch"
# 保存的json文件
json_file = "hongkong.json"
# 保存的图片文件夹
image_folder = "hongkong"
# 超时时间
load_time = 15
# 是否保存json文件
save_json = True
# 是否从json文件读取链接
load_json = True
# 在文件开头添加全局变量
saved_image_urls = set()

def create_driver():
    """创建并配置浏览器驱动"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--silent')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)

def grab_traffic_cameras_links(url, load_time=15):
    """Grab all camera links in the homepage"""
    driver = create_driver()
    camera_links = []

    driver.get(url)
    
    wait = WebDriverWait(driver, load_time)

    page_height = driver.execute_script("return document.body.scrollHeight")
    
    time.sleep(load_time//5)
    print("Search Big Camera...")
    while True: 
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class^='weatherTrafficLargeCameraView__Container-sc']")))
        main_cameras = driver.find_elements(By.CSS_SELECTOR, "div[class^='weatherTrafficLargeCameraView__Container-sc']")
        flag = False
        for container in main_cameras:
            try:
                link = container.find_element(By.CSS_SELECTOR, "a[href^='traffic-cam']")
                href = link.get_attribute("href")
                name = container.find_element(By.CSS_SELECTOR, "div[class*='CamNameContainer']").text
                location = container.find_element(By.CSS_SELECTOR, "div[class*='CamLocationContainer']").text
                print(f"Name: {name}")
                print(f"Location: {location}")
                print(f"Link: {href}")
                camera_links.append([href, name, location])
                flag = True
                break
            except Exception as e:
                continue
        if flag:
            break
    
    
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[class^='cameraThumbnail__Container']")))
    thumbnail_cameras = driver.find_elements(By.CSS_SELECTOR, "a[class^='cameraThumbnail__Container']")

    if thumbnail_cameras:
        for index, camera in enumerate(thumbnail_cameras, 1):
            try:
                href = camera.get_attribute("href")
                name = camera.find_element(By.CSS_SELECTOR, "div[class*='CamNameContainer']").text
                location = camera.find_element(By.CSS_SELECTOR, "div[class*='CamLocationContainer']").text
                
                print(f"\nThumbnail Camera {index}:")
                print(f"Name: {name}")
                print(f"Location: {location}")
                print(f"Link: {href}")
                camera_links.append([href, name, location])
            except Exception as e:
                continue

    print("grag camera links done")
    driver.close()
    driver.quit()
    print("close driver")
    return camera_links

def grab_picture(link, name):
    """grab picture of the camera"""
    print(f"grab picture of {name} start")
    
    # 创建图片保存目录
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    
    # 记录已保存的图片URL
    try:
        driver = create_driver()
        driver.get(link)
        
        while True:
            try:
                # 查找图片元素，使用链接前缀定位
                img_element = driver.find_element(
                    By.XPATH, 
                    "//img[contains(@src, 'https://ie.trafficland.com/v2.0/')]"
                )
                img_url = img_element.get_attribute('src')
                
                # 检查是否是新图片
                global saved_image_urls
                if img_url in saved_image_urls:
                    print(f"grab picture of {name} failed: {img_url} already saved")
                    time.sleep(10)
                    continue
                else:
                    print(f"grab picture of {name} start: {img_url}")
                # 下载图片
                try:
                    # 获取当前时间
                    current_time = datetime.now()
                    date_str = current_time.strftime("%Y%m%d")
                    time_str = current_time.strftime("%H%M%S")
                    
                    # 清理名称，移除非法字符
                    clean_name = "".join(x for x in name if x.isalnum() or x in [' ', '-', '_'])
                    clean_name = clean_name.replace(' ', '_')
                    
                    # 构建文件名
                    filename = f"{clean_name}_{date_str}_{time_str}.jpg"
                    filepath = os.path.join(image_folder, filename)
                    
                    # 下载图片
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        print(f"grab picture of {name} done: {filename}")
                        saved_image_urls.add(img_url)
                        # success
                        return True
                    else:
                        print(f"grab picture of {name} failed: {img_url}")
                        time.sleep(5)
                        return False

                except Exception as e:
                    print(f"grab picture of {name} failed: {str(e)}")
                    return False
                
            except Exception as e:
                print(f"grab picture of {name} failed: {str(e)}")
                return False
                
    except Exception as e:
        print(f"grab picture of {name} failed: {str(e)}")
        return False

    finally:
        try:
            driver.close()
            driver.quit()
            print(f"grab picture of {name} done")
        except:
            pass

def save_camera_links(camera_links):
    """save camera links to json file"""
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(camera_links, f, ensure_ascii=False, indent=4)
        print(f"save json to {json_file}")
        return True
    except Exception as e:
        print(f"save json failed: {str(e)}")
        return False

def load_camera_links(json_file):
    """load camera links from json file"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            camera_links = json.load(f)
        print(f"load json from {json_file}")
        return camera_links
    except FileNotFoundError:
        print(f"load json failed: {json_file} not found")
        return []
    except Exception as e:
        print(f"load json failed: {str(e)}")
        return []

if __name__ == "__main__":
    load_time = 15
    if load_json:
        camera_links = load_camera_links(json_file)
    else:
        while True:
            try:
                camera_links = grab_traffic_cameras_links(url, load_time)
                break;
            except Exception as e:
                load_time += 1
                time.sleep(5)
                continue;
    
    if save_json:
        save_camera_links(camera_links)

    for camera in camera_links: 
        grab_picture(camera[0], camera[1])
        time.sleep(30)

    print(f'total cameras: {len(camera_links)}')


