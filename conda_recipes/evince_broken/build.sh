#!/bin/bash

set -ex

meson_config_args=(
    -D nautilus=false
    -D pdf=enabled
    -D djvu=disabled
    -D gxps=disabled
    -D comics=disabled
    -D gtk_doc=false
    -D introspection=true
    -D browser_plugin=false
    -D previewer=false
    -D thumbnailer=false
    -D gspell=disabled
    -D dbus=false
)
# ensure that the post install script is ignored
export DESTDIR="/"

meson setup builddir \
    "${meson_config_args[@]}" \
    --prefix=$PREFIX \
    --libdir=$PREFIX/lib

ninja -v -C builddir -j ${CPU_COUNT}

ninja -C builddir install -j ${CPU_COUNT}
