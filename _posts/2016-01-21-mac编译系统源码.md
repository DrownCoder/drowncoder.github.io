---
title: "Mac编译系统源码"
date: 2016-01-21 08:00:00 +0800
categories: ["Android开源项目"]
source_name: "Mac编译系统源码"
---
1.注意建磁盘
2.第三个问题：少某个文件

报错日志：

[  4% 2459/59653] yacc out/soong/.inte.../system/tools/aidl/aidl_language_y.cpp
FAILED: out/soong/.intermediates/system/tools/aidl/libaidl-common/darwin_x86_64_static/gen/yacc/system/tools/aidl/aidl_language_y.cpp out/soong/.intermediates/system/tools/aidl/libaidl-common/darwin_x86_64_static/gen/yacc/system/tools/aidl/aidl_language_y.h
BISON_PKGDATADIR=external/bison/data prebuilts/misc/darwin-x86/bison/bison -d  --defines=out/soong/.intermediates/system/tools/aidl/libaidl-common/darwin_x86_64_static/gen/yacc/system/tools/aidl/aidl_language_y.h -o out/soong/.intermediates/system/tools/aidl/libaidl-common/darwin_x86_64_static/gen/yacc/system/tools/aidl/aidl_language_y.cpp system/tools/aidl/aidl_language_y.yy
[  4% 2462/59653] cc out/soong/.interm..._core/obj/system/core/adf/libadf/adf.o
ninja: build stopped: subcommand failed.
15:42:49 ninja failed with: exit status 1
make: *** [run_soong_ui] Error 1


frameworks/av/media/libstagefright/DataSource.cpp:29:10: fatal error: 'media/stagefright/DataURISource.h' file not found
#include <media/stagefright/DataURISource.h>

提示找不到头文件，需要查看当前文件目录下的Android.mk文件，然后查看，LOCAL_C_INCLUDES： 可选变量，表示头文件的搜索路径。 默认的头文件的搜索路径是LOCAL_PATH目录，找到头文件目录，发现头文件目录中的DataURISource的URL是DataUriSource，所以修改源码。结果发现不行，只能到GoogleSource中找到这个文件，然后新建一个，把代码拷贝过来
https://android.googlesource.com/platform/frameworks/av/+/65842db06c2d77e53cc5ac61692160d844cc7d0a/include/media/stagefright/DataURISource.h
https://blog.csdn.net/xx326664162/article/details/52875825


xt_DSCP.h头文件找不到，把大写改成小写就行
