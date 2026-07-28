.PHONY: check validate test

check: validate test

validate:
	python3 tools/validate_governance.py
	python3 tools/check_language.py
	python3 tools/scan_secret_shapes.py

test:
	python3 -m unittest discover -s tests -v
