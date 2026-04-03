---
title: "Android-Studio-导入项目太慢解决方式"
date: 2016-01-02 08:00:00 +0800
categories: ["Android基础"]
source_name: "Android-Studio-导入项目太慢解决方式"
---
android studio 导入项目太慢解决方式
=======
每次将别的项目导入到Studio都奇慢无比，最近代码敲多了总算知道原因了，总结一下，项目导入太慢的原因主要有两个方面：  
1.本地的gradle版本和要导入的项目的gradle版本不一样。  
2.本地Android Studio版本和要导入项目的Studio版本不一样。  

既然不同就要下载，所以导入项目的大量时间就拿来下载gradle了，然而**天朝的网**不可能运行你这样做的

##解决方式：  
修改一下配置文件：  
需要修改的文件：  
1. xxx-project/.idea/gradle.xml中的&lt;option name="gradleHome" value="D:\AndroidDevelop\AndroidStudio\gradle\gradle-**2.4**" /&gt;  
2. xxx-project/gradle/warpper/gradle-wrapper.properties中的  distributionUrl=https\://services.gradle.org/distributions/gradle-**2.4**-all.zip  
3. xxx-project/build.gradle中的classpath 'com.android.tools.build:gradle:**1.3.0**'

修改很简单， 就是拷贝一个本地项目的对应条目过去。
