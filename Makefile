.PHONY: check editorial validate test

check: validate editorial test

validate:
	python3 tools/validate_governance.py

editorial:
	vale --config=.vale.ini --no-global --minAlertLevel=warning .

test:
	python3 -m unittest discover -s tests -v
