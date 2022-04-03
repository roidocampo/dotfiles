#!/bin/bash

set -ex

meson_config_args=(
    -D viewer=false
    -D previewer=false
    -D thumbnailer=false
    -D browser_plugin=false
    -D nautilus=false
    -D comics=disabled
    -D djvu=disabled
    -D dvi=disabled
    -D pdf=enabled
    -D ps=disabled
    -D tiff=disabled
    -D xps=disabled
    -D gtk_doc=false
    -D user_doc=false
    -D introspection=false
    -D dbus=false
    -D gspell=disabled
    -D keyring=disabled
    -D gtk_unix_print=disabled
    -D thumbnail_cache=disabled
    -D multimedia=disabled
)

meson \
    --prefix=$PREFIX \
    --libdir=$PREFIX/lib \
    "${meson_config_args[@]}" \
    buildir

ninja -v -C builddir -j ${CPU_COUNT}

ninja -C builddir install -j ${CPU_COUNT}
