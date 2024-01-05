import requests
import json
import os
from requests.structures import CaseInsensitiveDict
import csv
import math
import pandas as pd

# ler os dados de categoria

with open('categories.txt', 'r') as f:
    categories = [line.strip() for line in f]
  
dictcategories = {}

for category in categories:
    if '.' not in category:
        if category not in dictcategories:
            dictcategories[category] = [category]
        else:
            continue
    else:
        category_splity = category.split('.')[0]
        dictcategories[category_splity].append(category)


def checkCategory(category):
    """Verifica se a categoria existe."""
    has_category = False
    if category in dictcategories:
        has_category = True
    else:
        for value in dictcategories.values():
            if category in value:
                has_category = True
                break

    return has_category



def getKey():
    """get api key from file"""
    with open('api.txt', 'r') as f:
        api_key = f.readline()
    return api_key


def get_attractions(latitude, longitude, max_distance, categories):
    """Obter as atrações."""
    # Construir a URL com os parâmetros
    url = f"https://api.geoapify.com/v2/places?categories={categories}&filter=circle:{longitude},{latitude},{max_distance}&apiKey={getKey()}"

    # Fazer o pedido à API
    response = requests.get(url)
    data = response.json()

    
    #print(get_attractions(39.42847, -8.80643, 1000, "no_fee"))
    places=[] 

    if data.get("features") is not None:
        #print(data)
        for place in data.get("features"):
            if place.get("properties").get("name") is None:
                continue
            places.append(place)
    else:
        return []
        #print("No places found", data)
        
    return places if places else []


def convert_time(time_in_hours):
    """Converte tempo de horas para hora e minuto."""
    minutes = time_in_hours * 60
    return f"{time_in_hours:.0f}h {minutes:.0f}m"

def order_attractions(attractions, criteria):
    """Ordena as atrações."""
    if criteria == "name":
        attractions.sort(key=lambda attraction: attraction.get("properties").get("name"))
    elif criteria == "contry":
        attractions.sort(key=lambda attraction: attraction.get("properties").get("country"))
    return attractions


def filter_attractions(attractions, name, country):
    filtered_attractions = []
    for attraction in attractions:
        attraction_name = attraction.get("properties").get("name")
        country_code = attraction.get("properties").get("country_code")
        if attraction_name == name and country_code == country:
            filtered_attractions.append(attraction)
    return filtered_attractions


def calculate_distance(lat1, lon1, lat2, lon2):
   """Calcula a distância entre duas coordenadas."""
   R = 6371 # raio da Terra em km
   phi1 = math.radians(lat1)
   phi2 = math.radians(lat2)
   delta_phi = math.radians(lat2 - lat1)
   delta_lambda = math.radians(lon2 - lon1)
   a = math.sin(delta_phi / 2) * math.sin(delta_phi / 2) + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) * math.sin(delta_lambda / 2)
   c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
   return R * c


def order_by_distance(attractions, latitude, longitude):
   """Ordena as atrações por distância."""
   attractions.sort(key=lambda attraction: calculate_distance(latitude, longitude, attraction.get("properties").get("lat"), attraction.get("properties").get("lon")))
   return attractions


def attractions_to_dataframe(attractions):
   """Transforma as atrações em um DataFrame do pandas. Essa 
   é para poder exportar para um arquivo CSV."""
   data = []
   for attraction in attractions:
       data.append({
           "Nome": attraction.get("properties").get("name"),
           "País": attraction.get("properties").get("country"),
           "Endereço": attraction.get("properties").get("formatted"),
           "Localização": f"{attraction.get('properties').get('lat')}, {attraction.get('properties').get('lon')}",
           "Distância": calculate_distance(latitude, longitude, attraction.get("properties").get("lat"), attraction.get("properties").get("lon")),
           "Categorias": ", ".join(attraction.get("properties").get("categories"))
       })
   return pd.DataFrame(data)


def write_to_csv(df, filename):
   """Escreve um DataFrame em um arquivo CSV."""
   df.to_csv(filename, index=False, encoding='utf-8')



def print_attraction(attraction, latitude2, longitude2):
    """Imprime as atrações."""

    if attraction == []:
        print("Não foram encontradas atrações")
        return

    print("Lista de lugares para visitar:\n")

    sum_distance = 0
    for attraction in attractions:
        print("Nome:",attraction.get("properties").get("name"))
        print("País:",attraction.get("properties").get("country"))
        print("Endereço:",attraction.get("properties").get("formatted"))
        latitude = float(attraction.get("properties").get("lat"))
        longitude = float(attraction.get("properties").get("lon"))
        print("Localização:",latitude, longitude)

        #distance = ((latitude - 39.42847)**2 + (longitude - (-8.80643))**2)**0.5
        distance = calculate_distance(latitude, longitude, latitude2, longitude2)
        sum_distance += distance
        distance = round(distance, 3)
        print(f"Distância em relação ao ponto de partida: {distance}km")
        print("categorias:",attraction.get("properties").get("categories"))
        # velocidade media: carro 100km/h, autocarro 20km/h, comboio 120km/h a pé 5km/h

        tempo_carro = distance / 100
        tempo_autocarro = distance / 20
        tempo_comboio = distance / 120
        tempo_pe = distance / 5

        print(f"Tempo médio para chegar de: carro - {convert_time(tempo_carro)}, autocarro - {convert_time(tempo_autocarro)}, comboio - {convert_time(tempo_comboio)}, a pé - {convert_time(tempo_pe)}")

        
        print("----------------------------------------------------")
    print(f"Número de atrações obtidas: {len(attractions)}")
    print(f"Distância média: {(sum_distance/len(attraction)):.3f}km")



# Função principal
if __name__ == "__main__":
    # Pegar as localizações do utilizador
    latitude = float(input("Digite a latitude: "))
    longitude = float(input("Digite a longitude: "))

    # pedir a distancia desejada
    distance_max = float(input("Digite a distancia maxima: "))

    # pegar as atraçoes do utilizador
    types = []
    while True:
        category = input("Enter a category ('q' to quit): ")
        category = category.strip()
        if category == "q":
            break
        if not checkCategory(category):
            print("Categoria inválida\ntry to rewrite the category or type 'q' to exit")
            continue

        # depois tenho que validar as categoriase

        types.append(category)
    

    # perguntar se pretende ordenar e/ou filtrar
    order_attractions_by = input("Ordenar as atrações (s/n): ")
    filter_attractions_by = input("Filtrar as atrações (s/n): ")

    # obter as atrações
    attractions = get_attractions(latitude, longitude, distance_max, ",".join(types))

    if order_attractions_by == "s":
        order_by = input("Ordenar as atrações por (name or country): ")
        attractions = order_attractions(attractions, order_by)

    if filter_attractions_by == "s":
        filter_criteria = input("Filtrar as atrações por (name e/ou country): ")
        attractions = filter_attractions(attractions, filter_criteria)

    print_attraction(attractions, latitude, longitude)

    attractions = order_by_distance(attractions, latitude, longitude)
    df = attractions_to_dataframe(attractions)
    write_to_csv(df, 'attractions.csv')

