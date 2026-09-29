import numpy as np
import pandas as pd
import requests
import re
from os import listdir
import urllib
import io
from io import StringIO
import matplotlib.pyplot as plt


raiz = "https://datos.madrid.es/"
url_diciembre_24 = "dataset/210104-0-multas-circulacion-detalle/resource/210104-15-multas-circulacion-detalle-csv/download/210104-15-multas-circulacion-detalle-csv.csv" 
url = raiz + url_diciembre_24.lstrip("/")


response = requests.get(url)
if response.status_code == 200:
    print(response.url)


# Accedemos al texto 
content = io.StringIO(response.text)
multas = pd.read_csv(content, sep =';', encoding = 'latin1')
print(multas.head())