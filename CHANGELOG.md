# Change Log 


## 1.0.2


### Added: 
* Added unittests for components, component connections and archetypes. 
* Added smart switch function: `ikfkSwitcher.switchSelectedComponent()`
Smart switch allows the animator to select any control within a component
that allows ikfk blending (`limb.limb`, `arm.arm`, `leg.leg`).
* added a versioning system to the components. 

### Changed: 
* changed the name of `meta.addMessageConnection` to `meta.createMessageConnection`. 
* changed the name of `container.listNodes` to `container.getNodesInContainer`
## 1.0.1

### Added: 
* Updated the  set driven key system to use the maya API. 
* Implemented the pose set driven key control to the hand.hand component. 
It works with any number of fingers over 3. 
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
 