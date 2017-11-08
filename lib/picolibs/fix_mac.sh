#!/bin/bash
#This script fixes two issues in the PicoScope libraries caused by SIP since El Capitan
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
sudo install_name_tool -add_rpath $DIR libps2000a.2.dylib
sudo install_name_tool -change libiomp5.dylib $DIR/libiomp5.dylib libpicoipp.1.dylib