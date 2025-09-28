#-----------------------------------------------------------------------------
set(MODULE_NAME tavi_analytics)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

set(MODULE_PYTHON_PACKAGE_DIRS
  core
  module1
  module2
  module3
  module4
  module5
  module6
  services
  ui
  utils
  widgets
  )

foreach(package_dir ${MODULE_PYTHON_PACKAGE_DIRS})
  file(GLOB_RECURSE package_python_files
    RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
    LIST_DIRECTORIES false
    ${package_dir}/*.py
    )
  list(APPEND MODULE_PYTHON_SCRIPTS ${package_python_files})
endforeach()
list(REMOVE_DUPLICATES MODULE_PYTHON_SCRIPTS)
list(REMOVE_ITEM MODULE_PYTHON_SCRIPTS __init__.py)

set(MODULE_PYTHON_RESOURCES
  config.json
  Resources/Icons/${MODULE_NAME}.png
  Resources/UI/${MODULE_NAME}.ui
  Resources/valve_config.json
  Resources/valve_plane_config.json
  Resources/valve.nrrd
  )

file(GLOB MODULE_ADDITIONAL_RESOURCES
  RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
  LIST_DIRECTORIES false
  Resources/Icons/*
  Resources/UI/*
  )
list(APPEND MODULE_PYTHON_RESOURCES ${MODULE_ADDITIONAL_RESOURCES})
list(REMOVE_DUPLICATES MODULE_PYTHON_RESOURCES)

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
