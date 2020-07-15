'''Translate Module'''

import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep

now_path = os.path.dirname(os.path.abspath(__file__))
driver_url = {'linux':now_path + '/chromedriver_Linux',
              'mac':now_path + '/chromedriver',
              'win64':now_path + '/chromedriver.exe',
              'win32':now_path + '/chromedriver.exe'}

lang_button_path = {'RU':'//*[@id="dl_translator"]/div[1]/div[4]/div[1]/div[1]/div[1]/div/button[11]', # ロシア
                    'PL':'//*[@id="dl_translator"]/div[1]/div[4]/div[1]/div[1]/div[1]/div/button[10]', # ポーランド
                    'NL':'//*[@id="dl_translator"]/div[1]/div[4]/div[1]/div[1]/div[1]/div/button[9]', # オランダ
                    'IT':'//*[@id="dl_translator"]/div[1]/div[4]/div[1]/div[1]/div[1]/div/button[8]', # イタリア
                    'PT':'//*[@id="dl_translator"]/div[1]/div[4]/div[1]/div[1]/div[1]/div/button[6]', # ポルトガル
                    'ES':'//*[@id="dl_translator"]/div[1]/div[4]/div[1]/div[1]/div[1]/div/button[5]', # スペイン
                    'FR':'//*[@id="dl_translator"]/div[1]/div[4]/div[1]/div[1]/div[1]/div/button[4]', # フランス
                    'DE':'//*[@id="dl_translator"]/div[1]/div[4]/div[1]/div[1]/div[1]/div/button[3]'} # ドイツ



# プラットフォームによって使用するchromdriverを分ける
def current_platform() -> str:
    """Get current platform name by short string."""
    if sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform.startswith('darwin'):
        return 'mac'
    elif (sys.platform.startswith('win') or
          sys.platform.startswith('msys') or
          sys.platform.startswith('cyg')):
        if sys.maxsize > 2 ** 31 - 1:
            return 'win64'
        return 'win32'
    else:
        print('Error: DO NOT SUPPORT OS', file=sys.stderr)
        sys.exit(1)


def traslateBydeepL(input_text, lang='JA'):
    if input_text == '' or input_text == ' ' or input_text == '\n':
        return ''

    # 翻訳用ドライバーをheadless modeで開く
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(driver_url[current_platform()], options=options)

    # DeepLクエリ
    baseURL = "https://www.deepl.com/ja/translator"
    # 返り値
    ret = ''

    # DeepLクエリ送信
    driver.get(baseURL)

    # 多言語対応
    if lang != 'JA':
        choice_button = \
        driver.find_elements_by_xpath('//*[@id="dl_translator"]/div[1]/div[4]/div[1]/div[1]/div[1]/button')[0]
        choice_button.click()
        sleep(1)
        lang_button = driver.find_elements_by_xpath(lang_button_path[lang])[0]
        lang_button.click()

    # 入力窓にテキスト送信
    input_element = driver.find_elements_by_xpath('//*[@id="dl_translator"]/div[1]/div[3]/div[2]/div[1]/textarea')
    input_element[0].send_keys(input_text)

    # 読み込み待ち
    if len(input_text) < 1000:
        sleep(12)
    else:
        sleep(15)

    # 出力窓からテキスト抽出
    output_element = driver.find_elements_by_xpath('//*[@id="dl_translator"]/div[1]/div[4]/div[3]/div[1]/textarea')
    for e in output_element:
        ret += e.get_attribute('value')

    # 翻訳用ドライバー閉じる
    driver.close()

    return ret