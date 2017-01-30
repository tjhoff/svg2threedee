  # ess vee gee to three dee
  ## this doesn't actually do anything but parse SVG into a list of connected points right now!
  ### I'm working on triangulation of nested paths currently.

 To set up: `./setup.sh`

 To run: either use pycharm (should detect the virtualenv automatically) or `source venv/bin/activate` then run `stlify.py` with a file name (e.g. `test_svg/squares_cut.svg`)

To test: install pytest (`pip install pytest`) in the virtualenv and run it (`py.test`) in the git root. If you initialize virtualenv without the setup script, be sure to add your virtualenv directory to the `[norecurse]` directories in `pytest.ini`.
