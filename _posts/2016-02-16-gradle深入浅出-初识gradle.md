---
title: "系列目录"
date: 2016-02-16 08:00:00 +0800
categories: ["Android源码分析"]
source_name: "【Gradle深入浅出】——初识Gradle"
---
[1.【Gradle深入浅出】——初识Gradle](https://www.jianshu.com/p/8e1ddd19083a)
[2.【Gradle深入浅出】——Gradle基础概念](https://www.jianshu.com/p/4bcdf07d4579)
[3.【Gradle深入浅出】——Android Gradle Plugin 基础概念](https://www.jianshu.com/p/6464ef756c5b)
[4.【Gradle深入浅出】——Gradle配置（一）](https://www.jianshu.com/p/eacd7625cc29)
[5.【Gradle深入浅出】——Gralde配置（二）](https://www.jianshu.com/p/9d3ecd0d1be1)

### 一、为什么要写Gradle
Gradle其实是自己一直想要了解的东西，但是一直没有下定决心，因为这个东西，你要说很有用，平时常用的可能就是那几个配置，要说没用，每次到关键的时候，gradle总会是你对于Android整体学习的一个拦路虎。为什么这样说呢，纵观现在Android整体的学习路线，其实归纳总结可以分为三个部分。
* 1.Android基础路线
也就是我们常说的业务开发，对于组件，MVP,MVVM的使用
* 2.Android运行时路线
也就是我们平时说的反射，hook等黑科技，而这类黑科技往往是在运行时对于系统层面或者源码层面的动态调整，达到我们的目的。
* 3.编译期路线
其实运行时做的调整已经能够完成我们所有的需求，但运行时对于性能的影响还有稳定性一直被人诟病，所以现在逐渐发展成编译期路线，也就是在编译期做处理，将我们想做的入侵编译期，最终打到我们的apk包中，达到我们想要的效果，而由于是在编译期做的处理，所以是前置处理好的，也就没有了运行时效率的问题。常见的比如组件化，插桩热修复，Router，AOP，包体积优化。

我们其实可以发现，一个技术无非就两种，运行时/编译期，从上面的介绍就会发现，同一个技术，编译期和运行时就有不同的解决方案，比如ARouter早期是用运行时反射查找，后面变成编译期生成映射关系的类，再比如热修复有hook的函数替换，也有插桩的方式。而且由于现在Android生态越来越重视性能问题，现在越来越多的库，开始迁移到编译期，所以可以看出现在对于编译的学习对于Android的进阶开发是非常重要的。
那么既然提到Android的编译，就肯定脱离不了Gradle的学习，这里就不展开Android从ADT到Gradle的变化历程，但是Gradle的强大，让不仅仅是Android，后端的Java项目也开始使用Gradle来进行打包，在了解了Gradle后，才能让我们进一步学习Android的各项技术，可以说这个已经成为一个拦路虎，或者说基石。
以上是我自己的想法，也是我自己对于Android学习的一个理解，所以我想开展一个长篇的Gradle学习系列，争取能较为全面深入的学习Gradle。
### 二、Gradle是什么
以上的内容可能来源于其他的一些博客的片段中，以为偏概念的东西，没办法做到纯原创编写，所以我做的是精选我认为值得学习的内容。
首先我们看下[Gradle官网](https://gradle.org/)对于他自己的介绍
>From mobile apps to microservices, from small startups to big enterprises, Gradle helps teams build, autom    ate and deliver better software, faster.

可以看到Gradle不仅是手机应用，还可以应用于后台，Gradle到使命简单来说就是帮忙工程构建，更快，更自动化，更可控，更便捷。
回到Android侧，Gradle是目前Android主流的构建工具，不管你是通过命令行还是通过AndroidStudio来build，最终都是通过Gradle来实现的。
说到打包，我们来看下Java打包到三大山。
Java生态体系中有三大构建工具：Ant、Maven和Gradle。其中，Ant是由Apache软件基金会维护；Maven这个单词来自于意第绪语（犹太语），意为知识的积累，最初在Jakata Turbine项目中用来简化构建过程；Gradle是一个基于Apache Ant和Apache Maven概念的项目自动化构建开源工具，它使用一种基于Groovy的特定领域语言(DSL)来声明项目设置，抛弃了基于XML的各种繁琐配置。

### 三、Gradle/Groovy/Java/JVM/Kotlin关系
最初看到Gradle的时候会发现他和Java的语法很像 ，但又有区别，再到后面了解Groovy，学习Kotlin，他们之间的关系对于新学习Gradle系统的人来说会很懵。
如果来画一个他们之间的关系，其实就比较清楚的体现了他们之间的关系。
![关系](https://upload-images.jianshu.io/upload_images/7866586-009a6fb2505ef283.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

从上面我们会有一个比较直观的理解，首先从上到下，Gradle不属于Language层，就像上面描述的，Gradle是一个框架，是一个帮助我们工程编译的框架。而往下的Language层，就是我们的Java/Kotlin/Groovy，虽然三个都属于Language层，但是还是有一定的归属关系，Groovy和Kotlin是基于Java的DSL，所以Groovy和Kotlin是可以无缝调用Java的。
>DSL：Domain Specific Language 的缩写，中文的翻译为领域特定语言（下简称DSL）;而与DSL相对的就是GPL，这里的GPL并不是我们知道的开源许可证，而是General Purpose Language的简称，即通用编程语言，也就是我们非常熟悉的Objective-C、Java、Python、以及C语言等。
>DSL 通过在表达能力上做的妥协换取在某一领域内的高效。它们的表达能力有限，只是在特定领域解决特定任务的。

我对DSL的理解是，**DSL是依附于某一特殊场景，或者专注于某一领域，通过大量的语法糖，来便捷这一领域的开发。**有来这样的理解，我们来看下属于DSL有哪些：SQL,CSS,HTML,Groovy,Kotlin。会发现特征就很明显。所以可以看到Groovy和Kotlin都是基于Java的DSL，所以再回头往上看，Gradle可以用Kotlin/Java编写吗？答案肯定是，完全没问题，只是缺少来语法糖的支持，肯定写起来会枯草很多。(当然还是指的Java,Kotlin编写Gradle脚本还是很爽的)再往下看，我们就到来真正运行的地方，class文件，刚才说到的Groovy/Kotlin/Java，最终都会编译成class文件，变成JVM能够运行的字节码文件，最终运行起来。
### 四、Gradle版本号和Gradle Plugin版本号的关系
记得刚从Eclipse转到Android Studio的时候，特别痛苦，经常各种莫名其妙的报错，说什么版本对应不上。
>Project is using an old version of the Android Gradle plug-in. The minimum supported version is x.x.x Please update the version of the dependency 'com.android.tools.build:gradle'

这时候就会很懵，版本对应不上，而且都是gradle，怎么一个工程里面有两个gradle版本，搜索项目会发现还真是有两个定义gralde版本的地方。
```
	//build.gradle
	classpath 'com.android.tools.build:gradle:3.5.1'
	//gradle-wrapper.properties
 	distributionUrl=https\://services.gradle.org/distributions/gradle-5.4.1-all.zip
```
所以这里刚一看到就会感到很奇怪，这两个Gradle到底哪个是真正的Gradle，各有什么作用呢？
所以这里就来介绍一下，先说一下Gradle和Android Studio是完全两个没有关系的东西，Gradle有一套自己的环境，就像我们安装Java一样，需要配置环境变量等等，然后也可以通过命令行执行操作，类似于javac,那么怎么能让AS便捷的使用Gradle呢，所以Google就针对Gradle和AS的结合，编写了一个Android Gradle Plugin，所以我们能在AS上使用Gradle完全是因为这个插件的原因。
它本质就是一个AS插件，它一边调用Gradle本身的代码和批处理工具来构建项目，一边调用Android SDK的编译、打包功能，从而让我们能够顺畅的在AS上进行开发。
Gradle插件跟Android SDK Build Tool有关联，因为它还承接着Android Studio里的编译相关的功能，这也是我们要在项目的local.properties文件里写Android SDK路径，在build.gradle里注明buildToolsVersion的原因。
所以现在我们再来看上两个定义的版本就会发现，`classpath 'com.android.tools.build:gradle:3.0.0'`是用来定义Android Gradle Plugin的版本，对应的`distributionUrl=https\://services.gradle.org/distributions/gradle-4.0-all.zip`就是用来定义Gradle的版本的。
Gradle插件是独立于AndroidStudio运行的，所以它的更新也是AndroidStudio分开的。Gradle插件会有版本号，每个版本号又对应一个或者一些Gradle发行版本（一般是限定一个最低版本）
所以我们的插件的版本和Gradle的版本一定要对应上，具体的对应关系[官方地址](https://developer.android.google.cn/studio/releases/gradle-plugin.html#updating-plugin)
但这里其实我很想吐槽一下，既然是插件，对于Gradle的包装，为什么不直接内部指定好Gradle的版本号，还需要开发者自己手动去对应Gradle Plugin和Gradle的关系，从一个插件或者产品的角度来看，我感觉这样的设计是有待优化的。
### 五、Gradle文件目录结构
接下来我们来看下和Gradle相关的目录结构，通过对目录结构对了解，也有助于我们后面对于Gradle编译原理对理解。
![目录结构](https://upload-images.jianshu.io/upload_images/7866586-2992c65a400ea0fb.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
首先我们看到了上面的目录结构，这个是我们新建的一个工程的目录结构。
#### local.properties
```
sdk.dir=/xxxxx/xxxxxx/Library/Android/sdk
```
local.properties是构建系统配置本地环境属性，其中包括：
* ndk.dir —— NDK路径。此属性已被弃用，NDK的所有下载版本都安装在Android SDK目录下的NDK目录中。
* sdk.dir —— SDK的路径。
* cmake.dir —— CMake的路径。
* ndk.symlinkdir —— 在Android Studio 3.5以及更高的版本中，创建指向NDK的符号链接，该符号链接的路径可比SDK安装路径短。

#### setting.gradle
setting.gradle文件位于项目的根目录下，用于指示Gradle在构建应用时将哪些模块包含在内。对于单工程来说，这个文件的作用很小，一般是这样的。
```
	include ':app'
```
但是如果我们创建一个子Module，就会发现这个文件的内容发生了改变。
```
	include ':app'
	include ':subModule'
```
所以这个文件就是当我们工程进行组件化和模块化的很重要的文件。

#### gradle.properties
用于配置项目全局Gradle设置，如Gradle守护程序的最大堆大小，有时候我们全局的一些配置，比如全局变量，也可以在这个文件进行配置，所有的Module都可以读取到。
但这里要提一个问题：这个文件可以有多个吗？如果多个的话，会是怎样的效果呢、这里大家可以自己试下，我这里就直接给结论了。
这个文件可以多个，但是根目录下的配置会全局生效，也就是如果我们在根目录配置了一个变量COMMON__VERSION，所有的子Module都可以读取到，如果我们在子项目中也新建一个gradle.properties也配置了一个COMMON_VERSION变量，那么会覆盖根目录的版本。

#### gradle--wrapper.properties
```
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-4.0-rc-1-all.zip
```
这个文件的从名字上来看，意思就很直观，就是包了一层Gradle，其实他的作用也是这样的，经常有这样的场景，我们每个人本地的Gradle版本可能不一致，每个项目的Gradle版本也可能不一致，这样就可能出现版本不一致而导致编译不通过的问题，所以为了解决这个问题，Gradle官方出了gradle-wrapper的机制，表示该项目使用什么版本来进行编译，这样假如我们本地是Gradle2.0，拉下来的gradle--wrapper的配置是gradle-4.1,这时候我们就会使用这个Gradle版本进行编译。

#### build.gradle
这个就是重头戏了，这就是我们用于打包编写的Gradle脚本，里面可以看到我们写的依赖关系，打包配置等等一系列配置和打包逻辑，这个这里就不展开讲了，后面会专门展开讲解，这里还是从文件结构的角度来看下这个文件，这里有两个build.gradle文件，如果我们看下，同样的两个文件层级是不一样的。
在**根目录**下的build.gradle常用于配置我们的全局属性，当在这个文件配置后，我们所有的子项目都会生效、
在**子项目目录**下的build.gradle,就是我们针对这个项目的单独的配置。

### 六、总结
这篇博客从基础上讲解了我认为在第一次接触Gradle可能遇到的一些困惑点，算是对Gradle先有了一个大体上的了解，接下来会继续讲解Gradle，第二篇博客可能对Gradle的配置进行讲解。

