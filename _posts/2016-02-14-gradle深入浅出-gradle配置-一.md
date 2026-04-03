---
title: "系列目录"
date: 2016-02-14 08:00:00 +0800
categories: ["Android源码分析"]
source_name: "【Gradle深入浅出】——Gradle配置（一）"
---
[1.【Gradle深入浅出】——初识Gradle](https://www.jianshu.com/p/8e1ddd19083a)
[2.【Gradle深入浅出】——Gradle基础概念](https://www.jianshu.com/p/4bcdf07d4579)
[3.【Gradle深入浅出】——Android Gradle Plugin 基础概念](https://www.jianshu.com/p/6464ef756c5b)
[4.【Gradle深入浅出】——Gradle配置（一）](https://www.jianshu.com/p/eacd7625cc29)
[5.【Gradle深入浅出】——Gralde配置（二）](https://www.jianshu.com/p/9d3ecd0d1be1)

### 一、背景
前面三篇博客讲解了Gradle的基础概念，看完前面三篇博客我们应该对于Gradle都有了一个基础的认知，知道了文件的作用，Gradle的基本构成，本篇博客开始就开始进入Gradle的学习，首先讲解的是Gradle的配置，Gradle配置应该是我们日常开发中必不可少的技能，平时的打包，编译等等都需要熟悉Gradle的配置。

### 二、属性配置
#### 2.1 Properties类
我们知道Gradle都关于属性配置有两个文件，`local.properties`和`gradle.properties`，这两个文件的实质都是生成Java的`Properties`对象，所以要属性这两个文件的作用，首先要属性下`Properties`类。
我们首先来看下这个类的基本上结构。
```
public class Properties extends Hashtable<Object,Object> {
    protected Properties defaults;

    public Properties() {
        this(null);
    }

    public Properties(Properties defaults) {
        this.defaults = defaults;
    }
    
    public String getProperty(String key) {
        Object oval = super.get(key);
        String sval = (oval instanceof String) ? (String)oval : null;
        return ((sval == null) && (defaults != null)) ? defaults.getProperty(key) : sval;
    }

    public synchronized Object setProperty(String key, String value) {
        return put(key, value);
    }
}
```
看完这个我们应该就有一个大体的认识了，`Properties`本质就是一个HashTable，支持设置默认属性，其他的没啥区别，哪我们看下`Properties`如何读取文件呢
```
public synchronized void load(InputStream inStream) throws IOException

public synchronized void load(Reader reader) throws IOException

public synchronized void loadFromXML(InputStream in)
        throws IOException, InvalidPropertiesFormatException
```
可以看到`Properites`给我们提供了三个加载文件的方式，所以这里我们也可以得出一个结论，**使用`Properties`不是必须使用`.properties`格式的文件。**
哪可能有人要问了，为啥这里的配置都使用properties格式的文件呢？
我猜测可能是复用Spring Boot中的支持的配置文件，Spring Boot中支持三种格式的配置文件`YAML,XML,Properties`，具体的差异这里就不展开讲解了。
我们可以理解为`.properties`就是类似于json的一套配置文件格式，IDE对于这类文件有特殊的支持，比如注释等语法，做了统一的规范
**Properties文件的格式规范**
>properties文件的书写要求总结：
1、注释内容由 # 或者! 开头， 如果# 或者!不在开头，则不作为注释
2、key,value之间用 = 或者 : 分隔。一行中既有=也有:时，第一个（或者=或者：）将作为key,value分隔符。
3、key 不能换行，value可以换行，换行符是\ ，且换行后的\t、空格都会忽略。

#### 2.2 local.properties配置
有了对于Properties类的理解，我们在来看local.properties文件，理解起来就方便类许多，前面几篇博客已经提到了`local.properties`是Studio自动生成的一个本地配置文件，并且不会提交到远端，是我们自己本地的配置文件，常见的配置如下：
```
#NDK 的路径。此属性已被弃用。NDK 的所有下载版本都将安装在 Android SDK 目录下的 ndk 目录中。
ndk.dir=xxxxxxx
#SDK 的路径。
sdk.dir==/Your Local Path/Android/sdk
#CMake 的路径。
cmake.dir=xxxxxxx
#在 Android Studio 3.5 及更高版本中，创建指向 NDK 的符号链接，该符号链接的路径可比 NDK 安装路径短。
ndk.symlinkdir=xxxxxxx
```
##### 2.2.1 定义全局变量
既然是配置文件，那么如何在`local.properites`中定义全局变量，然后在build.gradle中读取呢？比如我们的maven上传需要用户的姓名密码，每个人的都不一样，所以可以放到local.propertiest文件中
```
USER_NAME=xxxx
USER_PSD=xxxxx
```
和前面介绍的一样，我们只需要在local.properties中定义变量，然后在gradle中读取变量只需要生成Properties类来进行读取文件。
```
Properties properties = new Properties()
properties.load(project.rootProject.file('local.properties').newDataInputStream())
def sdkDir = properties.getProperty('sdk.dir')

```
#### 2.3 gradle.properties配置
同样的这也是一个Properties类型的文件，但这个文件主要是配置和Gradle自身相关的配置内容的，接下来聊聊他的几个作用：
##### 2.3.1项目级别的Gradle配置
这里主要是配置本项目在使用Gradle进行编译时的配置，比如虚拟机堆栈配置(常见的编译速度优化就在这里配置)
```
#使用构建缓存，设置为true时，Gradle将在可能的情况下重用任何先前构建的任务输出，从而使构建速度更快。
org.gradle.caching=(true,false)
#设置为true时，单个输入属性哈希值和每个任务的构建缓存键都记录在控制台上。
org.gradle.caching.debug=(true,false)
##只编译需要的项目，在org.gradle.parallel=true情况下，起很大作用
org.gradle.configureondemand=(true,false)
#自定义控制台输出的颜色或详细程度。默认值取决于如何调用Gradle。
org.gradle.console=(auto,plain,rich,verbose)
#当设置为true时，使用Gradle守护进程运行构建。默认是true的。也就是不用每次构建重新创建一个进程，加快编译速度
org.gradle.daemon=(true,false)
#Gradle守护进程将在指定的空闲毫秒数后终止。默认值为(3小时)。
org.gradle.daemon.idletimeout=(# of idle millis)
#当设置为true时，Gradle将在启用远程调试的情况下运行构建，默认为false
org.gradle.debug=(true,false)
#为Gradle构建过程指定Java home。该值可以设置为jdk或jre位置
org.gradle.java.home=(path to JDK home)
#指定用于Gradle守护进程的JVM参数。该设置对于配置用于构建性能的JVM内存设置特别有用。这不会影响Gradle客户端VM的JVM设置。
org.gradle.jvmargs=(JVM arguments)
#gradle log 级别
org.gradle.logging.level=(quiet,warn,lifecycle,info,debug)
#配置完成后，Gradle将分叉到org.gradle.workers。使用最大jvm并行执行项目,加快构建速度
org.gradle.parallel=(true,false)
#指定Gradle守护进程及其启动的所有进程的调度优先级。默认是正常的。
org.gradle.priority=(low,normal)
#配置长日志的打印，默认为false
org.gradle.vfs.verbose=(true,false)
#允许Gradle在下一个版本中重用有关文件系统的信息。默认设置为关闭。
org.gradle.vfs.watch=(true,false)
#设置警告日志的不同展示样式
org.gradle.warning.mode=(all,fail,summary,none)
#配置后，Gradle将使用最多给定数量线程。默认值为CPU处理器数。
org.gradle.workers.max=(max # of worker processes)
```
##### 2.3.2 常用配置
所以看到上面的定义后，我们就可以理解常见的“编译速度优化”的配置的大概意思
```
org.gradle.daemon=true
org.gradle.parallel=true
org.gradle.configureondemand=true
org.gradle.jvmargs=-XX:MaxPermSize=2048m -Xmx10240M
org.gradle.caching=true
android.enableBuildCache=true
android.buildCacheDir=buildCacheDir/

```
##### 2.3.3 配置系统配置
除了刚才说的这个文件用于配置gradle属性，这个文件还可以用于配置系统属性和android属性
并且可以区分配置不同的项目的配置
1、单项目gradle使用代理：gradle/wrapper/gradle-wrapper.properties
2、全局gradle使用代理：userdir/.gradle/gradle.properties

```
#代理服务器IP/域名
systemProp.http.proxyHost=127.0.0.1
#代理服务器端口
systemProp.http.proxyPort=8080
#代理服务器需要验证时，填写用户名
systemProp.http.proxyUser=userid
#代理服务器需要验证时，填写密码
systemProp.http.proxyPassword=password
#不需要代理的域名/IP
systemProp.http.nonProxyHosts=*.nonproxyrepos.com|localhost
#https的配置
systemProp.https.proxyHost=127.0.0.1
systemProp.https.proxyPort=8080
systemProp.https.proxyUser=userid
systemProp.https.proxyPassword=password
systemProp.https.nonProxyHosts=*.nonproxyrepos.com|localhost
#关闭aapt2
android.enableAapt2=false
#使用androidx
android.useAndroidX=false
#三方包使用androidx
android.enableJetifier=false
```
其他的系统变量这里就不列举了，具体看我们遇到具体场景来设置
##### 2.3.4 定义变量
接着来看下在gradle.properties文件中如何定义变量，gradle.properties就是官方定义的用来定义变量的文件的地方，所以定义和获取就不需要像local.properties那么麻烦了。
```
IS_DEBUG=true
```
获取变量，就不需要通过文件流读取文件流，gralde内部自身已经做了这个，我们可以直接引用变量即可。
```
//build.gradle
print("xxxxxxxxx:"+IS_DEBUG)
```
#### 2.4 local.properties和gradle.properties的差异
* local.properties不会提交到远端，多用于本地环境配置，不同用户有差异的配置，或者用户账号等私密信息
* local.properties读取配置需要通过文件流来读取生成Properties对象，但gradle.properties不需要，可以直接引用变量读取
* gradle.properties可以用于配置系统属性
* gradle.properties可以有多个，根目录的会全局生效，子目录的会覆盖根目录的。

### 3.setting.gradle配置
setting.gradle前面的博客介绍了，是用于配置项目的组成和模块的，所以一半我们的setting.gradle文件都是这样的
```
include ':testlibrary'
include ':app'
rootProject.name='StudyDemo'
```
前面有讲过setting.gradle的实质是生成一个Setting对象，我们按住ctrl点击include就进入了Setting.gradle类，其实就可以知道我们可以调用的api，这里还是介绍我们常用的几个方法吧。首先来看下最常用的`include`方法。
```
   /**
     * <p>Adds the given projects to the build. Each path in the supplied list is treated as the path of a project to
     * add to the build. Note that these path are not file paths, but instead specify the location of the new project in
     * the project hierarchy. As such, the supplied paths must use the ':' character as separator (and NOT '/').</p>
     *
     * <p>The last element of the supplied path is used as the project name. The supplied path is converted to a project
     * directory relative to the root project directory. The project directory can be altered by changing the 'projectDir'
     * property after the project has been included (see {@link ProjectDescriptor#setProjectDir(File)})</p>
     *
     * <p>As an example, the path {@code a:b} adds a project with path {@code :a:b}, name {@code b} and project
     * directory {@code $rootDir/a/b}. It also adds the a project with path {@code :a}, name {@code a} and project
     * directory {@code $rootDir/a}, if it does not exist already.</p>
     *
     * <p>Some common examples of using the project path are:</p>
     *
     * <pre class='autoTestedSettings'>
     *   // include two projects, 'foo' and 'foo:bar'
     *   // directories are inferred by replacing ':' with '/'
     *   include 'foo:bar'
     *
     *   // include one project whose project dir does not match the logical project path
     *   include 'baz'
     *   project(':baz').projectDir = file('foo/baz')
     *
     *   // include many projects whose project dirs do not match the logical project paths
     *   file('subprojects').eachDir { dir -&gt;
     *     include dir.name
     *     project(":${dir.name}").projectDir = dir
     *   }
     * </pre>
     *
     * @param projectPaths the projects to add.
     */
    void include(String... projectPaths);
```
这里特意把注释也放了进来，不得不说老外对于注释真的写的非常详细，往往我们忽视了这么冗长的注释，但当发现问题，从搜索引擎上搜相关资料都时候就会发现，其实大部分就是对于注释都翻译。
所以这里我下面介绍都内容，就会发现和上面注释都大同小异。
首次看下这里的引入方式，一般都是`include ':app'`，这里的语法是这样的
```
  include ':lib的文件名称'
```
在这里`:`表示的路径的分隔符，也就是`\`的意思，所以这里都需要使用`:`，其次这里都路径是相当于根目录的路径。然后我们可以看到其实这个方法是可变参数，所以这里支持多个项目引入。
```
  include ':app',':library'
```
所以我们如果有一个这样的目录结构的项目
```
RootProject
  -app
    -subapp
  -libA
  -libB
```
那么这时的setting.gradle就是这样
```
    include ':app'
    include ':app:subapp'
    include ':libA','libB'
```
这时我们可能有个问题：我们如果引入的不是根目录下的项目怎么办？也就是引入其他路径下的项目作为我们的子module，因为这里一直是相对与根目录的路径
```
include ':libX'
//这里是libX的相对根目录的相对路径
project(':libX').projectDir = new File(settingsDir, '../xxxx/xxxx/libX')
//这里是libX的绝对路径
project(':libX').projectDir = new File('libX的绝对路径')
```
这样我们就可以引入不在这个项目中的Lib作为我们这个项目的Lib，组件化的工程经常就会这样使用。
最后我们看下还有一个小知识点，我们如果想改变这个Lib在Studio的显示的名称，该如何操作？
```
  project(':lib').name='AAA'
```
这个方法的作用就是我们这样的，可以改变Lib在IDE中的名称。
#### 全局变量定义
接着来看下在setting.gradle怎么定义全局变量呢？这时候就是利用gradle的拓展属性的特性了。
```
   gradle.ext.IS_DEBUG=true
```
然后在build.gradle中使用变量的时候，就还是使用gradle.ext使用即可。
```
   println gradle.ext.IS_DEBUG
```
关于ext属性我们后面专门再讲下，我们前面也讲到了我们全局就只会有一个gradle对象，所以这里可以理解是一个全局的map对象，这样就好理解了很多。

### 总结
至此，本篇博客对于`gradle.properties`、`local.properties`、`setting.gradle`都配置都有了一个较为详细都讲解，我们后面在使用过程中，对于这三个文件的配置都不会那么陌生，并且对于三个文件的差异都有了一个基本都认知，知道我们在定义本地变量，不同人都环境有差异都地方都应该在local.properties配置，大家共同的配置和变量定义可以放到gradle.properties这个专职用于存放配置的文件，最后就是专门用于配置我们项目的目录结构的setting.gradle，当然这个文件也可以用于配置一些变量，这时候我们就要把我单一职责的原则，也就是高内聚，低耦合那一套，按照文件职责进行划分，下一篇博客准备对build.gradle的配置进行讲解。