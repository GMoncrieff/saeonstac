import pystac
from saeonstac.utils import SAEONstacio

#setup creds
MNEMOSYNE_KEY = "xxxx"

#creates empty pystac collection
def create_collection():
    
    sp_extent = pystac.SpatialExtent([None, None, None, None])
    #capture_start_date = datetime.strptime("2010-01-01", "%Y-%m-%d")
    tmp_extent = pystac.TemporalExtent([(None, None)])
    extent = pystac.Extent(sp_extent, tmp_extent)
    
    ngi_provider =   pystac.Provider(
    name= "National Geo-spatial Information (NGI), Department of Agriculture, Land Reform and Rural Development (DALRRD))",
    description= "South Africa's national mapping organisation",
    roles= [
        "producer",
        "processor"
    ],
    url= "https://ngi.dalrrd.gov.za/"
    )
    saeon_provider =   pystac.Provider(
        name= "South African Environmental Observation Network (SAEON)",
        description= "South Africa's long-term environmental observation and research facility",
        roles= [
            "host"
        ],
        url= "https://www.saeon.ac.za/"
    )

    #create collection
    za25 = pystac.Collection(
        id="ngi25",
        description="South Africa aerial photos - 25cm RGB imagery", extent=extent,
        title="South_Africa_25cm_RGB",
        license= "CC-BY-4.0",
        providers = [ngi_provider, saeon_provider]
        
    )
    return za25

#pubish collection to catalog
def publish_collection(cat,col,root,stac_io,col_dest):
    cat.add_child(col)
    pystac.write_file(col,
                  include_self_link= False,
                  dest_href = col_dest,
                  stac_io=stac_io)
    pystac.write_file(cat,
                  include_self_link= True,
                  stac_io=stac_io)
    
############
###create and publish new collection
#############
catalog_root = "https://mnemosyne.somisana.ac.za/osgeo/"

#setup creds
stac_io = SAEONstacio()
stac_io.headers = {'Authorization': f'Bearer {MNEMOSYNE_KEY}'}
#load catalog
saeon = pystac.catalog.Catalog.from_file(f'{catalog_root}catalog.json',stac_io)
#create collection
ngi25 = create_collection()
#publish
publish_collection(saeon,ngi25,root = catalog_root,stac_io=stac_io,col_dest=f'{catalog_root}ngi25/collection.json')