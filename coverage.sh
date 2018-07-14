#!/bin/bash
# Runs a unittest coverage and opens the results in the user's default
# browser.
coverage run -m unittest discover
coverage html
xdg-open htmlcov/index.html
