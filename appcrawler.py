# -- coding: utf-8 --**
import requests
import socket
import urllib3
import os
from bs4 import BeautifulSoup
import pandas
import configparser
import datetime

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
# import warnings
# from urllib import parse
# import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# driver_path = "chromedriver_win32/chromedriver.exe"
request_url = "https://www.wandoujia.com/search"
# notice that cookie can be valid for an hour. GET NEW ONE in explorer if necessary
cookie = "ctoken=jaHcMB54XeAwsUyLo-2QgaJH; sid=23650600167359063906180277201673; sid.sig=pJD03RTyyhLzzNH3OAHHLn3K2zD1jP-fSb8kqfQB18g; _bl_uid=e2lR6cjCuC34R7njCmvd2k0m9075; seo_ch=BAIDU; track_id=aligames_platform_ug_1673590640019_fa16fd20-f402-4ed9-abc7-99d033c53d8c; _ga=GA1.2.1712183619.1673590640; uuid=c61e7bf5-b321-406d-a97b-5ab3261e9ed6; _pwid=69439180167931910986705689497463; Hm_lvt_c680f6745efe87a8fabe78e376c4b5f9=1679319110; cna=qyeGHOoAihACAXOcjMXs4PkG; _gid=GA1.2.1480841650.1679489639; xlly_s=1; wdj_source=direct; Hm_lpvt_c680f6745efe87a8fabe78e376c4b5f9=1680697127; _uToken=T2gAv2xV8vj_3K_M6cwBaz8vpmiCLlgFhEh-ofFz8qI-34mOjflj5F_iOGQiskMev8U=; x5sec=7b22617365727665723b32223a22616439386361393865626630656461373635323634366263356437306664663643502f4f74614547454f69456949366d784d2b556a4145777a7175312f77524141773d3d227d; isg=BBERT8m6EQ34IH0sAwXmQnViIB2rfoXwEr3-qvOmbVj3mjDsO8-jwRX4PG58lB0o"
my_headers = {
    'User-Agent':
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 "
        "Safari/537.36 Edg/111.0.1661.44 ",
    # 'User-Agent': 'PostmanRuntime/7.29.2',
    'Accept': "*/*",
    'Cookie': cookie,
    'Accept-Encoding': "gzip, deflate, br",
    'Connection': "close",
}


# another_version_format_date, e.g. 2023年1月1日
# notified_version_date_str, e.g. "20230101"
def date_calculation(another_version_format_date, notified_version_date_str):
    notified_version_format_date = notified_version_date_str[0:4] + "年" + notified_version_date_str[
                                                                          4:6] + "月" + notified_version_date_str[
                                                                                       6:8] + "日"
    another_version_date = datetime.datetime.strptime(another_version_format_date, "更新时间：%Y年%m月%d日")
    notified_version_date = datetime.datetime.strptime(notified_version_format_date, "%Y年%m月%d日")
    calc_res = another_version_date - notified_version_date
    return calc_res.days


# size_str, e.g. "200MB"
def size_compare(size_str):
    print(size_str)
    size_unit = size_str[-2:]
    size_value = float(size_str[:-2])
    if size_unit == "KB":
        size_value = size_value / 1024
    elif size_unit == "GB":
        size_value = size_value * 1024
    elif size_unit == "MB":
        size_value = size_value
    if size_value > 250:
        return False
    else:
        return True


def notified_list_load(excel_file_name):
    notified_app_info_list = []
    df = pandas.read_excel(excel_file_name, engine="openpyxl")
    df.fillna("缺失", inplace=True)
    # Not Necessary to Filter the Resources
    filtered_res = df.loc[df["应用来源"] != "缺失"]
    res_cnt = len(filtered_res)
    # name, version, developer
    for i in range(0, res_cnt):
        app_info_item = [filtered_res.iloc[i]["应用名称"], filtered_res.iloc[i]["应用版本"], filtered_res.iloc[i]["应用开发者"]]
        notified_app_info_list.append(app_info_item)
    return notified_app_info_list


# "/search" is prohibited according to the robots.txt
def get_download_url_of_app(app_name, dev_company):
    # param_key_value = parse.quote(app_name)
    param_key = {"key": app_name}
    # set "verify=False" for not verifying the ca
    redirection_request = requests.get(url=request_url, headers=my_headers, params=param_key, verify=False)
    # include a redirection
    app_search_res = requests.get(url=redirection_request.url, headers=my_headers)
    # reset encoding mode for Chinese Characters
    app_search_res.encoding = app_search_res.apparent_encoding
    # Parsing html for APP information
    app_search_parser_result = BeautifulSoup(app_search_res.text, "html.parser")
    # print(app_search_parser_result.prettify())
    # Check & Update the Cookie if Expired
    # The Element "<title></title>" can somehow used as a fingerprint,
    # Cuz the Authentication Page doesn't Contain ANY "<title></title>
    if not app_search_parser_result.select("title"):
        print("[info]: Need To Renew the Cookie!")
        return "Cookie Expired"
    cnt = 3
    flag = False
    searched_app_name = ""
    app_page_url = ""
    developer = ""
    for search_result_item in app_search_parser_result.find_all(attrs={"class": "search-item search-searchitems"}):
        # print(search_result_item)
        if not cnt:
            break
        app_info = search_result_item.select('a')[-1]
        # Judge whether it's the True APP By Compared the DEVELOPER
        app_page = requests.get(url=app_info.attrs["href"], headers=my_headers, verify=False)
        app_page_parser_result = BeautifulSoup(app_page.text, "html.parser")
        developer = app_page_parser_result.find(attrs={"class": "dev-sites"}).get_text()
        app_name_of_cur_item = app_info.attrs["data-app-name"]
        # Logs
        print("********************************")
        print("Name of Possible App: ", app_name_of_cur_item)
        print("Developer of Possible APP: ", developer)
        if dev_company == "缺失" and app_name_of_cur_item == app_name:
            flag = True
            searched_app_name = app_name_of_cur_item
            app_page_url = app_info.attrs["href"]
            print("********************************")
            print("\n> > > > >Found Possible APP< < < < <\n")
            break
        elif app_name_of_cur_item == app_name or developer in dev_company or dev_company in developer:
            flag = True
            searched_app_name = app_name_of_cur_item
            app_page_url = app_info.attrs["href"]
            print("********************************")
            print("\n> > > > >Found Possible APP< < < < <\n")
            break
        cnt -= 1
    if not flag:
        print("********************************")
        print("[info]: Failed to Find APP: %s" % app_name)
        return False
    else:
        return searched_app_name, app_page_url, developer


def certain_versions_download_url(searched_app_name, batch_info, main_download_url, developer, notified_app_name, notified_version, dev_company):
    app_history_versions_download_url = main_download_url + "/history"
    app_history_versions_download_page = requests.get(url=app_history_versions_download_url, headers=my_headers,
                                                      verify=False)
    app_history_versions_download_page.encoding = app_history_versions_download_page.apparent_encoding
    soup_parser_result = BeautifulSoup(app_history_versions_download_page.text, "html.parser")
    # Rare Exception: Old Version List of Some APP Doesn't Exist
    # E.g., "PICOOC" in ""20210122-10.xlsx"
    has_old_version_list = soup_parser_result.find(attrs={"class": "old-version-list"})
    if has_old_version_list is None:
        print("[info]: Old Version List Not Exist: %s" % searched_app_name)
        return False
    # NOTICE HERE:
    # The block of latest version is different from any other versions' block, so simply EXCLUDE it from the list
    # The Latest Version Should Be SEPARATELY DownLoad if Necessary,
    app_versions_list = has_old_version_list.select("li")[1:]
    cur_index = 0
    ##############################
    # dict: {version: ...,
    #        download_url: ...}
    ##############################
    # the version notified
    notified_version_info = {}
    # the version next to the notified one but modified
    modified_version_info = {}
    flag = False
    for app_version_item in app_versions_list:
        item_version_info = app_version_item.select('a')[1]
        if item_version_info.attrs["data-app-vname"] == str(notified_version):
            flag = True
            # Examine The size
            item_version_size_str = app_version_item.select('a')[0].find("span").get_text()
            if not size_compare(item_version_size_str):
                print("[info]: Out of Size, App: %s" % searched_app_name)
                with open("appSamples/app_out_of_size.txt", mode='a') as f:
                    info_log = "[info]: Out of Size, App: %s\n" % searched_app_name
                    f.write(info_log)
                return False
            # notified version info dict
            notified_version_download_page_url = item_version_info.attrs["href"]
            notified_version_info["version"] = str(notified_version)
            notified_version_info["download_page"] = notified_version_download_page_url
            # modified version info dict
            tmp_static_period_len = 14
            tmp_index = cur_index
            date_flag = False
            notified_date_str = batch_info.split("-")[0]
            while not date_flag:
                tmp_index -= 1
                tmp_version_download_page_url = app_versions_list[tmp_index].select('a')[1].attrs["href"]
                tmp_version_download_page = requests.get(url=tmp_version_download_page_url, headers=my_headers, verify=False)
                tmp_version_download_page.encoding = "utf-8"
                tmp_version_download_page_soup_parser_result = BeautifulSoup(tmp_version_download_page.text, "html.parser")
                update_time = tmp_version_download_page_soup_parser_result.find(attrs={"class": "num-list"}).find(attrs={"class": "update-time"}).get_text()
                update_time_str = update_time[0:update_time.index("日")+1]
                # print(update_time_str)
                if date_calculation(update_time_str, notified_date_str) >= tmp_static_period_len:
                    date_flag = True
            modified_version_download_page_url = app_versions_list[tmp_index].select('a')[1].attrs["href"]
            modified_version_info["version"] = app_versions_list[tmp_index].select('a')[1].attrs["data-app-vname"]
            modified_version_info["download_page"] = modified_version_download_page_url
            break
        cur_index += 1
    if not flag:
        print("[info]: Failed to Find the APK of Notified version: %s" % searched_app_name)
        return False
    else:
        if developer != dev_company:
            with open("appSamples/Exception_Developer.txt", mode='a', encoding='gb18030') as f1:
                f1.write("批次: %s, App名: %s   %s --> %s\n" % (batch_info, searched_app_name, dev_company, developer))
        if notified_app_name != searched_app_name:
            with open("appSamples/Exception_AppName.txt", mode='a', encoding='gb18030') as f2:
                f2.write("批次: %s, %s --> %s\n" % (batch_info, notified_app_name, searched_app_name))
        return notified_version_info, modified_version_info


# Check App FileName to Avoid Repeatedly Downloading the APK of Same Version,
# In case of Cookie Expiration While Crawling A Single List
# Use Stream Mode Download
def download(app_name, batch_info, notified_version_info_dict, modified_version_info_dict):
    samples_dir = "appSamples"
    sub_dir = batch_info + "//" + app_name
    app_dir = samples_dir + "//" + sub_dir
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
    # notified version
    notified_version_full_name = app_name + "_" + notified_version_info_dict["version"] + ".apk"
    notified_version_download_page_url = notified_version_info_dict["download_page"]
    notified_version_path = app_dir + "//" + notified_version_full_name
    if os.path.exists(notified_version_path):
        print("[info]: Already Downloaded the Certain Version, APP's Full Name: %s" % notified_version_full_name)
    else:
        notified_version_download_page = requests.get(url=notified_version_download_page_url, headers=my_headers,
                                                      verify=False)
        notified_version_download_page.encoding = notified_version_download_page.apparent_encoding
        notified_version_download_page_soup_parser_result = BeautifulSoup(notified_version_download_page.text,
                                                                          "html.parser")
        notified_version_download_url = \
            notified_version_download_page_soup_parser_result.find(attrs={"class": "normal-dl-btn"}).attrs["href"]
        # print(notified_version_download_url)
        notified_version_response = requests.get(url=notified_version_download_url, headers=my_headers, stream=True)
        with open(notified_version_path, mode='wb') as f:
            for n_chunk in notified_version_response.iter_content(chunk_size=2048):
                f.write(n_chunk)

    # modified version
    modified_version_full_name = app_name + "_" + modified_version_info_dict["version"] + ".apk"
    modified_version_download_page_url = modified_version_info_dict["download_page"]
    modified_version_path = app_dir + "//" + modified_version_full_name
    if os.path.exists(modified_version_path):
        print("[info]: Already Downloaded the Certain Version, APP's Full Name: %s" % modified_version_full_name)
    else:
        modified_version_download_page = requests.get(url=modified_version_download_page_url, headers=my_headers,
                                                      verify=False)
        modified_version_download_page.encoding = modified_version_download_page.apparent_encoding
        modified_version_download_page_soup_parser_result = BeautifulSoup(modified_version_download_page.text,
                                                                          "html.parser")
        modified_version_download_url = \
            modified_version_download_page_soup_parser_result.find(attrs={"class": "normal-dl-btn"}).attrs["href"]
        modified_version_response = requests.get(url=modified_version_download_url, headers=my_headers, stream=True)
        with open(modified_version_path, mode='wb') as f:
            for m_chunk in modified_version_response.iter_content(chunk_size=2048):
                f.write(m_chunk)

    # privacy compliance policy
    # can be download through either of the url
    privacy_compliance_policy_file = app_dir + "//" + app_name + "_隐私政策.txt"
    if os.path.exists(privacy_compliance_policy_file):
        print("[info]: Already Downloaded the Privacy Compliance Policy, APP Name: %s" % app_name)
    else:
        try:
            modified_version_download_page = requests.get(url=modified_version_download_page_url, headers=my_headers,
                                                          verify=False)
            modified_version_download_page.encoding = modified_version_download_page.apparent_encoding
            modified_version_download_page_soup_parser_result = BeautifulSoup(modified_version_download_page.text,
                                                                              "html.parser")
            privacy_compliance_policy_url = modified_version_download_page_soup_parser_result.find(attrs={"class": "privacy-link"}).attrs["href"]
            # privacy_compliance_policy_resp = requests.get(privacy_compliance_policy_url, verify=False)
            _ = requests.get(privacy_compliance_policy_url, verify=False)
            # privacy_compliance_policy_resp.encoding = privacy_compliance_policy_resp.apparent_encoding
            # privacy_compliance_policy = BeautifulSoup(privacy_compliance_policy_resp.text, "html.parser")
            with open(privacy_compliance_policy_file, mode='w', encoding="utf-8") as f:
                f.write(privacy_compliance_policy_url)
        except Exception as e:
            print(type(e))
            print("[Warn]: Something Go Wrong With the URL for Privacy Compliance Policy, app: %s" % app_name)


list_dir = "lists" + "//"
for root, dirs, files in os.walk(list_dir):
    for list_file_item in files:
        # For Adjustment —— Sequence Number of Batch
        if int(list_file_item.split(".")[0].split("-")[1]) < 14:
            continue
        if int(list_file_item.split(".")[0].split("-")[1]) != 14:
            break
        print("Batch Info:  %s" % list_file_item.split(".")[0])
        cur_batch_notified_app_info_list = notified_list_load(os.path.join(root, list_file_item))
        batch = list_file_item.split(".")[0]
        for notified_app_item in cur_batch_notified_app_info_list:
            print("————————————————————————————————————————————————————————————————————")
            print("Searching For:  %s ...." % notified_app_item[0])
            print("Developer:  %s" % notified_app_item[2])
            searched_app_info = get_download_url_of_app(notified_app_item[0], notified_app_item[2])
            if searched_app_info:
                if searched_app_info != "Cookie Expired":
                    print("App Name In Search Result:\n   ", searched_app_info[0])
                    print("App Download URL:\n   ", searched_app_info[1])
                    target_app_info_pairs = certain_versions_download_url(searched_app_info[0], batch, searched_app_info[1], searched_app_info[2], notified_app_item[0], notified_app_item[1], notified_app_item[2])
                    if not target_app_info_pairs:
                        continue
                    else:
                        print("Target URL Pairs: ")
                        print("   version: %s, download_page: %s" % (
                            target_app_info_pairs[0]["version"], target_app_info_pairs[0]["download_page"]))
                        print("   version: %s, download_page: %s" % (
                            target_app_info_pairs[1]["version"], target_app_info_pairs[1]["download_page"]))
                        download(searched_app_info[0], batch, target_app_info_pairs[0], target_app_info_pairs[1])
                else:
                    break
        print("————————————————————————————————————————————————————————————————————\n\n")

# def search_for_app(app_name):
#     cookie_dict = {"name": "cookie", "value": cookie}
#     # cookie_list = cookie.split("; ")
#     # for item in cookie_list:
#     #     s3 = item.split("=")
#     #     key = s3[0]
#     #     value = s3[1]
#     #     cookie_dict[key] = value
#
#     # browser.add_cookie(cookie_dict)
#     browser.get(target_url)
#     # input
#     # wd = browser.find_element(by=By.NAME, value='wd')
#     # wd.send_keys(app_name)
#     input_location = browser.find_element(by=By.NAME, value='key')
#     input_location.send_keys(app_name)
#
#     # search
#     search_location = browser.find_element(by=By.ID, value='j-search-btn')
#     search_location.click()
#     # wd.send_keys(Keys.ENTER)
#     browser.implicitly_wait(10)
#
#
# my_option = webdriver.ChromeOptions()
# # my_option.headless = True
# my_option.add_argument(
#     'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36')
# my_option.add_experimental_option('excludeSwitches', ['enable-automation'])  # Developer Mode
# browser = webdriver.Chrome(executable_path=driver_path, options=my_option)
# browser.wait = WebDriverWait(browser, 10)
# search_for_app("1")
