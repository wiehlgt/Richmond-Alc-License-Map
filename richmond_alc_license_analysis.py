#%%
import requests
import pandas as pd
"""Here we get the Richmond Alcohol License data from the Richmond gov
We will get the data in the from of a json file and extract the addresses from it.
In order to map this data we will need the geocodes from the google api"""

r = requests.get("https://data.richmondgov.com/resource/bc34-rjtz.json",)
alc_license = r.json()
license_df = pd.DataFrame(alc_license)
#%%
"""There are some errors in the addresses list.
These are just the ones that I found by my own eyes, we'll look for more errors later"""

license_df.loc[150,'add1'] = license_df.loc[150,'add1'].replace("1215 ", "")
license_df.loc[375,'add1'] = license_df.loc[375,'add1'].replace("1106 ", "")
license_df.loc[419,'add1'] = license_df.loc[419,'add1'].replace("206 ", "")
#%%
"""There are some duplicated addresses. It is possible some of these have different
dates associated with it, but most of them have the same dates.
We will get rid of them for now ."""

uniq_df = license_df.drop_duplicates(subset = 'add1').reset_index(drop=True).copy()
uniq_addresses = uniq_df['add1']
#%%
"""Now lets use the google maps api to find the geocodes for each address. 
If an address is not found there is probably an error.Also we will add ", RICHMOND, VA" 
to all of the addresses to make sure the geocodes will be in the right city. We are using the 
google geocoding api, but we could also use the places api for more place specific data"""

api_key = "AIzaSyCVq-N1exVB0mZzLw18A73RRTiS9ymD39g"
geocode_url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}"

error_addr = []
for index, address in enumerate(uniq_addresses):
    try:
        geo = requests.get(geocode_url.format(address+ " , RICHMOND, VIRGINIA",api_key))
        geo = geo.json()
        results = geo['results']
        geometry = results[0]['geometry']
        location = geometry['location']
        uniq_df.loc[index, 'latitude'] = location['lat']
        uniq_df.loc[index, 'longitude'] = location['lng']
        print("{} address found".format(index + 1))
    except IndexError:
        error_addr.append([index,address])
        print("{} error found at index {}".format(len(error_addr), index))
        pass
print("Errors found at:",error_addr)
#%%
"""Looks as though there is only one error left.
the address that didn't work is 7009 THREE CHOPT RD STE A.
lets remove the "STE A." because I don't know what that means,
Then find the geocode and enter it into lat_long"""

uniq_df.loc[487,'add1'] = uniq_df.loc[487,'add1'].replace(" STE A", "")
geo = requests.get(geocode_url.format(uniq_df.loc[487,'add1'],api_key))
geo = geo.json()
results = geo['results']
geometry = results[0]['geometry']
location = geometry['location']
uniq_df.loc[487,'latitude'] = location['lat']
uniq_df.loc[487,'longitude'] = location['lng']
#%%
"""There seems to a problem with two addresses lat/long data, two of them are clearly not 
located in the city of Richmond. It seems as though neither the geocoding api nor the 
places api gets these two coordinates correct. Right now we'll get rid of the data so we 
don't have two points in the middle of nowhere when we map the data"""

uniq_df.loc[670,['latitude','longitude']] = None
uniq_df.loc[89,['latitude','longitude']] = None
#%%
"""Now that we have our latitude and longitude data, lets get our map of Richmond."""
from bokeh.io import output_file, show, save
from bokeh.models import ColumnDataSource, GMapOptions, HoverTool, CDSView, GroupFilter, BooleanFilter
from bokeh.plotting import gmap

output_file("richmond_alc.html")

map_options = GMapOptions(lat=37.55, lng=-77.45, map_type="roadmap", zoom=12) 
p = gmap(api_key, map_options, title="Richmond") #google maps plot

source = ColumnDataSource(uniq_df) #put the dataframe in a ColumnDataSource object

restaurant = CDSView(source=source, filters=[GroupFilter(column_name='estabdesc', group='Restaurant')]) #filters for restuarants
convenience = CDSView(source=source, filters=[GroupFilter(column_name='estabdesc', group='Convenience Grocery Store')]) #filters for convenience stores
grocery = CDSView(source=source, filters=[GroupFilter(column_name='estabdesc', group='Grocery Store')]) #filters for grocery stores
gourmet = CDSView(source=source, filters=[GroupFilter(column_name='estabdesc', group='Gourmet Shop')]) #filters for gourmet shops
brewery = CDSView(source=source, filters=[GroupFilter(column_name='estabdesc', group='Brewery')]) #filters for brewerys
club = CDSView(source=source, filters=[GroupFilter(column_name='estabdesc', group='Club - National')]) #filters for clubs

main_list = ['Restaurant','Convenience Grocery Store','Grocery Store',
             'Gourmet Shop','Brewery', 'Club - National']
booleans = [False if desc in main_list else True for desc in source.data['estabdesc'] ] 
misc = CDSView(source=source, filters=[BooleanFilter(booleans)]) #filters for all of the rest


p.circle(x='longitude', y="latitude", size=10, fill_color="red", fill_alpha=0.7, source=source, view=restaurant, legend="Restaurant")
p.circle(x='longitude', y="latitude", size=10, fill_color="purple", fill_alpha=0.7, source=source, view=convenience, legend="Convenience Store")
p.circle(x='longitude', y="latitude", size=10, fill_color="green", fill_alpha=0.7, source=source, view=grocery, legend="Grocery Store")
p.circle(x='longitude', y="latitude", size=10, fill_color="brown", fill_alpha=0.7, source=source, view=gourmet, legend="Gourmet Shop")
p.circle(x='longitude', y="latitude", size=10, fill_color="yellow", fill_alpha=0.7, source=source, view=brewery, legend="Brewery")
p.circle(x='longitude', y="latitude", size=10, fill_color="blue", fill_alpha=0.7, source=source, view=club, legend="Club")
p.circle(x='longitude', y="latitude", size=10, fill_color="gray", fill_alpha=0.7, source=source, view=misc, legend="Miscellaneous")

TOOLTIPS = [
    ("Name", "@tradename")
]
hover_tool = HoverTool(tooltips=TOOLTIPS)
p.add_tools(hover_tool)

p.legend.location = "top_right"
p.legend.click_policy="hide"

show(p)
save(p,"richmond_alc.html")