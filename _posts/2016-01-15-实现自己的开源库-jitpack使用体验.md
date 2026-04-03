---
title: "实现自己的开源库----JitPack使用体验"
date: 2017-09-26 00:26:45+08:00
categories: ["Android开发工具"]
source_name: "实现自己的开源库----JitPack使用体验"
jianshu_views: 573
jianshu_url: "https://www.jianshu.com/p/9218d34fb8fa"
---
最近热衷于写自定义View，但是感觉仅仅是实现了自定义View，放到Github不够爽，想和别人大神一样，能直接compile一下，直接能用多炫酷啊，网上搜了一下，有三个平台可以实现这个需求：
1.发布到Jcenter
2.发布到Maven
3.发布到JitPack
看别人的说法好像是前两个比较繁琐，并且还需要审核，第三个比较容易上手，所以选择了第三个，总结一下使用过程吧。

官方主页：
https://jitpack.io/
首先要分为两步
一、写自己的library
二、将自己的library发布到JitPack上

**一、写自己的library**
这个应该比较基础了
（1）
![这里写图片描述](/assets/img/posts/b8737cab573d6547.webp)
（2）
![这里选择Library](/assets/img/posts/a3e3e8cf14ba14fa.webp)
（3）在Library中完成自己的库
（4）在项目中使用Library，打开 app 的 build.gradle，在最后的 dependencies 节点添加一行，compile project(':library')，再 Sync 一下 Gradle即可，这样 app 就完成了对 library 的依赖。另外还有一种方法去依赖 library，右键 app 这个 module，选择 Open Module Settings，切换到最后一个Tab:Dependencies，点击左下角的加号->Module dependency->选择 library，这样也能完成 app 对 library 的依赖。
![这里写图片描述](/assets/img/posts/329c9e499264c0c5.webp)
这样就完成了Library的编写，这样就可以在app中写sample，引用library。
**二、在JitPack中发布自己library**
官方文档：https://jitpack.io/docs/ANDROID/
总结：
1.在root的build.gradle文件中加入

```
buildscript { 
  dependencies {
    classpath 'com.github.dcendents:android-maven-gradle-plugin:1.5' // Add this line
```
2.在library的build.gradle中加入

```
apply plugin: 'com.github.dcendents.android-maven'  

 group='com.github.YourUsername'
```
3.下面这一步要注意
下面检查你的Project目录是否存在 gradle/wrapper/gradle-wrapper.jar、gradle-wrapper.properties 这两个文件**（一般都是没有的）**，如果存在可跳过下面这步，如果不存在，请按下面的进行操作。打开当前项目的 Terminal面板，先后执行 gradle wrapper 和 ./gradlew install 两个命令
![这里写图片描述](/assets/img/posts/f430b5c00a3865da.webp)

4.将自己的项目传到Github上
这个的操作方式，网上基本上都有教程
![这里写图片描述](/assets/img/posts/6be99ccda33e9b0c.webp)
5.下面这步很重要！在Github上新建一个版本
这一步不做的话会导致发布失败的！
![这里写图片描述](/assets/img/posts/cbda23eb98b94fae.webp)
![这里写图片描述](/assets/img/posts/26e40edcb679b6d7.webp)
![这里写图片描述](/assets/img/posts/8623e2b52b6c3f6c.webp)
6.基本到这里就完成了发布，这时候你登录你的JitPack网址，搜索你的项目名，这时候就会显示你发布的项目的引用方式了
![这里写图片描述](/assets/img/posts/5d9ef8154630cdc2.webp)
![这里写图片描述](/assets/img/posts/a4e1d90cbba99495.webp)
**这里你要注意，要是你的Get it不是我这个状态的话，说明是没有上传成功的，需要检查一下你哪一步忘记做了，重新来一遍了**
![这里写图片描述](/assets/img/posts/0d4196be69f23a13.webp)
好了。现在你已经实现了自己的开源库了。
