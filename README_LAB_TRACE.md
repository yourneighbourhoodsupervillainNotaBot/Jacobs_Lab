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



####################################################


python lab_cli.py trace fold --demo fold --inspect
python lab_cli.py trace triangle --loops 3 --inspect
python lab_cli.py trace flexagon --inspect
python lab_cli.py trace category --inspect
python lab_cli.py trace pathfinding --inspect
python lab_cli.py trace three-body --periods 2 --inspect
python lab_cli.py trace fold-complexity --inspect

python lab_cli.py trace pathfinding --start-pos 1,1 --goal 8,7 --save traces/pathfinding.json
python lab_cli.py trace three-body --periods 2 --sample-every 20 --save traces/three_body.json
python lab_cli.py trace fold-codec --codec palindrome --save traces/fold_codec.json
python lab_cli.py trace fold-complexity --save traces/fold_complexity.json
python lab_cli.py trace prime --limit 40 --vm-limit 12 --save traces/prime.json
python lab_cli.py trace universality --max-functions 10 --save traces/universality.json


python lab_cli.py trace triangle --loops 3 --save traces/triangle.json
python lab_cli.py sonify traces/triangle.json traces/triangle.wav

python lab_cli.py trace fold --demo while --save traces/fold_while.json
python lab_cli.py sonify traces/fold_while.json traces/fold_while.wav

python lab_cli.py trace three-body --periods 2 --save traces/three_body.json
python lab_cli.py sonify traces/three_body.json traces/three_body.wav