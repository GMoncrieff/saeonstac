import pystac
import rasterio
import rio_stac
import datetime
from saeonstac.utils import SAEONstacio
from saeonstac.utils import get_name, create_thumbnail, list_files_on_webserver, get_ngi_properties
from shapely.geometry import GeometryCollection, shape

#setup creds
MNEMOSYNE_KEY = "xxxx"

def add_to_collection(col,url,properties):
    #read example.tif using rasterio
    tiff_files = list_files_on_webserver(url)
    #print(tiff_files)
    
    #iterate thourhg files and create items
    for i in range(len(tiff_files)):
        with rasterio.open(f"{url}{tiff_files[i]}") as src:
            
            #this is specific to the ngi data
            #implement your own properties
            properties  = get_ngi_properties(tiff_files[i])
            
            #this is just a placeholder
            #implement your own method to assign a date to the image
            year = properties['startstr'][:4]
            image_date = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")

            #create a name for the image
            image_name = get_name(f"{url}{tiff_files[i]}")
            
            #create thumbnial
            thumb = create_thumbnail(f"{url}{tiff_files[i]}")
            thumb_ass = pystac.Asset(
                href=thumb,
                roles=['thumbnail'],
                media_type="image/JPEG"
            )
            #create the item
            item = rio_stac.create_stac_item(
                src,
                id=image_name,
                input_datetime=image_date,
                collection=col.id,
                asset_name='cog',
                asset_media_type='image/tiff; application=geotiff; profile=cloud-optimized',
                asset_roles=['visual'],
                geom_precision=5,
                with_proj=True,
                properties=properties)
            
            item.common_metadata.gsd = 0.25
            
            item.add_asset(f"{image_name}_thumbnail",thumb_ass)
            
            pystac.write_file(item,
                include_self_link= False,
                dest_href = f"{url}{image_name}/{image_name}.json",
                stac_io=stac_io)
            
            col.add_item(item)
            
    #update collection
    #update extent1
    bounds = [
        list(
            GeometryCollection([shape(s.geometry) for s in col.get_all_items()]).bounds
        )
    ]
    col.extent.spatial = pystac.SpatialExtent(bounds)

    #update extent2
    col.update_extent_from_items()
    
    return col


############
###add items to collection and update collection
#############

catalog_root = "https://mnemosyne.somisana.ac.za/osgeo/"

#setup creds
stac_io = SAEONstacio()
stac_io.headers = {'Authorization': f'Bearer {MNEMOSYNE_KEY}'}

#load collection
ngi25 = pystac.collection.Collection.from_file(f'{catalog_root}ngi25/collection.json',stac_io)

#add items to collection 
ngi25 = add_to_collection(ngi25,dest="",url=f'{catalog_root}ngi25/')

pystac.write_file(ngi25,
                include_self_link= False,
                dest_href = f'{catalog_root}ngi25/collection.json',
                stac_io=stac_io)
