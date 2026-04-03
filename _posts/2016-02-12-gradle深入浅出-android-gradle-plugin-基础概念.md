---
title: "【Gradle深入浅出】——Android-Gradle-Plugin-基础概念"
date: 2020-12-31 16:50:39+08:00
categories: ["Android源码分析"]
source_name: "【Gradle深入浅出】——Android-Gradle-Plugin-基础概念"
jianshu_views: 5041
jianshu_url: "https://www.jianshu.com/p/6464ef756c5b"
---
[1.【Gradle深入浅出】——初识Gradle](https://www.jianshu.com/p/8e1ddd19083a)
[2.【Gradle深入浅出】——Gradle基础概念](https://www.jianshu.com/p/4bcdf07d4579)
[3.【Gradle深入浅出】——Android Gradle Plugin 基础概念](https://www.jianshu.com/p/6464ef756c5b)
[4.【Gradle深入浅出】——Gradle配置（一）](https://www.jianshu.com/p/eacd7625cc29)
[5.【Gradle深入浅出】——Gralde配置（二）](https://www.jianshu.com/p/9d3ecd0d1be1)

### 前言
前面一篇博客讲解了Gradle的基本概念，里面也提到Gradle的实质其实是一个流程控制框架，本身是没有业务逻辑的，而其本身的强大之处在于语法糖还有版本控制还有插件支持，这个就给复杂的工程结构构建提供了灵活的控制方式。所以这篇博客就针对我们经常使用的AGP来进行一个基础概念讲解。
首先来看下什么是AGP，全称`Android Gradle Plugin`也就是Google针对Android项目的构建专门开发的一个Gradle插件。
#### Configurations
这里首先讲的是`Configurations`，为什么要讲这个呢，因为这个概念其实在后面我们Android工程的编译构建发现是一个非常重要的概念，那就是**依赖管理**。
前面一篇博客我们简单的介绍来依赖的概念，依赖分为`repositories`和`dependencies`，分别表示依赖库的下载地址和具体的依赖库。这里我们先考虑一种场景，比如我们需要在编译时使用一组依赖A，在测试时需要依赖一组依赖B用于测试，这时候就会发现我们肯定需要一个字段或者一个策略来区分这两组依赖，所以Gradle就提出了`configuration`的概念，这里面每一组依赖称为一个`Configuration`。我们首先来看下`Configuration`如何定义。
```
//方式一
configurations {
   testDenp
}
//方式二
configurations.create('testDenp')
```
这样我们就定义了一个名为testDenp的Configuration，这样我们在声明依赖的时候，就可以通过定义不同的Configuration来区分不同条件下的依赖关系。那么我们来看下如何使用我们定义的Configuration。
```
dependencies {
   testDenp 'androidx.appcompat:appcompat:1.0.2'
}
```
这样我们就讲一个库加入我们的`testDenp`组中了，后面我们在构建的时候就可以按照我们地方需求用不同组的依赖来进行构建了。
这里我们列举下常用的几个configuraion，如compile,runtime之类已经默认被加入到java插件中了，而androidTestCompile,implementation这类就是AGP中默认添加的Configuration。
这里其实我挺想吐槽一下这里的命名的，起初我一直搞不明白configuraion的含义，我感觉如果叫做`denpendencyGroup`之类的会更让人容易理解些。

#### BuildType
字如其名,`BuildType`表示的就是构建类型，我们常说的`release`和`debug`就是两个`BuildType`,AGP默认会给项目增加Debug和Release两个BuildType,并且默认配置了一套默认值，例如Debug中的debuggable默认为true，Release的debuggable默认为false.
Build types（构建类型）定义了一些构建、打包应用时 Gradle 要用到的属性，主要用于不同开发阶段的配置，如 debug 构建类型要启用 debug options 并用 debug key 签名，release 构建类型要删除无效资源、混淆源码以及用 release key 签名
而我们想要自己定义一套我们的buildType如何定义呢？
```
android {
    ...
    defaultConfig {...}
    buildTypes {
        release {
            //开启混淆
            minifyEnabled true
            //混淆规则文件
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }

        debug {
            //apk的后缀
            applicationIdSuffix ".debug"
        }
        
        //debug的一个扩展
        develop {
            // 复制debug的属性和签名配置
            initWith debug
            applicationIdSuffix ".develop"
        }
    }
}
```
只需要在`android{}`中的`buildTypes{}`中增加一种类型即可。这里有几点需要注意：
* 配置buildTypes之前，必须要配置signingConfigs，把签名文件配好，否则就会出现installTask缺失的情况。
* 我们可以使用`initWith`方法来继承一个配置，可以理解成拷贝了debug这一构建类型的所有变量，因为我们知道，每一个构建类型都有一些默认的变量，例如debuggable、zipAlignEnabled等，使用该配置就免去为新增的构建类型定义所有的变量。
我们每新建一个BuildType都会创建一个新的assemble任务，assembleDebug和assembleRelease两个Task在上面已经提到过，这里就会新增一个assembleDevelop这样的任务，我们通过`./gradlew assembleDevelop`就会按照这个BuildType来打包。必须在 app 模块下的 build.gradle 中定义新的构建类型，gradle 才会生成新的task。
而BuildType中常用的定义的属性有

|  属性 |   描述  |
|  ----  | ----  |
|  boolean debbuggable   |  该构建类型是否生成一个可调式的apk  |
|  boolean minifyEnabled   |    是否可以移出无用的java代码，默认为false  |
|  Boolean multiDexEnabled   |  是否可以分包  |
|  File multiDexKeepFile   |    指定放在main dex内的类，如果设置则它的格式为一个类一行：com/example/MyClass.class  |
|  File multiDexKeepProguard   |    指定用在main dex 的类上的混淆文件，跟系统混淆文件联合使用  |
|  String name   |  这种构建类型的名称  |
|  proguardFiles   |    指定插件使用的混淆文件  |
|  SigningConfig signingConfig   |  签名配置文件  |
|  boolean zipAlignEnabled   |  是否使用zipAlign优化apk,Android sdk包里面的工具，能够对打包的应用程序进行优化，让整个系统运行的更快  |
|  String versionNameSuffix   |     VersionName的后缀  |

#### ProductFlavor
和上面提到的BuildType一样，`ProductFlavor`也是用于区分一种构建场景的设置，只不过维度不一样，这里指的是构建渠道，我们在打包发布的时候可能经常有这样的需求，不同的市场渠道号是不一样的，这样我们就可以定义不同的Flavor，然后进行配置。
```
android {  
 
    productFlavors {
        kuan {}
        xiaomi {}
        qh360 {}
        baidu {}
        wandoujia {}
    }  
 
    productFlavors.all { 
        flavor -> flavor.manifestPlaceholders = [UMENG_CHANNEL_VALUE: name] 
    }
}
```
也可以通过`productFlavors.all` 的代码所有 flavor 都会执行。
flavor会和buildType做一个组合,生成编译task
如果增加了flavor名为 dev, 会新增assembleDevRelease 和assembleDevDebug 命令。
所以结合上面的BuildType,我们就可以组合出例如`小米市场Debug包`、`官方市场Release包`。
并且我们每创建一个Flavors，对应的依赖也可以生成对应的依赖关系，例如`xiaomiCompile`。
#### BuildVariant
上面介绍了`BuildType`和`ProductFlavor`，那么这里说的`BuildVariant`是什么呢？这里放一个公式立马就清晰了许多。
```
BuildVariant = ProductFlavor x BuildType
```
也就是我们刚才上面说的BuildType和ProductFlavor的组合，最终来构建产物，我们Studio面板的左边的侧边栏就有对应的`BuildVariant`选项，用于我们来进行构建选择。
![Studio](/assets/img/posts/0f4c59c643d7e6d6.png)

例如如下的配置：
```
productFlavors {
    pro {
    }

    fre {
    }
}

buildTypes {
    debug {
    }
    release {
    }
}
```
这两个维度的组合，会产生如下包：
* proDebug
* proRelease
* freDebug
* proRelease
这里有几个地方需要注意下：
* 1.buildTypes不能设置 applicationId
* 2.productFlavors不能设置 minifyEnabled，如果需要同时设置混淆和applicationId,需要flavor和buildType组合

#### BuildConfig
BuildConfig是android studio在打包时自动生成的一个java类。我们可以理解是我们在构建时生成的一个Java静态类，我们可以在这个类里存放打包时的相关常量，例如`IS_DEBUG`这样的字段，用于判断我们构建的包是不是debug包。
BuildConfig类在项目工程的build/generated/source/buildConfig/androidTest或debug或release中，这些目录中的BuildConfig类中有相同的常量字段。
##### BuildConfig的生成
```
defaultConfig {
      ...
		  // 自定义的方法就是 buildConfigField ，这种是groovy写法
      // 三个参数分别是 type (类型) ， name (命名) ， value(值)
      buildConfigField 'int' , 'SEVER_CONFIG' , "1"

  		// 当然写成这种更容易看懂,这种写法更像java。
  		// 三个参数分别是 type (类型) ， name (命名) ， value(值)
  		buildConfigField("int" , "SEVER_CONFIG" , "1")
    }
```
就像上面举例一样，然后我们使用`buildConfigField`方法，然后`rebuild`一下，我们就会在刚才的提到的那个目录看到生成的`BuildConfig`类。
这里要注意下， "1" 对应的是1,如果是String加上\"号,所以是`"\"1\""`

而可以配置BuildConfig的地方有很多，那么优先级是什么样的呢？
>按优先级从高到低: buildType->Flavor->defaultConfig

例如同时存在同一变量定义.
```
productFlavors {
    dev {
      buildConfigField "String", "ADD_BY_FLAVOR_DEV", "\"set_in_flavor\""
      }
}
    
defaultConfig {
 
        buildConfigField "String", "ADD_BY_FLAVOR_DEV", "\"set_in_default_config\"" 
}
    
buildTypes { 

    debug { 
         buildConfigField "String", "ADD_BY_FLAVOR_DEV", "\"set_in_build_type\"" 
    }
}

```
最终 buildTypes的会生效.
而且这个优先级关系在很多场景下都有效，例如Manifest文件冲突，后续专门开一篇博客讲解吧。

#### SourceSet
java插件引入了一个概念叫做SourceSets，通过修改SourceSets中的属性，可以指定哪些源文件（或文件夹下的源文件）要被编译，哪些源文件要被排除。Gradle就是通过它实现Java项目的布局定义。
SourceSet 可以定义项目结构，也可以修改项目结构。Java插件默认实现了两个SourceSet，main 和 test。每个 SourceSet 都提供了一系列的属性，通过这些属性，可以定义该 SourceSet 所包含的源文件。比如，java.srcDirs，resources.srcDirs 。Java 插件中定义的其他任务，就根据 main 和 test 的这两个 SourceSet 的定义来寻找产品代码和测试代码等。
例如我们定义我们项目的Java文件的目录。
```
android {
    sourceSets {
        main {
            manifest.srcFile 'AndroidManifest.xml'
            java.srcDirs = ['src']
            resources.srcDirs = ['src']
            aidl.srcDirs = ['src']
            renderscript.srcDirs = ['src']
            res.srcDirs = ['res']
            assets.srcDirs = ['assets']
            jniLibs.srcDirs = ['libs']
        }

}
```
官方对于`SourceSets`的配置项的介绍：
![配置项](/assets/img/posts/2604dab483c9fd90.png)

当然SourceSets也可以指定多个路径，比如如果我们指定我们的Java路径是`src/main.java`我们在这个目录下使用Studio创建Java文件，就会发现有Javb Class的选项
![src/java](/assets/img/posts/357a0c5b26d59eac.png)

但如果我们这时候在src目录下新建一个`src/test`目录，我们再使用Studio创建文件，就会发现没有Java Class的选项，这就是因为我们配置来`SourceSets`，所以我们需要在`Sourcesets`中增加一个路径。
![image.png](/assets/img/posts/a97fd6af8a8128dd.png)

```
android {
//第一种写法
    sourceSets {
        main {
            java {
                srcDir 'src/main/java'
                srcDir 'src/test' //指定 test 为源码目录
            }
        }
    }
}
//第二种写法
android {
    sourceSets {
        main {
            java.srcDirs( 'src/main/java' , 'src/test' )
        }
    }
}
```
这样我们重新build一下，就会发现可以在这个目录下新建Java文件。

### 总结
这篇博客从AGP的角度来看了下Android中Gradle的相关配置项的基础概念，支持通过前三篇博客我们应该对于Gradle有了一个基本的掌握和理解，接下来我们就开始深入Gradle，开始我们的Gradle的学习旅程吧。