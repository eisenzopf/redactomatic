$pythonCmd = "py -3.10"

$pythonCmd -m pip install pip
$pythonCmd -m pip install --upgrade pip
$pythonCmd -m pip install -r requirements.txt
$pythonCmd -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
$pythonCmd -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl