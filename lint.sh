#! /bin/sh

pip install pycodestyle
current_branch="$CI_BUILD_REF_NAME"
echo $current_branch
all_changed_files=$(git diff --name-only '*.py')
echo "Checking changes!"
for each_file in $all_changed_files
do
# Checks each newly added file change with pycodestyle
pycodestyle $each_file
error_count=$(pycodestyle $each_file --count | wc -l)
if [ $error_count -ge 1 ]; then
    exit 1
fi
if [ $error_count -eq 0 ]; then
    exit 0
fi
done
echo "Completed checking"
