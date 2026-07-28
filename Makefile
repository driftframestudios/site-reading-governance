.PHONY: validate test

validate:
	python3 tools/validate_governance.py
	python3 tools/check_language.py

test:
	python3 -m unittest discover -s tests -v

