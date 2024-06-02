from flask import Flask, redirect, render_template, url_for
from selenium import webdriver
from time import sleep
import json
import os
#data manipulation
import pandas as pd
#Visulation
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

@app.route('/')
def index():
    with open('veriler.json', 'r', encoding='utf-8') as f:
        veriler = json.load(f)
    return render_template('index.html', veriler=veriler)

@app.route('/ilanlar')
def ilanlar():

    options = webdriver.ChromeOptions()
    options.add_argument('executable_path=C:/Users/halit/OneDrive/Masaüstü/chromedriver.exe')

    driver = webdriver.Chrome(options=options)

    hepsiemlak_arama = 'burdur 1+1 kiralık'

    driver.get('https://www.hepsiemlak.com/')

    # Arama
    driver.find_element(By.XPATH, '//*[@id="search-input"]') \
        .send_keys(hepsiemlak_arama)
    driver.find_element(By.XPATH, '//*[@id="__layout"]/div/section[1]/div[1]/div/div/div/div[2]/div[1]/div[1]/button') \
        .click()
    sleep(3)

    # Listeler
    def ilanlaritopla():
        konumlar = []
        fiyatlar = []
        # Değişkenler
        while True:
            s1evfiyat = driver.find_elements(By.XPATH, '//*[*]/div/div[2]/section/div/div/span')
            s1evkonum = driver.find_elements(By.XPATH , '//*[*]/div/div[2]/div[2]/div[1]/section[2]/div/section/div[2]/span[2]')
            for fiyat in s1evfiyat:
                try:
                     # Önce 'TL' ve '\n' karakterlerini kaldırıyoruz
                    temiz_fiyat = fiyat.text.replace("TL", "").replace("\n", "")
                    # Ardından noktaları ve virgülleri uygun şekilde değiştiriyoruz
                    temiz_fiyat = temiz_fiyat.replace(".", "").replace(",", ".")
                    # Son olarak float'a dönüştürüyoruz
                    fiyatlar.append(float(temiz_fiyat))
                except ValueError as e:
                    print(f"Fiyat Dönüştürülemedi: {fiyat.text}. Hata {e}")
            for konum in s1evkonum:
                konumlar.append(konum.text)
            # Sayfa sonuna gelindiğini kontrol et
            # Örneğin, bir sonraki sayfa düğmesi yoksa bu sayfada sona gelinmiş demektir
            sonraki_sayfa_dugmesi = driver.find_element(By.XPATH, '//*[@id="listPage"]/div[2]/div/div/main/div[2]/div/section/div/a[2]')
            if 'disabled' in sonraki_sayfa_dugmesi.get_attribute('class'):
                break
            # Sonraki sayfaya geç
            sonraki_sayfa_dugmesi.click()
        return konumlar , fiyatlar
    konumlar , fiyatlar = ilanlaritopla() 

    dfS = pd.DataFrame(zip(konumlar,fiyatlar),columns=['Konum','Fiyat'])
    dfS.to_json('veriler.json',orient='records')
    
    df = pd.read_json('veriler.json', encoding='utf-8')

    # Yeni verileri eski verilere ekleyerek güncelle
    df = pd.concat([df, dfS], ignore_index=True)
    
    # with open('veriler.json','r',encoding='utf-8') as f:
    #     df=pd.read_json(f)
    
    ortalamafiyat = df.groupby('Konum')['Fiyat'].mean()
    ortalama_fiyatlar_dict = ortalamafiyat.to_dict()
    
    # JSON dosyasına ortalama fiyatları yaz
    with open('veriler.json', 'w', encoding='utf-8') as f:
        json.dump(ortalama_fiyatlar_dict, f, ensure_ascii=False, indent=4)
    
    return redirect(url_for('index'))


if __name__ == '__main__':
     # Eğer veriler.json dosyası yoksa, oluştur
    if not os.path.exists('veriler.json'):
        with open('veriler.json', 'w') as f:
            f.write('[]')  # Boş bir JSON array oluştur
    app.run(debug=True , threaded=True)
