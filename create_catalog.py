import pystac
from saeonstac.utils import SAEONstacio

#set key
MNEMOSYNE_KEY = "xxxx"

#creates a catalog and adds a collection
def create_catalog():
    #create catalog
    cat= pystac.Catalog(
        id="saeon-stac", 
        description="SpatioTemporal Asset Catalog of geospatial data hosted by the South African Environmental Observation Network (SAEON).",
        title='saeon-stac'
        )
    return cat

#publishes catalog to catalog root
def publish_catalog(cat,stac_io):
    cat.save(catalog_type=pystac.CatalogType.RELATIVE_PUBLISHED,stac_io=stac_io)


############
###create and publish new catalog
#############
catalog_root = "https://mnemosyne.somisana.ac.za/osgeo/"

#setup creds
stac_io = SAEONstacio()
stac_io.headers = {'Authorization': f'Bearer {MNEMOSYNE_KEY}'}

#create and publish the root catalog
saeon = create_catalog()
#set catalog root
saeon.normalize_hrefs(catalog_root)
#publish
publish_catalog(saeon,stac_io)
