export PATH="$PATH:/Users/ahmedhassan/development/flutter/flutter/bin"

PATH="/usr/local/bin:$PATH"
export PATH="/opt/homebrew/opt/openjdk@11/bin:$PATH"
source /opt/homebrew/opt/chruby/share/chruby/chruby.sh
source /opt/homebrew/opt/chruby/share/chruby/auto.sh
chruby ruby-3.3.0

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/Users/ahmedhassan/miniconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/Users/ahmedhassan/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/Users/ahmedhassan/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/Users/ahmedhassan/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<


# Added by Antigravity
export PATH="/Users/ahmedhassan/.antigravity/antigravity/bin:$PATH"

# Added by Antigravity IDE
export PATH="/Users/ahmedhassan/.antigravity-ide/antigravity-ide/bin:$PATH"

# Added by codebase-memory-mcp install
export PATH="/Users/ahmedhassan/.local/bin:$PATH"
