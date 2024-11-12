# Overview

Rigamajig2 is an advanced, modular data-centric rigging tool designed for Autodesk Maya. Empowering
riggers, Rigamajig2 streamlines the complex process of creating intricate rigs by providing a
user-friendly interface and a powerful set of features.

- **Modular Data**: Rigamajig2 excels in modularity, allowing users to effortlessly store and manage data. This
  modular approach facilitates the construction of sophisticated rigs with ease. While allowing data to be very potable,
  saving time when facing similar rigging problems.


- **Designed for riggers**: With a focus on simplicity and efficiency, Rigamajig2 offers a straightforward method for
  creating rigs. While also exposing an internal framework for artist who want to build additional components or
  features.


- **Rigs animators love**: With a focus on building well-designed systems and an emphasis on performance rigs built with
  rigamajig allow for great deformations and real time playback.

# Installation

To install rigamajig2:

1. Download the latest release from the git repository
2. Unzip it
3. Copy the rigamajig2-master folder somewhere on your hard drive.
   If you're unsure of a good place the Maya modules folder is a good bet.

    ```
    Windows: Users<username>Documents/maya/modules
    Linux: ~/maya/modules
    Mac OS X:/Users/<username>/Library/Preferences/Autodesk/maya/modules
    ```

4. You will also need to install the third party requirements for rigamajig. (see the requires.txt).

   #### Note: These are only the requirements for a  general user, there are other recommendations if you plan to contribute

    ```commandline
    cd path/to/rigamajig2 
    pip install -r  requirements-core.txt --target python/lib
    ```

5. Open Autodesk Maya
6. Navigate to the `drag_into_maya.py` file located within the rigamajig package
7. drag the `drag_into_maya.py` file into your viewport

# Lauching the tool

Rigamajig2 has two methods to utilize the tool:

1. The framework (available through python)
2. The BuilderUI (a more straightforward PySide interface)

To launch the UI run the following code in python

```python
from rigamajig2.ui.builder.builderDialog import BuilderDialog

BuilderDialog.display()
```

# Getting started

More documentation to come

# Dev Tools

## installing additional packages

When developing on rigamajig2 It is highly recomended to work within a virtual enviornment.
Setup your venv to use python 3.9. You will also need to install the addional requirements for developers
this includes addtional tools for testing and code style:

```
cd path/to/rigamajig/venv/bin
pip install -r  requirements-dev.txt 
```

## Reloading the modules

When developing you will often want test your changes by reloading your python packages.
To reload the python packages within maya:

#### Note: Due to the structure of data gathering functions within the builder UI you will also need to re-launch the UI for rigamajig2 to function properly.

```python 
import rigamajig2

rigamajig2.reloadModule()
```

## Code Formatting and style

### Black

In general rigamajig adheres to the black coding style to format code consitantly. For more information check out the
black documentaiton.

to reformat files with black

```commandline
cd path/to/rigamaijg2
black path/to/python/module.py
```

### Pylint

While black handles code formatting the pylint configuration helps to ensure consistant naming within files.

```commandline
cd path/to/rigamajig2 
pylint python/rigamajig2
```

### Testing

While testing is still incomplete rigamajig uses pytest (specifically the mayatest package) to ensure code quality

#### Running the Unittests

To run tests run the python command
located in the bin at `rigamajig2/bin/testrigamajig`.

```commandline
cd path/to/rigamajig2/bin 
runmayatest -t ../tests/

// you can also specify a maya version to test with
runmayatest -m 2022 -t ../tests/

// or specific test modules or functions
runmayatest -t ../tests/test_module:test_func
```

### Generating Documentation

Documentation can be auto-generated using sphinx.

when new modules are added please cd into `rigamajig2/docs` and run the following to generate `.rst` files for all
modules

```commandline
sphinx-apidoc -o source ../python
```

To build the HTML Documentatino run:

```commandline
make html
```

## More info

Rigamajig2 development blog:
https://www.masonsmigel.com/blog

Questions?
email me at me@masonsmigel.com
