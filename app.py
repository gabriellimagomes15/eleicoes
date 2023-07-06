#%%writefile app.py

import streamlit as st
#import folium
#from streamlit_folium import st_folium

st.write('Hello, *World!* :sunglasses:')
st.title('Eleições de')
st.title('Aqui estará seu mapa!!! :sunglasses:')
"""
# center on Liberty Bell, add marker
m = folium.Map(location=[39.949610, -75.150282], zoom_start=16)
folium.Marker(
    [39.949610, -75.150282], popup="Liberty Bell", tooltip="Liberty Bell"
).add_to(m)

# call to render Folium map in Streamlit
st_data = st_folium(m, width=725)
"""
