---
title: "【Gradle深入浅出】——Gradle基础概念"
date: 2020-11-29 23:34:31+08:00
categories: ["Android源码分析"]
source_name: "【Gradle深入浅出】——Gradle基础概念"
jianshu_views: 5790
jianshu_url: "https://www.jianshu.com/p/4bcdf07d4579"
---
[1.【Gradle深入浅出】——初识Gradle](https://www.jianshu.com/p/8e1ddd19083a)
[2.【Gradle深入浅出】——Gradle基础概念](https://www.jianshu.com/p/4bcdf07d4579)
[3.【Gradle深入浅出】——Android Gradle Plugin 基础概念](https://www.jianshu.com/p/6464ef756c5b)
[4.【Gradle深入浅出】——Gradle配置（一）](https://www.jianshu.com/p/eacd7625cc29)
[5.【Gradle深入浅出】——Gralde配置（二）](https://www.jianshu.com/p/9d3ecd0d1be1)

##### 前言
前一篇博客从基础层面对Gradle做了一个讲解，让我们对于Gradle有了一个大体上对认知。本篇博客开始就开始进入Gradle的学习了，本篇博客将从Gradle的基础概念进行讲解，Gradle的基础概念又分为Gradle和AGP(Android Gradle Plugin后续简称AGP)的基础概念，所以这里会做一定的划分，可能有的概念在两边都有涉及，所以区分不会特别明显，但是对于我们学习来说，并不会造成什么困扰。
### Gradle基础概念
首先还是回到上篇博客一直围绕的一个话题，Gradle是什么？
Gradle中的所有内容都基于两个基本概念：project和task
Gradle 是通过组织一系列 task 来最终完成自动化构建的，所以 task 是 Gradle 里最重要的概念
我们以生成一个可用的 apk 为例，整个过程要经过 资源的处理，javac 编译，dex 打包，apk 打包，签名等等步骤，每个步骤就对应到 gradle 里的一个 task
gradle 可以类比做一条流水线，task 可以比作流水线上的机器人，每个机器人负责不同的事情，最终生成完整的构建产物。
![流水线](/assets/img/posts/09dae671b45a88ee.png)

而Gradle的代码实质是配置脚本，执行一种类型的配置脚本时就会创建一个关联的对象。
Gradle的三种主要对象解释如下：
* Project对象：每个build.gradle会转换成一个Project对象。
* Gradle对象：构建初始化时创建，整个构建执行过程中只有这么一个对象，一般很少去修改这个默认配置脚本。
* Settings对象：每个settings.gradle会转换成一个Settings对象。
### Build的生命周期
Gradle构建的生命周期其实相对来说还比较复杂，这里先仅从大方面来讲一下Gradle的生命周期，对于后续我们的理解有帮助，而对于具体Gradle提供的生命周期hook在后面再专门讲解。
Gradle的构建大体分为三个阶段：
* 初始化阶段
  初始化阶段主要做的事情是有哪些项目需要被构建，也就是执行我们的setting.gradle，构建出Setting对象,并且创建对应的Product对象。
* 配置阶段
  配置阶段主要是根据上一步setting.gradle配置的项目，根据项目的build.grale进行构建，这时候就会根据build.gradle，并且生成相应要执行的Task
* 执行阶段
  执行阶段就是根据上面的task,按照顺序进行执行构建。
  

#### Setting对象
上篇博客其实有提到，我们在多项目构建多时候，Setting.gradle就发挥了很大多作用，这个文件一般放在工程多根目录，该文件在初始化阶段被执行，通过读取我们在setting.gradle中配置的多项目，引入并且进行构建，所以我们在做组件化和模块化的时候，经常就是在setting.gradle里面做文章。

#### Project/RootProject/SubProject
每次构建（build）至少由一个project构成，我们每个build.gradle脚本在被Gradle解析后，都会生成一个Project对象。
而这里要讲解下RootProject/SubProject的区别，其实也很好理解，上一篇博客其实就有提到，我们一个项目里有多个build.gradle，所以对应的肯定有多个project对象，而根目录下的build.gradle对应的就是RootProject，每个子module下的build.gradle对应的就是SubProject.我们可以输入命令：`./gradlew projects`来查看当前有的Project对象。
```
Root project 'StudyDemo'
\--- Project ':app'
```
关于Project相关的配置，后面会专门开一篇博客进行讲解，本篇的博客的重点还是从代码的角度，来了解下Gradle的实质。

#### Task
每个task的实质其实是一些更加细化的构建（譬如编译class、创建jar文件等）。所以Task正如其名，表示一个任务，那我们用具体的代码来看下Task具体是怎么样的。
```
task hello {
    doLast {
        println 'Hello world!'
    }
}
```
当我们在build.gradle中定义了上述Task后，我们通过`./gradlew hello`执行task,就会发现输出结果。
>Task :hello
>Hello world

#### Task的创建方式
而创建Task有很多种方式，这里列举一下
```
//创建一个名为build.gradle的文件
task hello {
    doLast {
        println 'Hello world!'
    }
}

//这是快捷写法，用<<替换doLast
task hello2 << {
    println 'Hello world!'
}

task (hello3){
  println 'Hello3 world!'
}

task ('hello4'){
  println 'Hello4 world!'
}

tasks.create('hello5'){
  doLast{
    println 'Hello5 world!'
  }
}
```
#### Task的执行阶段
而这里我们继续展开下，从上面的几种创建方式，我们会发现其实是有些区别的，为什么有些有doLast是什么,而有些没有，有些有<<这样的符号，这种会有区别吗？
```
task hello {
  println 'init here'
  doLast {
    println 'Hello world'
    }
}
```
通过上面这个例子我们来理解下，这里我们分别执行两个命令，第一个`gradle -q`会发现结果是这样的。
>init here
>Welcome to Gradle 6.1.1.
>To run a build, run gradle <task> ...
>To see a list of available tasks, run gradle tasks
>To see a list of command-line options, run gradle --help
>To see more detail about a task, run gradle help --task <task>
>For troubleshooting, visit https://help.gradle.org

通过输出的日志对比我们应该会发现区别，我们在没有执行task的时候，我们写入的init here同样打印来出来，而我们`doLast`中的逻辑并没有执行。
所以这里就可以看出区别，如果我们定义了一个Task没有加`doLast`或者没有使用`<<`的话，task内部的内容无论执行什么task都会在inittialization阶段被执行，而`<<`其实是`doLast`的简化，所以当我们用`doLast`定义的内容，则会在该Task被执行的时候执行。
#### 自定义Task
Task其实就是一个对象，而且前面说到了Groovy和Java是互通的，我们是可以自定义Task的，做一定程度的组合和封装。
```
class MyTask extends DefaultTask {

 	@TaskAction
	void action1(){
		println 'do action1'
	}
	
	@TaskAction
	void action2(){
		println 'do action2'
	}

	void action3(){
		println 'do action3'
	}
}

task hello3 (type:MyTask){
	doLast{
		println 'do Last'
	}
}

```
同样我们来执行下hello3 Tast,会得到下面的结果。
> Task :hello3
do action1
do action2
do Last

所以这里就会明白，自定义Task我们首先需要集成`DefaultTask`对象，并且实现方法，方法使用`@TaskAction`进行注解，被注解的方法会按照定义方法的顺序在Task被执行的时候执行，而如果没有使用注解，则就是一个常规的对象方法。我们可以看下`@TaskAction`的源码。
```
/**
 * Marks a method as the action to run when the task is executed.
 */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@Inherited
public @interface TaskAction {
}
```
   
#### Task的顺序
前面有说到，Gradle通过将一系列的Task构建成一个有向无环图，来执行最终的任务，既然是有向无环，那么说明Task之间是有依赖和顺序关系的。那么Task之间的依赖关系如何定义呢？这里就来介绍一下。
```
   doLast{
   }
   doFirst{
   }
```
首先看下Task内部的一个API，用于表示Task内部的执行方式
* doFirst：task执行时，最开始的操作
* doLast：task执行时，最后的操作
接着来看下Task之间的顺序如何控制。
###### 1.dependsOn
最直接的一个任务依赖另一个任务的执行就是通过`denpendsOn`方法。

```
task task1 << {
    println "我是task1----"
}

task task2 << {
    println "我是task2----"
}

//task2 依赖 task1, 执行task2之前先执行task1
task2.dependsOn task1
``` 
执行task2`gradlew task2`
结果
>我是task1----
>我是task2----

###### mustRunAfter
当一种场景TaskA依赖TaskB和TaskC，但我们想控制TaskB和TaskC的关系，那么这时候我们如何处理，可能有刚才的介绍我们会用taskB.dependsOn TaskC，但是这样其实就有问题另，因为实际上TaskB是不依赖TaskC的，只是在有TaskA的情况下，我们希望TaskC先执行。这时候就需要用到`mustRunAfter`。
```
task taskA {
	doLast{
	println '我是taskA'
	}
}

task taskB {
	doLast{
	println '我是taskB'
	}
}

task taskC {
	doLast{
	println '我是taskC'
	}
}

taskA.dependsOn taskB
taskA.dependsOn taskC
taskB.mustRunAfter taskC
```  
执行TaskA，会得到结果
> Task :taskC
我是taskC

> Task :taskB
我是taskB

> Task :taskA
我是taskA

所以`mustRunAfter`并不会添加依赖，只是高度Gradle执行的优先级，如果两个Task同时存在，那么就会按照这个定义的优先级执行。

##### finalizedBy 
我们如果希望任务执行结束的时候自动执行某个任务，比如我们在打包结束后自动上报包体积到后台，如果用dependsOn，那么我们就需要类似`打包任务.dependsOn taskUpload`，后续打包就需要通过taskUpload来执行，这样就很别扭，所以这里就有来`finalizedBy`，用于任务执行结束后自动执行其他任务。
```
task taskC {
	doLast{
	println '我是taskC'
	}
}

task taskD {
	doLast{
	println '我是taskD'
	}
}

taskC.finalizedBy taskD
```
执行taskC，会得到结果
> Task :taskC
我是taskC

> Task :taskD
我是taskD

#### 常用Task
其实我们打开Studio右边的gradle面板就会看到很多的项目，里面的每一项其实就是一个Task。我们也可以用一个简单的方法来看下一个项目打包的时候会执行的所有的Task,前面介绍到了我们会构建一个Task的有向无环图，所以我们可以等这个有向无环图构建成功的时候，将所有的task打印一下
```
gradle.taskGraph.beforeTask { Task task ->
    println "executing:  $task.name"
}
```
然后在命令行执行`./gradlew assemble | grep 'executing'`，具体命令后面会有个博客介绍一下，这里先简答说下，`assemble`也是一个Task，我们在Studio的操作面板中执行打包编译实质就是执行这个task，所有这里就相当于执行下这个打包的Task，然后用`grep`过滤下我们刚才打印的关键词
```
executing:  preBuild
executing:  preDebugBuild
executing:  compileDebugAidl
executing:  checkDebugManifest
executing:  compileDebugRenderscript
executing:  generateDebugBuildConfig
executing:  mainApkListPersistenceDebug
executing:  generateDebugResValues
executing:  generateDebugResources
executing:  createDebugCompatibleScreenManifests
executing:  processDebugManifest
executing:  mergeDebugResources
executing:  processDebugResources
executing:  kaptGenerateStubsDebugKotlin
executing:  kaptDebugKotlin
executing:  compileDebugKotlin
executing:  mergeDebugShaders
executing:  compileDebugShaders
executing:  generateDebugAssets
executing:  mergeDebugAssets
executing:  javaPreCompileDebug
executing:  compileDebugJavaWithJavac
executing:  compileDebugSources
executing:  processDebugJavaRes
executing:  checkDebugDuplicateClasses
executing:  mergeDebugJavaResource
executing:  transformClassesWithDexBuilderForDebug
executing:  validateSigningDebug
executing:  signingConfigWriterDebug
executing:  mergeDebugJniLibFolders
executing:  extractProguardFiles
executing:  preReleaseBuild
executing:  compileReleaseAidl
executing:  compileReleaseRenderscript
executing:  checkReleaseManifest
executing:  generateReleaseBuildConfig
executing:  mainApkListPersistenceRelease
executing:  generateReleaseResValues
executing:  generateReleaseResources
executing:  mergeReleaseResources
executing:  createReleaseCompatibleScreenManifests
executing:  processReleaseManifest
executing:  processReleaseResources
executing:  kaptGenerateStubsReleaseKotlin
executing:  kaptReleaseKotlin
executing:  compileReleaseKotlin
executing:  javaPreCompileRelease
executing:  compileReleaseJavaWithJavac
executing:  compileReleaseSources
executing:  mergeDebugNativeLibs
executing:  stripDebugDebugSymbols
executing:  prepareLintJar
executing:  lintVitalRelease
executing:  mergeReleaseShaders
executing:  compileReleaseShaders
executing:  generateReleaseAssets
executing:  mergeReleaseAssets
executing:  signingConfigWriterRelease
executing:  mergeReleaseJniLibFolders
executing:  mergeReleaseNativeLibs
executing:  stripReleaseDebugSymbols
executing:  mergeReleaseGeneratedProguardFiles
executing:  processReleaseJavaRes
executing:  mergeReleaseJavaResource
executing:  transformClassesAndResourcesWithR8ForRelease
executing:  transformClassesAndDexWithShrinkResForRelease
executing:  packageRelease
executing:  assembleRelease
executing:  mergeExtDexDebug
executing:  mergeDexDebug
executing:  packageDebug
executing:  assembleDebug
executing:  assemble
```
后续的介绍也会围绕这个进行介绍，所以这里我先介绍下我认为平时开发中接触到比较多的几个Task吧

|  Task名称   | 作用  |
|  ----  | ----  |
| clean  | 清除缓存，懂的都懂吧~经常用到 |
| assemble | 打包任务 |
| install | 安装任务,会安装我们打出的包到手机|

#### 插件
其实我们了解到现在会发现，其实Gradle的核心就是一个包含丰富语法糖，支持丰富DSL的流程控制框架，而框架的内部其实是没有实质的操作的，所以Gradle的构建便捷其实都是由插件提供支持的。插件可以看作是一系列Task的集合，插件添加了新的任务，然后Gradle按照有向无环图进行顺序执行。在Gradle中插件一般分为两种：
* 脚本插件
  是额外的构建脚本，他会进一步配置构建，我们可以理解我们将部分的配置抽取成一个脚本，然后进行依赖。脚本插件通常可以从本地文件或者远程获取，如果是从本地文件获取则是相对于项目路径，如果是远程获取，则是由HTTP进行指定。
  脚本插件其实并不能是一个真正的插件，他是脚本模块化的基础，所以我们可以把复杂的脚本文件，进行拆分，分段，拆分成一个职责分明的脚本插件。
* 二进制插件
  是实现了Plugin接口的类，并且采取编程的方式来操作构建。可以理解我们自定义一些需要在编译执行的时候来进行一些自定义处理。

插件需要用过`Project.apply()`的方法声明应用，相同的插件可以应用多次。
```
//脚本插件
apply from 'utils.gradle'
//二进制插件
apply from 'java'
```
插件还可以使用插件ID，插件ID作为插件的唯一标示，我们可以注册的时候给插件定义一个唯一ID，后续讲解插件开发的时候会单独讲解。
#### gradle.properties
这个文件前面有提到这个文件，这个文件我们在创建项目的时候，AndroidStudio会自动生成一个这个文件，这个文件是用来配置项目级别的Gradle配置，也就是我们可以在这个文件里配置项目级别的公共属性。
当然这个文件是可以有多个的，其中子项目的gradle.properties会覆盖rootProject的gradle.properties，但是子项目的的gradle.properties属性只会在子项目中可见，只有rootProject的gradle.properties的属性是全局可见的。

```
//gradle.properties
COMPILE_SDK_VERSION=28
MIN_SDK_VERSION=15

//setting.gradle
// 输出Gradle对象的一些信息
def printGradleInfo(){
    println "COMPILE_SDK_VERSION:" + COMPILE_SDK_VERSION
}

printGradleInfo()
```
#### 依赖
gralde之所以能代替Maven，其依赖管理是一大关键因素。这里先简单介绍下依赖的概念，后面会专门开一篇博客讲解依赖的相关内容。
首先，Gradle做为一个项目构建的DSL工程，Gradle需要知道项目构建时需要的一些文件，而这些文件往往除了我们自己编写的项目文件，往往还会用到其他工程的一些文件，例如三方的开源库，自己编写的子项目，这些文件就是项目的依赖，Gradle在项目构建的时候需要告诉它项目的依赖是什么，在哪里能够找到他们，然后帮你加入到构建中，有的可能是在本地，有的可能需要到远端下载，有的甚至是另一个工程。我们先简单的看一个依赖。
```
apply plugin: 'java'
repositories {
    mavenCentral()
    google()
    jcenter()
}
dependencies {
  implementation 'androidx.appcompat:appcompat:1.0.2'
}
```
首先我们在`dependencies`中声明来我们需要的依赖库，也就是`androidx.appcompat:appcompat:1.0.2`,这里往往是`group:name:version`三段式组成，然后gradle在编译的时候知道我们项目的构建需要这个库的依赖支持，那么肯定需要找到这个库，这时候就会去`repositories`中寻找，这里看到我们声明了三个地址分别是maven、google、jcenter仓库。这样在构建的时候就会从这个仓库地址中下载这个依赖库，然后进行构建。

### 总结
这篇博客可能稍微讲的有点乱，Gradle是一个庞大的体系，里面的每一个点都可以展开讲解，细枝末节很多，所以这篇博客还是篇前期的基础概念讲解，后面会针对这里面的接触概念进行专项拓展讲解。希望自己的这篇Gradle系列能帮助大家把Gradle弄懂吃透。