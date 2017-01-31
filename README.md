# ess vee gee to three dee

## It's super slow (O(n^2) where n is # lines, but it works for single polygons (no nesting right now)

 To set up: `./setup.sh`

 To run: either use pycharm (should detect the virtualenv automatically) or `source venv/bin/activate` then run `stlify.py` with a file name (e.g. `test_svg/squares_cut.svg`)

To test: install pytest (`pip install pytest`) in the virtualenv and run it (`py.test`) in the git root. If you initialize virtualenv without the setup script, be sure to add your virtualenv directory to the `[norecurse]` directories in `pytest.ini`.
