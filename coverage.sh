#!/bin/bash
# Runs a unittest coverage and opens the results in the user's default
# browser. We don't exclude the tests themselves from coverage, so we
# can go completely meta and check that our tests are covered.
coverage run -m unittest discover
coverage html
xdg-open htmlcov/index.html
