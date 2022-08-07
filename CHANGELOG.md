# Change Log 

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
 