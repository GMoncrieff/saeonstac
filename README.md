# SAEONSTAC

## Overview
This repository contains code for creating and managing a SpatioTemporal Asset Catalog (STAC) for the South African Environmental Observation Network (SAEON).

## Prerequisites
- Python 3.8+
- Conda

## Environment Setup

To set up the Python environment, run:

```bash
conda env create -f environment.yml
conda activate saeonstac
```

## Usage

First create the catalog. Skip this step if you aready have the catalog and just want to add a collection

```python
python create_catalog.py
```

Then add a collection. Skip this step if you already have a collection and just want to add items

```python
python create_collection.py
```

Then add items to the collection
```python
python update_collection.py
```
