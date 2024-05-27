#!/bin/bash

source_code="main.py"
last_code_md5=""

while true
do
    current_code_md5=$(md5sum $source_code | cut -d' ' -f1)

    if [ "$current_code_md5" != "$last_code_md5" ]; then
        echo "Code has changed, restarting program..."
        pkill -f "python $source_code"

        python $source_code &
        last_code_md5=$current_code_md5
    fi

    sleep 1
done

!/bin/bash

# dir_path=$(dirname "$0")
# last_md5=""

# while true
# do
#     current_md5=$(find $dir_path -type f -exec md5sum {} \; | md5sum | cut -d' ' -f1)

#     if [ "$current_md5" != "$last_md5" ]; then
#         echo "Files have changed, restarting program..."
#         pkill -f "python $dir_path/*.py"

#         python $dir_path/main.py &
#         last_md5=$current_md5
#     fi

#     sleep 1
# done
