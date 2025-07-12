path='/home/erwan/GIT_PERSO/scruteNet'
config=$path/config/config.json
python='/home/erwan/venv/index/bin/python'

$python $path/scrute.py   $config &
$python $path/monitor.py  $config &
$python $path/resolve.py  $config &

cd $path/web
FLASK_APP='SQLookRunner'
/home/erwan/venv/index/bin/flask run
