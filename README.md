# SPLC2py

A package for easy execution of SPLConqueror (https://github.com/se-sic/SPLConqueror) in your python workflows. The package relies on your local docker setup and uses docker-py (https://github.com/docker/docker-py) to execute a container with SPLConqueror. Note: You need to have docker installed and your executing user has to be member of the `docker` group (i.e. needs to be allowed to use docker without `sudo`).

```
pip install git+https://github.com/mailach/SPLC2py.git@main 
```

Currently the following SPLC functionalities are supported:


## Binary Sampling
Sampling of *only* binary configuration Options. The `BinarySampler` class expects you to have a valid feature model in the xml scheme of SPLC. Your input is not validated, but will lead SPLC to fail. See the following example usecases, for all usecases you need a feature model loaded as `xml.etree.ElementTree` and instantiate the `BinarySampler` class.

```python
import xml.etree.ElementTree as ET
from splc2py.sampling import BinarySampler

vm = ET.parse("path/to/vm.xml")
sampler = BinarySampler(vm)
```

### (Negative) featurewise, pairwise and distance based sampling
For (negative) featurewise and pairwise sampling no further parameters are needed. Each of the following lines of code creates a sample from the loaded feature model.

```python
sampler.sample("featurewise")
sampler.sample("negfeaturewise")
sampler.sample("pairwise")
```

### Distance-based and t-wise sampling
For distance-based and t-wise sampling you further need to pass a `params` dictionary containing the following parameters:
```python
sampler.sample("distance-based", params = {"optionWeight":2, "numConfigs":3})
sampler.sample("t-wise", params = {"t":2})
```

### Specifying return format
Currently, two return formats are supported. The default is `'list'` which will lead the sampler to return the configurations as a list of lists, where each list holds strings representing the enabled options. You can specifiy to get `'onehot'` encoded configurations, which will lead the sampler to return a list of dictionaries, in which each opttion is either 1 (enabled) or 0 (disabled). 

```python
sampler.sample("featurewise") # returns a list of lists, holding enabled options
sampler.sample("featurewise", format = "onehot") # returns a list of dictionaries with option: 1 if enabled(option) else 0
```