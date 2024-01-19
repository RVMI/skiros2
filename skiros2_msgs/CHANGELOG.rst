^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package skiros2_msgs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1.0.5 (2020-06-09)
------------------
* Merge remote-tracking branch 'origin/rvmi/develop' into develop
* Merge remote-tracking branch 'origin/rvmi/develop' into develop
* Contributors: Matthias Mayr

1.0.4 (2020-03-04)
------------------
* Finish improved-debugging-tools
* 1.0.3
* Updated changelog
* Sending processor in skill progress
* Contributors: Francesco Rovida

1.0.3 (2019-09-16)
------------------
* Sending processor in skill progress
* Contributors: Francesco Rovida

1.0.2 (2019-08-26)
------------------
* Merge branch 'master' into develop
* Finish gui-improved-visualization
* Printing SLOW tag to primitives running with a period above 40msec.
* Updated changelog
* Contributors: Francesco Rovida

1.0.1 (2019-05-22)
------------------

1.0.0 (2019-04-30)
------------------
* Merged 'develop' into 'pycodestyle'.
* Finish plan-in-the-tree
* GUI improvements: BT execution visualization and more intuitive interface
* Changed license to LGPL-3.0-or-later and updated changelog
* Updated version and changelog file
* Contributors: Matthias Mayr, Francesco Rovida

0.1.0 (2018-09-27)
------------------
* Finish wm-restructure
* Improved GUI and interfaces
* Completed and tested implementation of wm contexts
* Started restructuring
* Removed obsolete package skiros_resource. Added Property msg and changed WmElement And WmMonitor msgs. Changed serialization accordingly.
* Bug fix in remapping and several bug-fix on the GUI.
* Simplified and cleaned memorization and print of skills' progresses. Now also printing the skill's parent name for clearer reading.
* Added time from start to skill progress.
* Further improvements to BT execution rate: decreased queries to wm and added interface to update only element properties. Bug fix on skills reset.
* Completed interface for dynamic sync with wm
* Simplified and improved skill managers discovery mechanism
* Changed Task manager control from service to action. Added verbosity option. Added support for universal quantifier.
* Merge pull request `#1 <https://github.com/RVMI/skiros2/issues/1>`_ from ScalABLE40/master
  IPA changes integration
* 0.0.2
* Changelogs added
* Merge pull request `#2 <https://github.com/RVMI/skiros2/issues/2>`_ from ipa-led/master
  Fixed CMakeLists and package.xml inconsistencies
* Fixed CMakeLists and package.xml inconsistencies
* Merge pull request `#1 <https://github.com/RVMI/skiros2/issues/1>`_ from RVMI/master
  Added robot discovery mechanism and execution monitor
* Finish WP5_task_feedback (preliminary)
  # Conflicts:
  #	skiros2_common/src/skiros2_common/core/abstract_skill.py
* Added progress message and publisher
* Finish WP5_robot_discovery (preliminary)
* Optimized some code;
  Added dummy sub and pub for robot discovery
* First commit
* Contributors: Bjarne Grossmann, Francesco Rovida, Ludovic Delval, Francesco Rovida, ipa-led
