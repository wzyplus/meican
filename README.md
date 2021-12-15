# Meican

1. Clone
    ```
    git clone https://github.com/wzyplus/meican.git ~/.meican
    ```
1. Add to $PATH
    ```
    # for bash
    echo 'export PATH=$HOME/.meican/bin:$PATH' >> ~/.bashrc

    # for zsh
    echo 'export PATH=$HOME/.meican/bin:$PATH' >> ~/.zshrc
    ```
1. Install python requirements (need python3)
    ```
    meican install-requirements
    ```
1. Config username, password
    ```
    meican config auth.username xxxxxx
    meican config auth.password xxxxxx
    ```
1. Pay
    ```
    meican qrpay jiduo
    ```
1. Show help
    ```
    meican -h
    ```
