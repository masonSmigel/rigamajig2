# Change Log 


## 1.0.7

### Added:
* UvPin rivet to `rigamjig2.maya.constrain`. This uses a single Uv pin node to output 
multiple matricies for a mesh based on UV coords. it can be used as a more opitmal folicle system.
* Added the `basic.basicArray` to create multiple basic components with a similar rig parent from 
within a single rig component.
* Added a `squash.splineSquash` component for usage on the head squash and stretch. 
This also includes the implementation of a bpm setup for stacking skin clusters.  


### Changed: 
* the `rigamajgi2.maya.constrain.negate` no longer creates a parent relationship between the driver and driven. 
This was changed to make the funciton more adaptable. 
* load SHAPEs can now accept a file or a directory. Selecting a directory loads all `.mel` files in that directory.
* using mayaMixin made the main builder dialog dockable. 


### Fixed: 
* issue loading single skin from the builder dialog. 

## 1.0.6

### Added: 
* Simple jaw component with auto jaw push. 
* A proper prop archetype
* Space switches to the basic component. 
* Added deform layer setup to the builder dialog. This allows the user to setup a chain of deformations.

### Changed: 
* Fixed bug with paths preventing the tool from being loaded properly on windows computers. 
* Added the option to save the selected joints if there is no `skeleton_root`. 
* Fixed issue with the paths preventing the user from setting a new path or setting a path to None
* Moved the old jaw component to the sandbox. 
* Fixed an issue with loading skinweights where non-existant skinweights would cause the step to stop. 

## 1.0.5


### Added: 
* Added `guide` step to builder. This step is split off from `initialize` which 
now is just the creation of the container while `guide` creates the guides and additional setup.
* Added space switch the the FK limb instead of just the swing control. 
* Added physical cup controls to the `hand` component.
* Added "ballSwivel" attribute to the `leg` component.
* Added "import SHAPES Data" to builder.
* Added icons to the builder UI. 
* Added value parameter to the `interpJoint` function
* Added Swing and twist combo values to the Psd Reader. 

### Changed: 
* updated `curve_data` to replace existing shapes if cvs dont match 
* Unlocked the translate on the FK limbs for finer control. 
* Moved the visability for the "bind" group to the "main" control. 

### Fixed: 
* Bug with relative paths not being generated from `pathSelector`
* Bug in the `savePsdData` that caused only twist to be saved. 

## 1.0.4


### Added: 
* Added `editComponentParameters` dialog to the component manager. 
This dialog allows the user to edit the parameters without diving into the attribute editor
* Added `mirrorComponentParameters` and `createMirroredComponent` options to the component manager. 
These funcitons aide in managing and creating new components. 
  * `mirrorComponentParameters` will attempt to process and create a mirror name for all appropriate parameters in a component. 
  * `createMirroredComponent` will create a new mirrored compponent and mirror the parameters. 

### Changed: 
* refactored `_lookForComponents` and changed name to `findComponents`


## 1.0.3


### Added: 
* Implemented archetype layering system. Shared data can be stacked via the 
pre_script, post_script, and pub_scripts. Rigs will inherit all scripts from all 
previous archetypes. 
  * Note: all archetypes inherit from base. Core rig functionaly should be stored here. 
* Added `joint.createInterpJoint` to the joint module. This will create a joint that blends 
transformation between the given joint and a parent. 
An attribute is provided on the new joint for to control the interpolation. 

### Changed: 
* refactored the name of `rig_builder` to `builder`
* refactored `builder.utils` to `builder.core`

## 1.0.2


### Added: 
* Added unittests for components, component connections and archetypes. 
* Added smart switch function: `ikfkSwitcher.switchSelectedComponent()`
Smart switch allows the animator to select any control within a component
that allows ikfk blending (`limb.limb`, `arm.arm`, `leg.leg`).
* Added a versioning system to the components. 
* Added some metadata to the main group of a finalized rig. This is added in the `finalize`step.
Data includes: 
  * Rigamajig version
  * Creation user 
  * Creation date
### Changed: 
* Changed the name of `meta.addMessageConnection` to `meta.createMessageConnection`. 
* Changed the name of `container.listNodes` to `container.getNodesInContainer`


## 1.0.1

### Added: 
* Updated the  set driven key system to use the maya API. 
* `hand.hand v1.0.2` Implemented the set driven key control to the component. 
* added a versioning system to the components. 
    

## 1.0.0

initial start of the change log

### Added: 
* First version of the rigging system. it includes: 
    - components (pre-configured rig systems)
    - framework and utilities 
    - user interface 
    
 
### Changed: 

### Removed: 
 