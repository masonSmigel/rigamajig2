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
    a. Windows: Users<username>Documents/Mayamodules
    b. Linux: ~/maya/modules
    c. Mac OS X: ~/maya/modules
```

4. Open Autodesk Maya

5. Navigate to the `drag_into_maya.py` file located within the package 

6. drag the `drag_into_maya.py` file into your viewport

## Lauching the tool
Rigamajig2 has two methods to utilize the tool: 
1. The framework (available through python)
2. The BuilderUI (a more straightforward PySide interface)

To launch the UI run the following code in python
```
import rigamajig2.ui.builderUi
rigamajig2.ui.builderUi.RigamajigBuilderUi.show_dialog()
```

## Getting started 

More documentation to come 

## Dev Tools

### Reloading the modules
to reload all rigamajig2 modules run the following code 
```
import rigamajig2
rigamajig2.reloadModule()
```

### Testing 
To run the rigamajig2 tests... 

## More info
Rigamajig2 development blog: 
https://www.masonsmigel.com/blog