#!/bin/bash

./configure \
    --prefix="${PREFIX}" \
    --enable-desktopfiles=no

make

make install
