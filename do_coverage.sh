OMIT=""
coverage run --source='.' --omit=$OMIT -m unittest discover
coverage html
xdg-open htmlcov/index.html
