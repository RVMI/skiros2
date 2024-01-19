^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package skiros2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1.0.5 (2020-06-09)
------------------
* Merge pull request `#31 <https://github.com/RVMI/skiros2/issues/31>`_ from ipa-led/launch_test
  added simple launch test to skiros2 package
* added simple launch test to skiros2 package
* Added CadModel data property.
* Merge remote-tracking branch 'origin/rvmi/develop' into develop
* Fix to `#24 <https://github.com/RVMI/skiros2/issues/24>`_
* Merge branch 'develop' into develop-rss
  # Conflicts:
  #	skiros2/scripts/install_fd_task_planner.sh
* Merge remote-tracking branch 'origin/rvmi/develop' into develop
* Removes installation of g++ and make from install script.
* Fix: Adds # to a comment that will be put in bashrc.
* Enhancement: Adds installation of build dependencies when installing planner.
* Fix: Puts correct TDF variables in bashrc even when installation was skipped.
* Merge remote-tracking branch 'origin/rvmi/develop' into develop
* Install script: Adds missing exit statement.
* Install script: Changed suggested folder and check if it's already existent.
* Contributors: Francesco Rovida, Ludovic Delval, Matthias Mayr, francesco

1.0.4 (2020-03-04)
------------------
* Added more documentation. Removed obsolete files. Moved generated files (e.g. logs and plans) into ~/.skiros folder. Simplified planner installation, that now doesn't modify system path.
* Added force properties to ontology.
* Finish improved-debugging-tools
* Minor fix in skiros.launch
* 1.0.3
* Updated changelog
* Corrected script for install planner.
* Made scene subclass of Object
* Contributors: Francesco Rovida

1.0.3 (2019-09-16)
------------------
* Corrected script for install planner.
* Made scene subclass of Object
* Merge remote-tracking branch 'scalable/master'
* Merge pull request `#7 <https://github.com/RVMI/skiros2/issues/7>`_ from ScalABLE40/catkin_linted
  Catkin linted
* linted packages.xml and CMakeLists.txt
  * install install bash scripts
  * makes everything exec_depend
* removed owl files executable
* Contributors: Francesco Rovida, Ludovic Delval, Francesco Rovida

1.0.2 (2019-08-26)
------------------
* Merge branch 'master' into develop
* Added launch file for complete skiros system.
* Added TFTimeStamp to ontology
* Added datatype property PushToFrameId.
* Added transformation templates and fix in skill interface
* Updated changelog
* Contributors: Bjarne Grossmann, Francesco, RvmiLab

1.0.1 (2019-05-22)
------------------
* Added Velocity data property to ontology
* Added output screen in launch
* Contributors: RvmiLab

1.0.0 (2019-04-30)
------------------
* Planner uses hold conditions
* Added xterm ros dependency
* Merged 'develop' into 'pycodestyle'.
* Finish plan-in-the-tree
* Added extra properties to test robot hardware
* Changed test camera type
* Changed license to LGPL-3.0-or-later and updated changelog
* Updated version and changelog file
* Contributors: Matthias Mayr, RvmiLab, Francesco Rovida

0.1.0 (2018-09-27)
------------------
* Finish wm-restructure
* Specified Weight datatype
* Added commands for installation
* Added parameter to load automatically contexts on wm. Fix in context save function.
* Added depthcamera class
* Started restructuring
* Cleaned obsolete dependencies on and launch files for skiros2_resource manager
* Decreased output verbosity on GUI
* Optimized PDDL problem generation. Task planner returns success if replan is empty. Adding relation hasTemplate to all elements with a template. Added utility functions to world element and pddl interface.
* Reverted change to launch files. Changed evaluation of relation conditions. Bug fix in task manager interface.
* Changed Task manager control from service to action. Added verbosity option. Added support for universal quantifier.
* Added deploy variable to launch files in order to disable xterm prefix
* Added deploy variable to launch files in order to disable xterm prefix
* Specified required properties for Physical things in ontology
* Changed parameter types (`#10 <https://github.com/RVMI/skiros2/issues/10>`_)
  * Changed skill tab: added system parameters as mandatory and added empty field in optional parameters
  * Bug-fix in skill reset and adding element to world model.
  * Changed base parameters types. Removed World and Config became Required.
  * Added gui launch in world_model_server.launch
  * Fix avoiding gui crashing when a parameter is not specified
  * Removed System from ParamTypes
  * Setting name of the scene on the GUI according to init_scene parameter
* Added gui launch in world_model_server.launch
* Integration of AAU developments (`#3 <https://github.com/RVMI/skiros2/issues/3>`_)
  * Added support to run skiros under a ROS namespace. Updated readME.
  * Bug-fix when using a namespace. Implemented simple policy for wm to stay up until clients are correctly disconnected.
  * Added getIndividuals function to ontology interface
  * Started GUI for WM: Add objects
  * Bug-fix in getIndividuals function
  * Decreased ourput verbosity of skill manager
  * Handling spatial reasoner in properties of the world element
  * Access properties in world element
  * Changed isList function in property class.
  * Bug-fix for unicode/str serialization. Removed spaces in utils.py
  * Bug-fix on world model getIndividual. Removed spaces from world model.py
  * Development of GUI - WM tab
  * Started GUI for WM: Add objects
  * GUI development (wm add/remove/modify) in progress
  * Extended property condition with support for different operators. Added loop decorator. Minor change in world model server init.
  * Skill type is now set automatically to the class name
  * Fixed author name for world model modifcations. Fixed remove of objects
  * Changed all author_name with widget_id
  * Added interactive markers feedback to change to objects position
  * Bug-fix in param makeDefault and setValues functions
  * Bug-fix in world model load. On boot, skill manager remove old skill from the scene before adding new ones.
  * Skill in success state are no more bypassed by visitor (are executed again). Other minor changes on output
  * Checking file existence before loading scene.
  * Bug-fix
  * Added sequential operator and made it default.
  * Fixed bug in interactive markers
  * Added or condition. Change in param handle printState
  * Bug-fix in GUI set parameters. And changed interactive markers visualization
  * GUI update on wm changes
  * Fixed bugs with elements caching
  * Fixed bug in instanciate function. Fixed bug in the gui's add and remove object buttons.
  * Allow fast property update in GUI
  * Minor fixes
  * Bug-fix in skill manager naming
* Merge pull request `#1 <https://github.com/RVMI/skiros2/issues/1>`_ from ScalABLE40/master
  IPA changes integration
* 0.0.2
* Changelogs added
* Added support to run skiros under a ROS namespace. Updated readME.
* Merge pull request `#1 <https://github.com/RVMI/skiros2/issues/1>`_ from RVMI/master
  Added robot discovery mechanism and execution monitor
* Changed robot_description output
* Changed output of robot_description. Updated robot name in task mgr launch
* Added camera to test robot (for planning pick and place)
* Added location, gripper, and arm to test robot
* Added a default pose to test robot
* First commit
* Contributors: Bjarne Grossmann, Francesco Rovida, Francesco Rovida, ipa-led
