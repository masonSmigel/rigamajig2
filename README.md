# Rigamajig2
Rigamajig2 is a modular data-centric rigging tool for Autodesk Maya. 
It provides a straightforward method of creating and 
connecting componets to create complex rigs. 

* Rigamajig2 currently only supports Python 2. While compatiablity 
with Python 3 is being developed if using Maya 2022 or 2033 
please change your Python version to version 2 in the global variables. 

## Installation 
To install rigamajig2 on your computer: 

1. Download the latest version from the git repository

2. Unzip it

3. Copy the rigamajig2-master folder somewhere on your hard drive. 
If you're unsure of a good place the Maya modules folder is a good bet. 
```
Windows: Users<username>Documents/Mayamodules
Linux: ~/maya/modules
Mac OS X:/Users/<username>/Library/Preferences/Autodesk/maya/modules
```

4. Open Autodesk Maya

5. Navigate to the `drag_into_maya.py` file located within the package 

6. drag the `drag_into_maya.py` file into your viewport

## Lauching the tool
Rigamajig2 has two methods to utilize the tool: 
1. The framework (available through python)
2. The BuilderUI (a more straightforward PySide interface)

To launch the UI run the following code in python
```python
import rigamajig2.ui.builder_ui.dialog as builder_dialog
builder_dialog.BuilderDialog.showDialog()
```

## Getting started 

More documentation to come 

## Dev Tools

### Reloading the modules
To reload all rigamajig2 modules in a python session run the following code 
```python 
import rigamajig2
rigamajig2.reloadModule()
```

### Pylint 
Rigamajig2 adheres to some general coding practices. To test any additions made
 the run the following command:

```commandline
cd path/to/rigamajig2 
pylint scripts/rigamajig2
```

Or if you using PyCharm configure your project to use the `rigamajig2/scripts` folder 
as the content root. Then you can run: 

```commandline
pylint rigamajig2
```

### Testing 
Rigamajig2 comes with unitesting capiblilities. 


#### Running the Unittests
To run tests run the python command 
located in the bin at `rigamajig2/bin/testrigamajig`. 

```commandline
cd path/to/rigamajig2/bin 
python testrigamajig
```

#### Creating new Unittests
Added unittests must be subclasses of the base unittest class.To setup your own unittest 
confugure your test as shown below: 

```python
from rigamajig2.maya.test.mayaunittest import TestCase

class TestSomething(TestCase):
    def test_someSuperCoolTest(self):
        """ Your awesome test goes here"""
        pass
```

## More info
Rigamajig2 development blog: 
https://www.masonsmigel.com/blog

Questions? 
email me at mgsmigel@gmail.com! 
