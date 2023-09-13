
import pystac
import os
import json
import requests
from urllib.parse import urlparse
import re
import rio_stac
import numpy as np
from xml.etree import ElementTree as ET
import rasterio
from io import BytesIO
from rasterio.enums import Resampling
from PIL import Image
from  datetime import datetime
from shapely.geometry import GeometryCollection, shape

#stac io class
class SAEONstacio(pystac.stac_io.DefaultStacIO):
    def write_text_to_href(self, href: str, txt: str) -> None:
        """Writes text to file using UTF-8 encoding.

        This implementation uses the `requests` library to send a PUT request
        with the file contents.

        Args:

            href : The URL to which the file will be uploaded.
            txt : The string content to write to the file.
        """
        href = os.fspath(href)
        # Convert the text to bytes using UTF-8 encoding
        txt_bytes = txt.encode("utf-8")
        # Send a PUT request to upload the file
        response = requests.post(href, headers=self.headers, data=txt_bytes)

        # Check if the request was successful
        if response.status_code not in  [200,201]:
            raise RuntimeError(f"Failed to upload the file. Status code: {response.status_code}, Response: {response.text}")

def split_url_path_and_filename(url):
    parsed_url = urlparse(url)
    base_url = parsed_url.scheme + '://' + parsed_url.netloc
    path, filename = os.path.split(parsed_url.path)
    complete_path = base_url + path
    return complete_path, filename

def get_name(url):
    parsed_url = urlparse(url)
    filename_with_ext = os.path.basename(parsed_url.path)
    filename_without_ext = filename_with_ext.split('.')[0]
    return filename_without_ext

def get_ngi_dates(url):
    #hardcoded
    root="https://mnemosyne.saeon.ac.za/osgeo/ngi25"
    
    #get vrt filename
    pattern = r'\d{4}[A-Z]{2}'
    result = re.search(pattern, url)
    if result:
        extracted_string = result.group()
        path = f"{root}{extracted_string}.vrt"
    else:
        raise ValueError("No match")
    
    # Read the VRT data from the file
    response = requests.get(path)

    if response.status_code == 200:
        vrt_data = response.text
    else:
        print(f"Failed to fetch the URL: {url}")

    tree = ET.fromstring(vrt_data)

    # Find all SourceFilename tags
    source_filenames = tree.findall(".//SourceFilename")

    # Extract the year from each source filename and store the raw source filenames
    years = []
    raw_source_filenames = []
    for source_filename in source_filenames:
        filename_only = os.path.basename(source_filename.text)
        raw_source_filenames.append(filename_only)
        match = re.search(r"(\d{4})_", source_filename.text)
        if match:
            year = int(match.group(1))
            years.append(year)

    return years, raw_source_filenames

def list_files_on_webserver(url,extension = '.tif', base_url = ''):
    headers = {'Accept': 'Application/json'}
    response = requests.get(url, headers=headers)
    parsed_data = json.loads(response.text)
    tif_paths = [base_url + item['entry'] for item in parsed_data if item['isFile'] and (item['path'].endswith(extension))]
    return tif_paths

def get_ngi_properties(filename):
    years, filenames = get_ngi_dates(filename)
    minyear = np.array(years).min()
    maxyear = np.array(years).max()
    #end = datetime.strptime(f"{maxyear}-12-31", "%Y-%m-%d")
    startstr = f"{minyear}-01-01 00:00:00Z"
    endstr = f"{maxyear}-12-31 00:00:00Z"
    properties = {'start_datetime':startstr,'end_datetime':endstr,'ngi_source_files':filenames}
    return properties

def create_thumbnail(url,token="16f848885810b30b761e81dc2871b36e:cb7049071594b44429d2694dd59bd9f0039627ae72207895e9b03ea041f85330", thumbnail_size=(256, 256)):
    print(url)
    with rasterio.open(url) as src:
        # Calculate the thumbnail dimensions while maintaining the aspect ratio
        scale = min(thumbnail_size[0] / src.width, thumbnail_size[1] / src.height)
        width = int(src.width * scale)
        height = int(src.height * scale)

        # Read the raster data and resample it
        data = src.read(
            out_shape=(src.count, height, width),
            resampling=Resampling.bilinear
        )

        thumbnail_data = data.transpose(2, 1, 0)
        thumbnail_data = thumbnail_data[:,:,:3]
        img = Image.fromarray(thumbnail_data, mode="RGB")
        buffer = BytesIO()
        img.save(buffer, "JPEG")
        buffer.seek(0)
        #get path and name of source
        path, name = split_url_path_and_filename(url)
        
        #upload
        headers = {"Authorization": f"Bearer {token}"}
        thumbpath = f"{path}/{name}_thumb.jpeg"
        response = requests.post(thumbpath, headers=headers, data=buffer.getvalue())
                
        # Check if the request was successful
        if response.status_code not in  [200,201]:
            raise RuntimeError(f"Failed to upload the file. Status code: {response.status_code}, Response: {response.text}")

        return thumbpath

    #read example.tif using rasterio
    tiff_files = list_files_on_webserver(url)
    print(tiff_files)
    #tiff_files=['2328DB.webp.google.r_lanczos.bs_256.aligned.cog.tif','2328DC.webp.google.r_lanczos.bs_256.aligned.cog.tif','2328DD.webp.google.r_lanczos.bs_256.aligned.cog.tif']
    for i in range(len(tiff_files)):
        with rasterio.open(f"{url}{tiff_files[i]}") as src:
            years, filenames, grid = get_dates(tiff_files[i],url)
            minyear = np.array(years).min()
            maxyear = np.array(years).max()
            start = datetime.strptime(f"{minyear}-01-01", "%Y-%m-%d")
            #end = datetime.strptime(f"{maxyear}-12-31", "%Y-%m-%d")
            startstr = f"{minyear}-01-01 00:00:00Z"
            endstr = f"{maxyear}-12-31 00:00:00Z"
            properties = {'start_datetime':startstr,'end_datetime':endstr,'ngi_source_files':filenames}
            
            thumb = create_thumbnail(f"{url}{tiff_files[i]}")
            thumb_ass = pystac.Asset(
                href=thumb,
                roles=['thumbnail'],
                media_type="image/JPEG"
            )
            item = rio_stac.create_stac_item(
                src,
                id=grid,
                input_datetime=start,
                collection=col.id,
                asset_name='cog',
                asset_media_type='image/tiff; application=geotiff; profile=cloud-optimized',
                asset_roles=['visual'],
                geom_precision=5,
                with_proj=True,
                properties=properties)
            
            item.common_metadata.gsd = 0.25
            
            item.add_asset(f"{grid}_thumbnail",thumb_ass)
            
            pystac.write_file(item,
                include_self_link= False,
                dest_href = f"{url}{grid}/{grid}.json",
                stac_io=stac_io)
            
            col.add_item(item)
            #print(si.to_dict())
            
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