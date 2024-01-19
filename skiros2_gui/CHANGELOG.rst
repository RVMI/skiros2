^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package skiros2_gui
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1.0.5 (2020-06-09)
------------------
* Fix mistake in previous commit
* Printing output log also when not saving
* Added possibility to filter log output.
* Releasing buttons and log if skill mgr crashes.
* Merge remote-tracking branch 'origin/rvmi/develop' into develop
* Merge pull request `#26 <https://github.com/RVMI/skiros2/issues/26>`_ from RVMI/modifyRelation-labels
  Fix: labels not showing up in modify relation dialog
* Fix to `#24 <https://github.com/RVMI/skiros2/issues/24>`_
* fix labels not showing up in modify relation dialog
* Merge remote-tracking branch 'rvmi/develop' into develop
* Merge branch 'develop' into develop-rss
  # Conflicts:
  #	skiros2/scripts/install_fd_task_planner.sh
* Merge remote-tracking branch 'origin/rvmi/develop' into develop
* Contributors: Francesco Rovida, Matthias Mayr, emmanuelkring, francesco

1.0.4 (2020-03-04)
------------------
* Merge pull request `#23 <https://github.com/RVMI/skiros2/issues/23>`_ from RVMI/py3-fixes
  Py3 fixes
* Python3 fixes in skiros2_gui
* Fix in add relation
* Sorting elements when adding a new object. Fix in log saving.
* Fix on GUI shortcuts and Element hasRelation function.
* Use also 'plus' as a 'space' shortcut
* Bug-fix for elements sometimes not appearing in GUI
* Added assertions to guard skill execution return value
* Added more documentation. Removed obsolete files. Moved generated files (e.g. logs and plans) into ~/.skiros folder. Simplified planner installation, that now doesn't modify system path.
* Fixed error introduced in commit 21f6693e61ac9efacaf4d341642a777dd477a2e5 making GUI crash when changing label property.
* Fix for possible crash reason on start
* Supporting input of lists in properties from the GUI
* Removed obsolete attribute _is_list from Property class.
* Finish improved-debugging-tools
* 1.0.3
* Updated changelog
* Finish gui-improved-visualization
* Added guards to avoid gui crash.
* Contributors: DavidWuthier, Francesco Rovida, RvmiLab, emmanuelkring

1.0.3 (2019-09-16)
------------------
* Finish gui-improved-visualization
* Added guards to avoid gui crash.
* Contributors: Francesco Rovida

1.0.2 (2019-08-26)
------------------
* Merge branch 'master' into develop
* Finish gui-improved-visualization
* Printing SLOW tag to primitives running with a period above 40msec.
* Updated changelog
* Contributors: RvmiLab, Francesco Rovida

1.0.1 (2019-05-22)
------------------
* Bug-fix in gui with bool parameters
* Contributors: RvmiLab

1.0.0 (2019-04-30)
------------------
* Merge pull request `#11 <https://github.com/RVMI/skiros2/issues/11>`_ from matthiashh/matthias-devel-pycodestyle
  Matthias devel pycodestyle
* Merge branch 'develop' into matthias-devel-pycodestyle
* Merge pull request `#8 <https://github.com/RVMI/skiros2/issues/8>`_ from matthiashh/skiros_widget_config
  Enabled empty configuration function for skiros_widget.
* Merge branch 'develop' into matthias-devel-pycodestyle
* Removed match blackboard feature.
* Merged 'develop' into 'pycodestyle'.
* Finish plan-in-the-tree
* Enabled empty configuration function for skiros_widget.
  skiros_gui dies if rqt configuration button is pressed and this function
  doesn't exist.
* Applied pycodestyle (pep8) with "--aggresive"
  This should fix most violations of pep8.
  Excemptions were made for manually structured code through tabs.
* Removed old BSD headings and minor bug-fixes
* Bug-fix for boolean parameters in GUI
* Added more tooltips to GUI elements
* Stretched param section in GUI layout
* Added timeout to kill blocked BTs. Minor improvements on GUI
* GUI improvements: BT execution visualization and more intuitive interface
* Implemented visualization of active tasks
* Changed license to LGPL-3.0-or-later and updated changelog
* Updated version and changelog file
* Contributors: Francesco Rovida, Matthias Mayr, Francesco Rovida

0.1.0 (2018-09-27)
------------------
* Bug-fix in GUI. Changed Idle status handling in BT Parallel processors.
* Changed log format
* Finish wm-restructure
* Added commands for installation
* Improved GUI and interfaces
* Bug-fixes
* Changed world model interfaces methods to snake case
* Started restructuring
* Removed obsolete package skiros_resource. Added Property msg and changed WmElement And WmMonitor msgs. Changed serialization accordingly.
* Bug fix in remapping and several bug-fix on the GUI.
* Decreased output verbosity on GUI
* Simplified and cleaned memorization and print of skills' progresses. Now also printing the skill's parent name for clearer reading.
* Added time from start to skill progress.
* Added GUI tab to log skills execution
* Tested multiple task execution/stop. Now skill manager can instantiate new skills when available ones are already running.
* Bug-fix in GUI skill's parameters
* Further improvements to BT execution rate: decreased queries to wm and added interface to update only element properties. Bug fix on skills reset.
* Patch to always refresh WM view when starting the GUI
* Completed interface for dynamic sync with wm
* Optimized GUI
* GUI Bugfix
* Bugfix GUI: Move objects spatially in tree
* Autoscroll for progress messages
* Autoscroll for progress messages
* Feature: Progress output
* Added progress output
* Changed parameter types (`#10 <https://github.com/RVMI/skiros2/issues/10>`_)
  * Changed skill tab: added system parameters as mandatory and added empty field in optional parameters
  * Bug-fix in skill reset and adding element to world model.
  * Changed base parameters types. Removed World and Config became Required.
  * Added gui launch in world_model_server.launch
  * Fix avoiding gui crashing when a parameter is not specified
  * Removed System from ParamTypes
  * Setting name of the scene on the GUI according to init_scene parameter
* Setting name of the scene on the GUI according to init_scene parameter
* Fix avoiding gui crashing when a parameter is not specified
* Changed skill tab: added system parameters as mandatory and added empty field in optional parameters (`#9 <https://github.com/RVMI/skiros2/issues/9>`_)
* Changed skill tab: added system parameters as mandatory and added empty field in optional parameters
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
* Finish WP4_gui
  # Conflicts:
  #	skiros2_world_model/src/skiros2_world_model/ros/world_model_server.py
* Minor fixes
* Allow fast property update in GUI
* Fixed bug in instanciate function. Fixed bug in the gui's add and remove object buttons.
* GUI update on wm changes
* Bug-fix in GUI set parameters. And changed interactive markers visualization
* Fixed bug in interactive markers
* Skill in success state are no more bypassed by visitor (are executed again). Other minor changes on output
* Added interactive markers feedback to change to objects position
* Changed all author_name with widget_id
* Fixed author name for world model modifcations. Fixed remove of objects
* 0.0.2
* Changelogs added
* Merge pull request `#2 <https://github.com/RVMI/skiros2/issues/2>`_ from ipa-led/master
  Fixed CMakeLists and package.xml inconsistencies
* Removed Include lines in skiros2_gui
* Fixed CMakeLists and package.xml inconsistencies
* GUI development (wm add/remove/modify) in progress
* Started GUI for WM: Add objects
* Development of GUI - WM tab
* Started GUI for WM: Add objects
* First commit
* Contributors: Bjarne Grossmann, DavidWuthier, Francesco Rovida, Ludovic Delval, Francesco Rovida, ipa-led
