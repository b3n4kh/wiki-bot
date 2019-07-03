#!/bin/sh

read -p 'Username: ' uservar
read -p 'Password: ' passvar
read -p 'Host: ' hostvar

which direnv && OUT=.envrc || OUT=~/.profile

cat <<EOF >>$OUT
export BOT_USER='${uservar}'
export BOT_PASSWORD='${passvar}'
export BOT_HOST='${hostvar}'
export FLASK_APP=web
eval "$(_WIKIBOT_COMPLETE=source wikibot)"
#export BOT_DEBUG=True
EOF

which pip3 && pip3 install --user -r requirements.txt

sudo ln -s $PWD/bot.py /usr/local/bin/wikibot
