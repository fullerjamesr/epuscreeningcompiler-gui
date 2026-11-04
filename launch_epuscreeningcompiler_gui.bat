@echo off
rem Launches the EPU Screening Compiler GUI from its conda environment.
rem
rem SETUP: edit the CONDA_ROOT line below for this PC, then double-click this file
rem (or make a desktop shortcut to it).
rem   CONDA_ROOT: the folder that contains "Scripts\activate.bat" (e.g. the miniconda3 or anaconda3 folder).
rem               In an Anaconda Prompt, "where conda" prints a path inside it.
rem Requires epuscreeningcompiler-gui to be pip-installed in the "epuscreeningcompiler" conda environment.
rem Troubleshooting: change "pythonw" to "python" to keep a console open and see error messages.

set "CONDA_ROOT=C:\PATH\TO\miniconda3"

call "%CONDA_ROOT%\Scripts\activate.bat" epuscreeningcompiler
pythonw -m epuscreeningcompiler_gui
