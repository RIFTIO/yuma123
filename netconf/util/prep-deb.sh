#!/bin/sh
#
# prep-deb.sh [svnversion]
#
# make the yuma build code and tar it up for debuild
#
# 2 packages:
#   yuma-tools-version.deb
#   yuma-tools-dev-version.deb
#
# the $1 parameter must be a revision number if present
# this will be used instead of HEAD in the svn export step

VER="1.13"

mkdir -p ~/build
mkdir -p ~/rpmprep
rm -rf ~/rpmprep/*

cd ~/rpmprep

if [ $1 ]; then
  svn export -r$1 http://svn.netconfcentral.org/svn/yuma/trunk yuma-$VER
else
  svn export http://svn.netconfcentral.org/svn/yuma/trunk yuma-$VER
fi

tar cvf yuma_$VER.tar yuma-$VER/
gzip yuma_$VER.tar
cp yuma_$VER.tar.gz ~/build

cd ~/build
if [ ! -f yuma_$VER.orig.tar.gz ]; then
  cp yuma_$VER.tar.gz yuma-tools_$VER.orig.tar.gz
fi

tar xvf yuma_$VER.tar.gz




