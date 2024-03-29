#!/bin/bash

which git || exit 1

function compute_version() {
    git fetch --tags
    current_version=$(git describe --tags `git rev-list --tags --max-count=1`)
    if [ ! -z "${current_version}" ]; then
        major_version=$(echo $current_version | awk '{split($0,a,"."); print a[1]}')
        minor_version=$(echo $current_version | awk '{split($0,a,"."); print a[2]}')
        update_version=$(echo $current_version | awk '{split($0,a,"."); print a[3]}')

        if [ $(($update_version + 1)) -ge 11 ]; then
            update_version=0
            minor_version=$((${minor_version} + 1))
        else
            update_version=$(($update_version + 1))
        fi
    fi

    latest_version="${major_version}.${minor_version}.${update_version}"

    git config user.email "rugging24@gmail.com"
    git config user.name "Olakunle Olaniyi"
    poetry version ${latest_version}
    git add pyproject.toml
    git commit -m "project version update ${latest_version}"
    git push origin main
    git tag -a "${latest_version}" -m "creating ${latest_version} tag version"
    git push origin tag "${latest_version}"

    echo ${latest_version}
}


compute_version
