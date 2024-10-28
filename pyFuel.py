#https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti
#https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv
#https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv

import requests
import tempfile

PREZZI = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
ANAGRAFICA = "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv"
IMAGE_PATH = "/home/andrea/Documenti/personale/pyFuel/img/"

DEBUG = 1

def printDebug (stringa):
    if (DEBUG == 1):
        print("###   ",stringa,"   ###")

def getDataFromMimit (URL, filename):
    response = requests.get(URL)
    with open(filename, mode="wb") as file:
        file.write(response.content)

def readFile(filename):
    lines = []
    with open(filename, 'r') as file:
        lines = list(file)

    extraction_date = lines[0] # save the extraction date
    print(extraction_date[:-1])
    lines.pop(0) # delete the first row

    for i in range (0, len(lines)):
        lines[i]=lines[i][:-1] # remove the new line character

    field_names = []
    field_names = lines[0].split(';')
    printDebug (field_names)

    dataset = []
    for i in range (1, len(lines)):
        row = []
        row = lines[i].split(';')
        single_data = {}
        for j in range (0, len(field_names)):
            single_data[field_names[j]] = row[j]
        dataset.append(single_data)
    
    return dataset

def decodeSelf (stringa):
    if stringa == "1":
        return "Self-Service"
    else:
        return "Servito"


tmpprezzi = tempfile.NamedTemporaryFile(prefix="pyFuelPrezzi_", suffix=".csv")
tmpanag = tempfile.NamedTemporaryFile(prefix="pyFuelAnag_", suffix=".csv")

getDataFromMimit (PREZZI, tmpprezzi.name)
getDataFromMimit (ANAGRAFICA, tmpanag.name)


import time
time.sleep(1)

anagrafiche = []
anagrafiche = readFile (tmpanag.name)
prezzi = [] 
prezzi = readFile (tmpprezzi.name)

printDebug("Numero di anagrafiche acquisite: " + str(len(anagrafiche)))
printDebug("Numero di prezzi acquisiti: " + str(len(prezzi)))

from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="a.alfieri@gmail.com")
print("Insert your address")
address = input()
#address = "via ludovico grossi, mantova"
location = geolocator.geocode(address, addressdetails=True)

printDebug(location.raw)
printDebug("latitude " + location.raw['lat'])
printDebug("longitude " + location.raw['lon'])

from geopy import distance
print("Enter the radius of the area to search")
radius = eval(input())
#radius = 5

start_location = (eval(location.raw['lat']), eval(location.raw['lon']))
near_fuel = []
for i in range (0, len(anagrafiche)):
    fuel_location = {}
    fuel_location['idImpianto'] = anagrafiche[i]['idImpianto']
    fuel_location['Bandiera'] = anagrafiche[i]['Bandiera']
    fuel_location['Indirizzo'] = anagrafiche[i]['Indirizzo']
    fuel_location['Comune'] = anagrafiche[i]['Comune']
    fuel_location['Provincia'] = anagrafiche[i]['Provincia']
    fuel_location['Latitudine'] = anagrafiche[i]['Latitudine']
    fuel_location['Longitudine'] = anagrafiche[i]['Longitudine']
    #printDebug (fuel_location)
    try:
        float(fuel_location['Latitudine'])
        float(fuel_location['Longitudine'])
        fuel_distance = distance.distance(start_location, (fuel_location['Latitudine'], fuel_location['Longitudine'])).km 
        if (fuel_distance < radius):
            near_fuel.append (fuel_location)
    except ValueError:
        continue

import folium
import webbrowser

loc = [location.raw['lat'], location.raw['lon']] 
map = folium.Map(location=loc, tiles="OpenStreetMap")

import sys

min_gasolio = sys.maxsize
min_benzina = sys.maxsize
for i in range (0, len(near_fuel)):
    for j in range (len(prezzi)):
        if prezzi[j]['idImpianto'] == near_fuel[i]['idImpianto']:
            if (prezzi[j]['descCarburante'] == 'Gasolio' and eval(prezzi[j]['prezzo']) < min_gasolio):
                min_gasolio = eval(prezzi[j]['prezzo'])
                printDebug(prezzi[j]['idImpianto'] +" "+ near_fuel[i]['idImpianto'] + " " + str(prezzi[j]['prezzo']))
            if (prezzi[j]['descCarburante'] == 'Benzina' and eval(prezzi[j]['prezzo']) < min_benzina):
                min_benzina = eval(prezzi[j]['prezzo'])
        
printDebug ("Gasolio minimo " + str(min_gasolio))
printDebug ("Benzina minima " + str(min_benzina))

for i in range (0, len(near_fuel)):    
    flg_green = 0    
    html = "<p>"
    html += near_fuel[i]['idImpianto'] + " <b>" + near_fuel[i]['Bandiera'] + "<img src = \"" + IMAGE_PATH + near_fuel[i]['Bandiera']+".png\" width =\"30\">" + "</b><br>"
    html += near_fuel[i]['Indirizzo'] + " " + near_fuel[i]['Comune'] + " " + near_fuel[i]['Provincia']
    html += "</p>"
    for j in range (len(prezzi)):
        flg_minimum = 0
        if prezzi[j]['idImpianto'] == near_fuel[i]['idImpianto']:
            if (prezzi[j]['descCarburante'] == 'Gasolio' and eval(prezzi[j]['prezzo']) == min_gasolio):
                flg_green = 1
                flg_minimum = 1
            if (prezzi[j]['descCarburante'] == 'Benzina' and eval(prezzi[j]['prezzo']) == min_benzina):
                flg_green = 1
                flg_minimum = 1
            if flg_minimum == 1:
                html += "<b>" + prezzi[j]['descCarburante'] + " " + decodeSelf(prezzi[j]['isSelf']) + " " + prezzi[j]['prezzo'] + "</b><br>"
            else:
                html += prezzi[j]['descCarburante'] + " " + decodeSelf(prezzi[j]['isSelf']) + " " + prezzi[j]['prezzo'] + "<br>"
    
    printDebug (near_fuel[i]['Latitudine'] + " " + near_fuel[i]['Longitudine'] + " " + near_fuel[i]['idImpianto'])
    
    if (flg_green == 1):
        folium.Marker((near_fuel[i]['Latitudine'], near_fuel[i]['Longitudine']), popup=folium.Popup(html, max_width=250,min_width=250), icon=folium.Icon(color='green'), max_width=500,min_width=500).add_to(map)
    else:
        folium.Marker((near_fuel[i]['Latitudine'], near_fuel[i]['Longitudine']), popup=folium.Popup(html, max_width=250,min_width=250)).add_to(map)
sw = []
ne = []
sw.append(near_fuel[0]['Latitudine'])
sw.append(near_fuel[0]['Longitudine'])
ne.append(near_fuel[0]['Latitudine'])
ne.append(near_fuel[0]['Longitudine'])

for i in range (1, len(near_fuel)):
    if near_fuel[i]['Latitudine'] < sw[0]:
        sw[0] = near_fuel[i]['Latitudine']
    if near_fuel[i]['Longitudine'] < sw[1]:
        sw[1] = near_fuel[i]['Longitudine']
    if near_fuel[i]['Latitudine'] > ne[0]:
        ne[0] = near_fuel[i]['Latitudine']
    if near_fuel[i]['Longitudine'] > ne[1]:
        ne[1] = near_fuel[i]['Longitudine']

### TO DO: FIT VAULES AND REMOVE ZOOM LEVEL ###
map.fit_bounds([sw, ne])

temp = tempfile.NamedTemporaryFile(prefix="pygeomap_", suffix=".html")

printDebug (tempfile.tempdir)
printDebug (temp.name)

map.save(temp.name)

time.sleep(1)
webbrowser.open(temp.name)
