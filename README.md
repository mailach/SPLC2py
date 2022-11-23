# SPLC2py

A wrapper for easy execution of SPLConqueror (https://github.com/se-sic/SPLConqueror) in your python workflows. The package relies either on a local SPLConqueror installation or your local docker setup to execute a container with SPLConqueror. 

```
pip install git+https://github.com/mailach/SPLC2py.git@main 
```

Currently sampling and learning of SPLC is supported. For easy usage of these functionalities the Sampler and Model class work independent of each other and currently executing full workflows is not supported. 

## Backends
SPLC2py allows for two execution backends `local` or `docker`. You can specify the backend when creating a `Sampler` or `Model` instance. `local` execution can be used to run SPLC on kubernetes when using the Dockerimage `mailach/splc:py3.7`. *Note: When using local execution, SPLC2py expects you to have SPLconqueror installed at `/SPLConqueror/` and a working mono installation. When using docker,  you need to have docker installed and your executing user has to be member of the `docker` group (i.e. needs to be allowed to use docker without `sudo`).*


## Sampling
For sampling the `Sampler` class expects you to have a valid feature model in the xml scheme of SPLC. Your input is not validated, but will lead SPLC to fail. See the following example usecases, for all usecases you need a feature model loaded as `xml.etree.ElementTree` and instantiate the `Sampler` class. The `Sampler` class supports only binary sampling as wells as numeric and binar sampling mixed. By default, if no other strategy is given, the sampler will execute `allbinary` strategy and no numeric. 

```python
import xml.etree.ElementTree as ET
from splc2py.sampling import Sampler

vm = ET.parse("path/to/vm.xml")
sampler = Sampler(vm, "docker") # specify the backend to execute SPLC
```

### Binary sampling strategies
For only sampling binary options you only set the `binary` argument and corresponding parameters. 


#### (Negative) featurewise, pairwise and distance based sampling
For (negative) featurewise and pairwise sampling no further parameters are needed. Each of the following lines of code creates a sample from the loaded feature model.

```python
sampler.sample(binary="featurewise")
sampler.sample(binary="negfw")
sampler.sample(binary="pairwise")
```

#### Distance-based and t-wise sampling
For distance-based and t-wise sampling you further need to pass a `params` dictionary containing the following parameters:
```python
sampler.sample(binary="distance-based", params = {"optionWeight":2, "numConfigs":3})
sampler.sample(binary="twise", params = {"t":2})
```



### Numeric sampling strategies
 For sampling numerical options you can set the `numeric` argument and corresponding parameters. Note, that the `binary` argument defaults to `allbinary`.
```python

# strategies with not further parameters
sampler.sample(numeric="centralcomposite")
sampler.sample(numeric="fullfactorial")
sampler.sample(numeric="boxbehnken")

# strategies that need further specification of parameters
sampler.sample(numeric="plackettburman", params = {"measurements":125, "level":5})
sampler.sample(numeric="random", params = {"sampleSize":20, "seed":5})
sampler.sample(numeric="hypersampling", params = {"precision":25})
sampler.sample(numeric="onefactoratatime", params = {"distinctValuesPerOption":5})
sampler.sample(numeric="kexchange", params = {"sampleSize":10, "k":3})
```

### Mix binary and numeric sampling strategies
You can combine numeric and binary strategies by setting both arguments and provide all necessary parameters in `params`. Some examples are
```python
sampler.sample(binary="featurewise", numeric="kexchange", params = {"sampleSize":10, "k":3})
sampler.sample(binary="pairwise", numeric="boxbehnken")
sampler.sample(binary="twise", numeric="hypersampling", params = {"t":2, "precision":25})
```


### Specifying the return format
Currently, two return formats are supported. The default is `'list'` which will lead the sampler to return the configurations as a list of lists, where each list holds strings representing the enabled options. You can specifiy to get `'dict'` encoded configurations, which will lead the sampler to return a list of dictionaries, in which each binary option is either 1 (enabled) or 0 (disabled) and each numeric option is assigned with a float value. 

```python
sampler.sample(binary="featurewise") # returns a list of lists, holding enabled options
sampler.sample(binary="featurewise", formatting = "dict") # returns a list of dictionaries with option: 1 if enabled(option) else 0 and floats for numeric features
```


## Learning
For learning the `Model` class expects you to provide valid measurements in either splc-xml loaded as a table loaded as `pandas.DataFrame`, in which binary options are represented as 1 or 0 and numeric features hold the corresponding numeric value.

```python
import pandas as pd
import xml.etree.ElementTree as ET

from splc2py.learning import Model

measurement_data = pd.read_csv("path/to/traindata") # for pandas format

model = Model("docker") # specify the backend to execute SPLC
model.fit(measurement_data, "nfp") 
```

*Note: the `Model.fit()` method will generate a generic feature model from the input data, since this is needed by SPLC for learning. Therefore, the internal validation that is performed by SPLC on the learning set will always evaluate to true. You are responsible for providing valid configurations.* 

You can use the `model` instance to generate predictions by providing a pandas dataframe. You can further print the model as a string and get the learning history.

```python
test_data = pd.read_csv("path/to/testdata")
predictions = model.predict(test_data) 
print(model.to_string())
print(model.learn_history)
```

### Specifying machine learning settings
SPLC supports a wide list of mlsettings, such as `lossFunction`, `epsilon`, `parallelization` or `bagging`. You can pass individual settings as a dictionary to the `Model.fit()` method. For a full list of supported settings visit the SPLC documentation.

```python
model.fit(measurement_data, "nfp", mlsettings = {"lossFunction": "LEASTSQUARES", 
                                                 "parallelization": "false",
                                                 "useBackward": 0}) 
```

## Parsing FM from SPLC format

Generate a dimacs from the *binary* options in a splc-xml file. 

```python
import xml.etree.ElementTree as ET
from splc2py.fmodel import FeatureModel

fm_xml = ET.parse("path/to/fm.xml")
fm = FeatureModel(fm_xml)

# get attributes of feature model
fm.dimacs
fm.constraints
fm.binary
fm.numeric

```
