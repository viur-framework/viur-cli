#!/usr/bin/env bash
if [[ $(basename $SHELL) = 'bash' ]];
then
    if [ -f ~/.bashrc ];
    then
        echo "Installing bash autocompletion..."
        grep -q 'viur-autocompletion' ~/.bashrc
        if [[ $? -ne 0 ]]; then
            echo "" >> ~/.bashrc
            echo 'eval "$(_VIUR_COMPLETE=bash_source viur)"' >> ~/.viur-autocompletion.sh
            echo "source ~/.viur-autocompletion.sh" >> ~/.bashrc
        fi
    fi
elif [[ $(basename $SHELL) = 'zsh' ]];
then
    if [ -f ~/.zshrc ];
    then
        echo "Installing zsh autocompletion..."
        grep -q 'ecli-autocompletion' ~/.zshrc
        if [[ $? -ne 0 ]]; then
            echo "" >> ~/.zshrc
            echo "autoload bashcompinit" >> ~/.zshrc
            echo "bashcompinit" >> ~/.zshrc
            echo 'eval "$(_VIUR_COMPLETE=source ecli)"' >> ~/.viur-autocompletion.sh
            echo "source ~/.viur-autocompletion.sh" >> ~/.zshrc
        fi
    fi

fi
