# Lab Trace Layer

This layer adds a unified trace/event system, inspector UI, save/load support,
and headless export for the folding laboratory.

## Test the lab layer

```bash
python lab_cli.py test

Build traces

python lab_cli.py trace triangle --loops 2 --inspect
python lab_cli.py trace test-walk --inject-failure --save traces/test_walk.json
python lab_cli.py trace fold --demo fold --save traces/fold.json
python lab_cli.py trace flexagon --save traces/flexagon.json
python lab_cli.py trace category --save traces/category.json

Inspect saved traces

python lab_cli.py inspect traces/fold.json

Export traces

python lab_cli.py export traces/fold.json traces/fold.json
python lab_cli.py export traces/fold.json traces/fold.txt
python lab_cli.py export traces/fold.json traces/fold.html
python lab_cli.py export traces/fold.json traces/fold.png