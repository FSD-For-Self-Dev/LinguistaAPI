#!/bin/bash

source_code="main.py"
last_code_md5=""

while true
do
    current_code_md5=$(md5sum $source_code | cut -d' ' -f1)

    if [ "$current_code_md5" != "$last_code_md5" ]; then
        echo "Code has changed, restarting program..."
        pkill -f "python $source_code"  # Команда для убийства процесса Python

        python $source_code &  # Запуск Python в фоновом режиме
        last_code_md5=$current_code_md5
    fi

    sleep 1
done

!/bin/bash

# dir_path=$(dirname "$0")  # Получаем путь к директории, в которой находится скрипт
# last_md5=""

# while true
# do
#     current_md5=$(find $dir_path -type f -exec md5sum {} \; | md5sum | cut -d' ' -f1)

#     if [ "$current_md5" != "$last_md5" ]; then
#         echo "Files have changed, restarting program..."
#         pkill -f "python $dir_path/*.py"  # Команда для убийства всех процессов Python в данной директории

#         python $dir_path/main.py &  # Запуск main.py в фоновом режиме
#         last_md5=$current_md5
#     fi

#     sleep 1
# done
