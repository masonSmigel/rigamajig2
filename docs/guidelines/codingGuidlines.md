# General Coding Guidelines
Some general coding and style guidelines to both keep the project clean and pass the linter. 

## Vocabulary
* varriables
* functions: defintions outside of classes. 
* methods: definitions inside a class
* private variables: are not meant to be used outside of the module 
* hidden variables: are hidden from other modules

```python
myVariable = 'someString'
CONSTANT_VARIABLE = True
_privateVariable = 'Some private data'
__hiddenVariable = 'Some hidden data'


def myFunction():
  return "This is a function"


class myClass:
  def myMethod(self):
    return "This is a method"
```


## Naming conventions
* Classes must be  `PascalCase` 
* namespaces must be `lowercase`
* Constants must be `UPPER_CASE` (words separated by an underscore `_`)
* Use abbrivations where it makes sense but it MUST be readable. 
* Naming convetion for public, private, and hidden: 
  * public: `camelCase`
  * private: `_camelCase` (starts with `_`)
  * hidden: `__camelCase` (starts with `__`)


## Generic 
* 4 spaces to indent. No 'tab' characters
* Code should not exeed 120 characters per line 
* Break code into smaller functions when possible. Try not to exceed 75-100 lines 
* strings should be `unicode` for python3 compatability
* return values should NOT be inside parenthesis
* Add 1 blank line at the end of a file 
* Add 1 blank line between methods in a class 
* Add 2 blank lines between functions

## Tags 
* `TODO`: Marks a feature to come back and do later
* `FIXME`: Marks non-working code that shoudl be fixed later 
* `BUG`: marks a bug in the code. Should go with a TODO 
* `HACK`: Marks an ugly solution to do something

## Python 
* Avoid `global` varriables 
* NEVER override python builtins. 
* Dont but multiple statements on one line. 
  * Simple List comprehenision and Teriary conditions are acceptable. 

```python 
# DONT

if condition == True: return True
else: return False

# DO 
if condition == True: 
  return True
else: 
  return False
  
# List comprehension is also acceptable 
list = [x + 1 for x in listOfNumbers]
```

* strings should be 'single quoted' 
* Docstrings should use three """ Double Quotes """
* Put multi-line strings in paretheisis

## Imports 
* Never use wildcard imports 
```python
# DONT 
from PySide2.QtWidgets import *
widget = QLabel() 

# DO
from PySide2 import QtWidgets
widget = QtWidgets.QLabel()
```

* Modules should be imported at the top of a file 
* Organize inputs into three blocks 
  * python standard imports 
  * 3rd party imports 
  * submodules within the same package
* Imports should be in alphabetical order
* Dont rename imports using `as`
* Dont do multiple imports on the same line 

```python
# PYTHON
import os 
import sys 

# THIRD PARTY
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# SUBMODULES 
from rigamajig2.maya import something
```

## Modules 
* Whenever possible use `__all__` to define parts of a module intended for later use. 

## Class 
* Avoid using metaclasses. Subclasses are prefectly fine
* Do not rename the `self` keyword
* Use discriptive class names
* Dont use "test" in any method names. That is reserved for unittests. 

## Class Methods
* Class methods use `camelCase`
* Class mathods should start with a verb. (ie. `get`, `do`, `execute`, `create`, `update`, `find`, `set`)
* Class method names should be readable and discriptive

## Returns 
* all returns in a function or method must be the same type and length. 
```python
# DONT 
def myBadFunction(var):
  if var: 
    return 1
  else:
    return "Some String"

# DO 
def myGoodFunction(var):
  if var: 
    return 1
  else:
    return 0
```
* Must have a return at the end of a nested if else statement if there are any returns

## Documentation (Docstrings)
* All `classes`, `functions`, and `methods` must have a docstring discription. 
* `functions` and `methods` should specify a `rtype` if they return anything. 
* `functions` and `methods`  should specify any raised errors if any.

## Aurguments
* Functions should have no more than `10` arguments
* Never use mutables as default argument types.
When passing a mutable value as a default argument in a function, the default argument is mutated anytime that value is mutated.
Here, "mutable value" refers to anything such as a list, a dictionnary or even a class instance.
  * In short: Dont use (`list`, `dict`, `class`) as default arguments in functions

* Arguments that are longer than 120 lines should be broken into many lines. 

## Decorated Methods 
* Use at `@classmethod` and `@staticmethod`
* Use `@property` and `@property.setter` to access class acessor properties
* Use `@property` instead of class acessor
* Put `@property` and `@property.setter` next to eachother

## Unittest
* All unittests shold derive from the `mayaUnitTest.TestCase` class

## Maya 
* Dont use pymel! It can be handy for prototyping but it is SLOW. OpenMaya can provide all the same functionality. 
* always use `import maya.cmds as cmds`
* Use long names for `maya.cmds` functions 
  * `q` is ok for query
  * `e` is ok for edit
  * some other arguments can use the short name as well. IF they are clear and readable.


