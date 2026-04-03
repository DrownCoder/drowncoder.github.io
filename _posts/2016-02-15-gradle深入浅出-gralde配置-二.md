---
title: 【Gradle深入浅出】——Gralde配置（二）
date: 2021-06-23 23:53:20+08:00
categories: ["Android源码分析"]
source_name: "【Gradle深入浅出】——Gralde配置（二）"
jianshu_views: 2893
jianshu_url: "https://www.jianshu.com/p/9d3ecd0d1be1"
---
[1.【Gradle深入浅出】——初识Gradle](https://www.jianshu.com/p/8e1ddd19083a)
[2.【Gradle深入浅出】——Gradle基础概念](https://www.jianshu.com/p/4bcdf07d4579)
[3.【Gradle深入浅出】——Android Gradle Plugin 基础概念](https://www.jianshu.com/p/6464ef756c5b)
[4.【Gradle深入浅出】——Gradle配置（一）](https://www.jianshu.com/p/eacd7625cc29)
[5.【Gradle深入浅出】——Gralde配置（二）](https://www.jianshu.com/p/9d3ecd0d1be1)

### 一、前言
前一篇博客分析了Gralde配置的三个文件local.properties、gradle.properties、setting.gradle，本篇博客开始分析gradle的工程配置，这些配置参数都是影响我们平时实际工程打包的参数，所以还是很有必要了解的。首先我们要知道gradle打包的核心配置在build.gradle文件，而关于build.gradle父工程和子工程的差异这里就不再说了，前面的博客已有介绍，所以有了前面博客的介绍，我们知道我们工程的打包首先要看父项目的打包配置的build.gralde.

### 二、Root工程的Build.gradle配置
```
// Top-level build file where you can add configuration options common to all sub-projects/modules.

buildscript {
    ext.kotlin_version = '1.3.50'
    repositories {
        google()
        jcenter()
        maven {
            url('http://xxxxxx')
        }
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:3.5.1'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
        // NOTE: Do not place your application dependencies here; they belong
        // in the individual module build.gradle files
    }
}

allprojects {
    repositories {
        google()
        jcenter()
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}

```
我们初始化创建的工程的build.gradle还是比较清晰简单的，首先看到的是`buildscript`,看到内部的内容我们一开始可能会很困惑，这里为什么有`repositories`和`dependencies`的定义，我们每个子工程的build.gradle中也有关于`repositories`和`dependencies`的定义，这两个有什么区别呢？
这里buildScript正如名字的含义那样，表示的是gradle脚本编译过程中需要的资源，比如我们在gradle打包时用到了一些外部依赖项或者第三方插件，那么这时我们就需要在buildScript中声明相关的repo仓库地址，并且在dependencies中声明相应的依赖项。而在其他工程中的build.gradle中声明的repo和denpencies表示的是打包的项目所依赖的资源，也就是我们工程用到的依赖的资源。
repositories表示的是dependencies的repo地址，我们看下配置的源码，我们一般会配置`google()`,`jcenter()`,`maven`这几种，简单看下源码。
```
   /**
     * Adds a repository which looks in Google's Maven repository for dependencies.
     * <p>
     * The URL used to access this repository is {@literal "https://dl.google.com/dl/android/maven2/"}.
     * <p>
     * Examples:
     * <pre autoTested="">
     * repositories {
     *     google()
     * }
     * </pre>
     *
     * @return the added resolver
     * @since 4.0
     */
    @Incubating
    MavenArtifactRepository google();

    /**
     * Adds a repository which looks in Bintray's JCenter repository for dependencies.
     * <p>
     * The URL used to access this repository is {@literal "https://jcenter.bintray.com/"}.
     * The behavior of this repository is otherwise the same as those added by {@link #maven(org.gradle.api.Action)}.
     * <p>
     * Examples:
     * <pre autoTested="">
     * repositories {
     *     jcenter()
     * }
     * </pre>
     *
     * @return the added resolver
     * @see #jcenter(Action)
     */
    MavenArtifactRepository jcenter();

    /**
     * Adds a repository which looks in the local Maven cache for dependencies. The name of the repository is
     * {@value org.gradle.api.artifacts.ArtifactRepositoryContainer#DEFAULT_MAVEN_LOCAL_REPO_NAME}.
     *
     * <p>Examples:</p>
     * <pre autoTested="">
     * repositories {
     *     mavenLocal()
     * }
     * </pre>
     * <p>
     * The location for the repository is determined as follows (in order of precedence):
     * </p>
     * <ol>
     * <li>The value of system property 'maven.repo.local' if set;</li>
     * <li>The value of element &lt;localRepository&gt; of <code>~/.m2/settings.xml</code> if this file exists and element is set;</li>
     * <li>The value of element &lt;localRepository&gt; of <code>$M2_HOME/conf/settings.xml</code> (where <code>$M2_HOME</code> is the value of the environment variable with that name) if this file exists and element is set;</li>
     * <li>The path <code>~/.m2/repository</code>.</li>
     * </ol>
     *
     * @return the added resolver
     */
    MavenArtifactRepository mavenLocal();
```
所以可以看到google(),jcenter(),mavenLocal()就表示我们引入了三个地址的仓库，下载denpendencies库的时候就会按照顺序从这几个url中找是否有对应的库，如果有则会下载下来。
那么如何指定本地路径作为repo地址呢？我们在开发gradle插件的时候可能会遇到这个问题。
```
   maven{
            url 'file://E:/libs/localMaven/'
        }
```
接着往下看，会看到脱离了buildScript的代码块，也就是说明现在的配置不是用于gradle编译使用了，而且真正打包使用的配置了。
```
allprojects {
    repositories {
        google()
        jcenter()
    }
}
```
正如名字`allprojects`一样，这个就是我们统一为所有的子project配置的地方，具体为什么语法糖是这样的，后面会专门开一篇博客讲一下关于这里的语法糖，这里如果有困惑的我们其实可以把代码改成这样。
```
allprojects {
    println "this.name:" + name
    repositories {
        google()
        jcenter()
    }
}
```
这样我们就会发现这其实是一个for循环，会将我们依赖的子project都打印出来，所以这里配置的所有配置都会在全局的project生效，而如果子project在build.gralde的配置会覆盖这里的配置，所以我们如果做全局配置，就可以在这里进行统一配置。
接下来就是一个统一的配置，可以看到定义了一个task，关于task的定义前面已经讲到过，这里可以看到定义了一个`clean`的task，可以看到clean这个task继承了系统的delete的task，所以我们可以在task内部用到delete的功能，而clean的作用也很简单，就是把`/projectDir/build`目录给清理了，所以我们有时候在编译打包时有时候会发现自己的一个改动没有生效，很有可能就是缓存的问题，先clean一下再build就好了。
这样根目录的build.gradle就分析完了，总体来看下根目录的build.gradle会做哪些事情：
* 构建脚本的配置，例如gradle插件的版本，构建依赖的repo，注意这里都是和构建有关的
* 定义全局配置，可以定义所有子project的配置
* 定义了一个clean的task，用于清理缓存目录
接下来来看下主project的build.gradle

```
apply plugin: 'com.android.application'
apply plugin: 'kotlin-android'
apply plugin: 'kotlin-android-extensions'
apply plugin: 'kotlin-kapt'

android {
    compileSdkVersion 29
    buildToolsVersion "29.0.2"
    defaultConfig {
        applicationId "com.xuan.studydemo"
        minSdkVersion 15
        targetSdkVersion 29
        versionCode 1
        versionName "1.0"
        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
    }
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}

dependencies {
    def lifecycle_version = "2.2.0"
    implementation fileTree(dir: 'libs', include: ['*.jar'])
    implementation "org.jetbrains.kotlin:kotlin-stdlib-jdk7:$kotlin_version"
    implementation 'androidx.appcompat:appcompat:1.0.2'
    implementation 'androidx.core:core-ktx:1.0.2'
    implementation 'androidx.constraintlayout:constraintlayout:1.1.3'
    testImplementation 'junit:junit:4.12'
    androidTestImplementation 'androidx.test.ext:junit:1.1.0'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.1.1'
    implementation 'androidx.lifecycle:lifecycle-extensions:2.2.0'
    kapt "androidx.lifecycle:lifecycle-compiler:$lifecycle_version"
}

```
首先看到的是`apply plugin`，这个就是gradle中的**插件**，关于插件的自定义我们后面再详细讲解，但对于插件的定义我们要在这里先了解下，不然后面对于流程会有些不理解。前面一篇[博客](https://www.jianshu.com/p/6464ef756c5b)有讲解关于插件的基础概念，这里再结合这里讲一下。
>gradle的本质是一个流程控制框架，提供了基础的task和方便的流程控制的语法糖，而AGP是Google以Gradle为基础，并且结合Android的打包流程，专门开发的一个插件。

所以简单的理解，就是Google将Android的打包流程，例如编译、资源合并、混淆、签名等一系列的打包流程开发成一个个Gradle中的Task，而AGP再将这些Task整合成流程，利用Gradle方便的流程控制和配置打包，整合成一个AGP插件。
所以可以看到我们经常会看到`apply plugin: 'com.android.application'`,`apply plugin: 'com.android.library'`,这其实就是AGP中定义的插件，因为依赖了这些插件，所以有了下面的`android`的配置，我们可以试下将`apply plugin: 'com.android.application'`注释掉，这时候再build就会发现这样的错误的信息。
```
Could not find method android() for arguments [build_kmftzroc9bwua5m7q41tme6p$_run_closure1@47c045f] on project ':app' of type org.gradle.api.Project.
```
这也就是说明`android()`这个配置其实不是gradle自带的，而是AGP中新增的。接下来来看看android的配置。
**compileSdkVersion**
表示的Gradle用哪个版本的AndroidSDK编译项目，所以当我们使用新版本的API时就需要使用对应版本的AndroidSDK，而**compileSdkVersion只影响编译时行为，不影响运行时的行为**，如果我们想要使用最新版本的的API,就可以将compileSdkVersion升级到对应的版本，并且如果有老的API过期，在编译时就会警告或者报错。
**buildToolsVersion**
表示的编译工具集的版本号，例如在打包时使用的aapt,dx等工具版本，都是根据这里的版本制定的版本来寻找的。也就是我们构建项目需要的工具集的版本号，一般是在sdk/build-tools/目录中，如果说刚才说到的`compileSdkVersion`表示的是我们使用的AndroidSDK版本，那么`buildToolsVersion`就是我们的编译工具的版本，然后使用这个编译工具配合AndroidSDK来编译工程项目，所以一般`buildToolsVersion`的版本会和`compileSdkVersion`大版本相同。
**minSdkVersion**
表示的是我们的应用程序运行所需要的最低版本号，如果手机系统版本大于这个版本，那么Android系统会阻止应用安装应用，而如果我们没有显示的声明`minSdkVersion`,那么默认值就是1，也就是可以运行在所有的Android机器上。
**targetSdkVersion**
正如字面意思，表示的是我们应用的目标版本，所以也是最重要的和我们应用适配有关的字段，在`targetSdkVersion`设置的版本表示我们已经对当前版本及以下的版本充分适配测试，所以能够兼容小于等于`targetSdkVersion`所有的手机，所以这个也是Android系统向前兼容的判断依据。比如我们设置的`targetSdkVersion`版本是26，而如果我们运行项目在一个28版本系统的手机上，Android系统判定我们应用的`targetSdkVerison`是26，就会向前兼容，使用API时就会使用26及26版本以下的API,如果某个API在28上有变更，我们的应用就不会体现出新特性。

所以综上所述，我们应用的版本关系应该是：
> minSdkVersion<=targetSdkVersion<=compileSdkVersion(buildToolsVersion)
#### defaultConfig
接下来来看下defaultConfig的配置，首先看下这个是用来配置什么东西的，当然最便捷的就是先看AGP的源码。
```
/**
     * Specifies defaults for variant properties that the Android plugin applies to all build
     * variants.
     *
     * <p>You can override any <code>defaultConfig</code> property when <a
     * href="https://developer.android.com/studio/build/build-variants.html#product-flavors">
     * configuring product flavors</a>.
     *
     * <p>For more information about the properties you can configure in this block, see {@link
     * ProductFlavor}.
     */
    public void defaultConfig(Action<DefaultConfig> action) {
        checkWritability();
        action.execute(defaultConfig);
    }
```
这里我们先忽略下为什么这里是一个方法，这个其实涉及到Gradle的一个特性，后续讲Gradle源码的时候会专门分析，这里先看注释来看下是做什么作用的，在这个系列的第三篇博客我们有提到过关于AGP中buildType,Flavor,defaultConfig的区别和概念，这里再来看应该就清晰很多，其实defaultConfig就是对于不同的产物类型的默认配置，而如果我们在buildType或者Flavor中配置，那么就会覆盖defaultConfig里的配置。具体的顺序之前也有提到，这里在说明一下：
>按优先级从高到低: buildType->Flavor->defaultConfig
首先来看下defaultConfig的配置方式，defaultConfig和Gradle之前的配置一样，支持语法糖和方法调用两种形式
```
defaultConfig {
  minSdkVersion 15
}

//等价于
defaultConfig {
  minSdkVersion(15)
}
```
接下来来看下核心属性，这里只列举几个我认为比较常见，其他的这里有可以查看[Google的官方文档](https://google.github.io/android-gradle-dsl/3.3/com.android.build.gradle.internal.dsl.DefaultConfig.html)，或者这里有一篇[博客](https://juejin.cn/post/6844903941528895502)讲的也比较详细。
* applicationId
应用的id，也就是我们常说的包名，Android中的应用包名是唯一的，所以我们是用包名来区分一个唯一的应用的。
* comsumerProguardFiles\consumerProguardFile\proguardFiles
```
defaultConfig {
	consumerProguardFiles 'consumer-rules.pro'
}

// 因为该属性是一个 List<File> 类型，如果需要多个文件配置，则如下所示
defaultConfig {
	consumerProguardFiles 'consumer-rules.pro','consumer-test-rules.pro'
}

proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
```
首先说下comsumerProguardFiles，很多博客有说到一个概念
>这个属性只作用于我们创建的library中，也就是不是在我们的主项目中配置使用的，它是负责配置library被编译打包时使用的混淆规则的。

但其实我感觉这里这样描述是有错误或者说有歧义的，接下来我们来分析下这个问题。
首先看下proguardFiles这个属性，这个是用于配置混淆属性的，也就是我们平时打包时当开启了minifyEnabled属性时，这时候Android打包的过程中，在混淆时就会读取我们通过proguardFiles配置的文件列表，来进行相应的混淆配置和防混淆配置。这个属性适用于App也同样适用于library，也就是我们如果打一个aar包时，也可以通过配置proguardFiles属性来进行混淆。哪可能有人要问来，哪comsumerProguardFiles是用于干什么的呢？
我们在使用一些三方开源库，可能会发现一种情景，库的Uage要求不仅仅需要通过maven依赖，还需要手动写入一些keep文件，这时就会发现很麻烦，为什么三方库的混淆配置需要我们手动加到我们自己工程里的，不能在三方库内部配置好吗？
comsumerProguardFiles就是用于这种场景的，我们在通过comsumerProguardFiles配置了混淆配置后，我们打出的release的aar，我们解压后就会发现里面包含一个`proguard.txt`文件，而这个文件内容其实就是我们的comsumerProguardFiles配置，也就是我们的混淆配置会被打入aar文件中，而proguardFiles就不会有这样的效果。
然后在App引入aar后，Android在进行apk打包的时候，就会对`proguard.txt`进行合并，然后最终在apk打包混淆时对全部文件生效。
这时候我们就可以得出几个结论：
>comsumerProguardFiles用于用于当三方库被App依赖时，不仅仅会对三方库生效，也会对全局的Java代码生效
>proguardFiles仅用于当次编译混淆时使用，并不会被持久化到aar中，所以我们在aar配置的proguardFiles只会当前aar打包的混淆时有效，并不会被写入`proguard.txt`文件中，也就是aar中的proguardFiles配置不会影响接入的Apk的混淆。

这里大家可以测试一下，如果在一个aar的comsumerProguardFiles配置，增加一个`-dontobfuscate`表示不进行混淆，然后打出一个aar包，用App项目依赖这个aar，就会发现我们在app中就算打开了混淆，也会失效，就是因为我们在aar的comsumerProguardFiles配置了`-dontobfuscate`这个属性，最终被合并到apk打包的`proguard.txt`文件中，对全部的Java文件进行生效了，所以就导致全局的混淆都被关闭，这样看这个配置还是要慎重的。
* javaCompileOptions
配置编译时 java 的一些参数，例如我们使用 annotationProcessor 时所需要的参数。
```
defaultConfig {
	javaCompileOptions {
        annotationProcessorOptions{
			arguments = []
			classNames ''
			....
		}
	}
	......省略其他配置
}
```
* ndk
用于配置abi过滤，配置我们打出来的apk支持什么架构类型的CPU
```
defaultConfig {
	// ndk中，目前只有 abiFilter 一个属性，所以 ndk 目前来说只用于 abi 的过滤
	ndk {
        abiFilter 'armeabi-v7a'
    }
	...
}
```
* versionCode/versionName
这里两个的区别网上其实挺多讲解的，但其实可以简单理解就是：versionName就是一个名字，是一个字符串，没任何作用，仅给用户展示区分使用，versionCode是最重要的参数，是一个int值，应用市场的更新/判断新旧包都是用这个，对开发者透明，不对用户透露。可以出现一个versionName对应多个versionCode，但是最好不要这样使用，因为这样很容易导致版本乱了，后续的运营数据分析，线上问题修复，版本升级，渠道管理都可能会有问题，所以最好的就是一对一的关系。
最后介绍一个defaultConfig的两个特性，用于动态生成变量使用。
首先是我们在defaultConfig配置的属性，在构建时都会在对应的产物变体目录下生成对应的BuildConfig.java文件，此文件会讲我们之前配置的属性变成对应的Java常量，这样我们就可以在Java代码中进行使用。
```
public final class BuildConfig {
  public static final boolean DEBUG = Boolean.parseBoolean("true");
  public static final String APPLICATION_ID = "com.xuan.studydemo";
  public static final String BUILD_TYPE = "debug";
  public static final String FLAVOR = "";
  public static final int VERSION_CODE = 1;
  public static final String VERSION_NAME = "1.0";
}
```
而如果我们想在编译时自定义一些相应的属性变量，这时候就可以用`buildConfigField(type,name,value)`方法，用于向构建时生成BuildConfig.java类中新增属性。例如：
```
defaultConfig {
    ...
    // 是否是Monkey包
    isMonkey = project.hasProperty('isMonkey') ? isMonkey : 'false'
    buildConfigField "boolean", "IS_MONKEY", isMonkey
    
    // 添加模块对应的模块名
    buildConfigField "String", "MODULE_NAME", "\"${project.name}\""
}
```
对应我们如果编译后，就会在产物目录中发现BuildConfig.java类中就有我们相应的变量定义。
```
public final class BuildConfig {
  public static final boolean DEBUG = Boolean.parseBoolean("true");
  public static final String APPLICATION_ID = "com.xuan.studydemo";
  public static final String BUILD_TYPE = "debug";
  public static final int VERSION_CODE = 1;
  public static final String VERSION_NAME = "1.0";
  // Fields from default config.
  public static final boolean IS_MONKEY = true;
  public static final String MODULE_NAME = "app";
}
```
这样我们就可以在我们的代码逻辑中加入相关的判断，例如Monkey包可以不显示某些入口，直接登录等等。
除了`buildConfigField(type,name,value)`方法外，还有一个方法也是用于在编译时新增资源的。`resValue(String type, String name, String value)`,这个方法相当于在res/values中新增一个资源。例如：
```
buildTypes {
        debug {
            resValue("String", "app_name_monkey", "Monkey for App")
        }
    }
```
这样我们在编译后，就会生成一个资源文件。
而我们如果要在代码中使用这个资源，就可以通过下面的方式来获取。
```
getResources().getString(R.string.app_name_monkey);
```
最后是关于`buildTypes`的介绍，其实关于`buildTypes`和`productFlavors`的区别，前面已经有一篇博客比较详细的介绍，这里再简单总结下，`buildType`就是我们的构建类型，比如debug包，release包，monkey包，不同的构建类型有不同的构建方式，比如debug包一般不会混淆，monkey包一般会加入一些apm的操作和库，release一般会开启混淆和签名。而`productFlavors`就是指的产物类型，比如我们打的不同的渠道包，比如内部包，GooglePlay包，国内市场包，而`buildTypes`和`productFlavors`会以排列的方式进行汇总，所以对应的就是`n*m`的关系，比如GooglePlay版的Debug包/release包，等等。对应的这个最终的产物就是我们的`BuildVariant`，所以对应到一个公示：
>BuildVariant = ProductFlavor x BuildType

就很好理解这些了，而这些对应的配置优先级顺序就是：
>按优先级从高到低: buildType->Flavor->defaultConfig
接下来来看下里面常用的一些属性。
* shrinkResources
`shrinkResources`是google官方提供的优化无用资源的配置，shrinkResources和minifyEnabled必须同时开启才有效，这里具体`shrinkResources`的实现细节就不展开了，后续有时间可以专门写篇博客学习分析下，但是这里说几个这个属性特殊的地方。
>shrinkResources中被移除的资源是真正被删除了吗？

这里先说下结论，**开启后无用的资源和图片并没有被真正的移除掉，而是用了一个同名的占位符号**，具体我们可以自己试下。

>shrinkResources会将所有无用的资源都移除吗？

这个也是不会的，shrinkResources在严格模式下，其实是会检测我们代码中静态声明的一些字符串，如果图片中有命中我们定义的字符串，就算资源没有被使用，但是也不会被移除，具体这里有篇[博客]()比较详细的讲解了。
* minifyEnabled
当设置为true的时候，就会开启代码混淆，压缩apk，还会对资源进行压缩，对无用的代码和多余的代码在编译打包的时候就会被移除掉，而具体的混淆规则配置前面也有提到，就是我们关于`proguard.pro`的配置。
>如何方式资源被混淆移除

我们可以在res/raw/keep.xml(避免被误删除)配置。例如：
```
<?xml version="1.0" encoding="utf-8"?>  
<resources xmlns:tools="http://schemas.android.com/tools"  
  tools:keep="@layout/activity_main,@drawable/comfirm_bg"/>  
```
>代码混淆的结果和细节如何追溯？

代码混淆生成apk之后，项目下面会多出来一个proguard文件夹，proguard文件夹中四个文件的作用。
dump.txt : 描述了apk中所有类文件中内部的结构体。

mapping.txt : 列出了原始的类、方法和名称与混淆代码间的映射。

seeds.txt : 列出了没有混淆的类和方法。

usage.txt : 列出congapk中删除的代码。

* signingConfig
从字面知道有 “签署配置” 的意思。该配置的作用，就是为编译出来的apk签上我们的“名字”，这样才能将apk发布安装到用户的设备上。设备（手机、TV等）对 apk 的唯一认定，并不只是包名，而是 包名和签名，其中一项不同，都会认为这个 apk 包是不同的。
>包名的不同，表现为多个应用。签名的不同，在应用升级时表现为无法安装，如果是第一次安装，则不会有问题。

具体可以看下这篇[博客](https://juejin.cn/post/6844904008054734862)
* resConfigs
作用是指定打包时编译的语言包类型，未指定的其他语言包，将不会打包到apk文件中，从而减少apk体积的大小。

最后介绍下关于依赖的内容，这里但从使用层面介绍下几种常用依赖的关键字的区别：
首先介绍下gralde不同版本下的几个关键字的区别：
compile依赖关系已被弃用，被implementation和api替代;provided被compileOnly替代;
* implementation
与compile对应，会添加依赖到编译路径，并且会将依赖打包到输出（aar或apk），但是在编译时不会将依赖的实现暴露给其他module，也就是只有在运行时其他module才能访问这个依赖中的实现。使用这个配置，可以显著提升构建时间，因为它可以减少重新编译的module的数量。建议，尽量使用这个依赖配置。
* api
与compile对应，功能完全一样，会添加依赖到编译路径，并且会将依赖打包到输出（aar或apk），与implementation不同，这个依赖可以传递，其他module无论在编译时和运行时都可以访问这个依赖的实现，也就是会泄漏一些不应该不使用的实现。举个例子，A依赖B，B依赖C，如果都是使用api配置的话，A可以直接使用C中的类（编译时和运行时），而如果是使用implementation配置的话，在编译时，A是无法访问C中的类的。
* compileOnly
与provided对应，Gradle把依赖加到编译路径，编译时使用，不会打包到输出（aar或apk）。这可以减少输出的体积，在只在编译时需要，在运行时可选的情况，很有用。
* annotationProcessor
与compile对应，用于注解处理器的依赖配置。
### 三、总结
本篇博客介绍了gradle的常用配置，至此关于Gradle的基础知识准备告于段落了，虽然没有很全面的把Gradle基础配置都包含进来，但5篇博客下来基本上对于Gradle的基础概念有了一个大体的认识和思路，所以接下来准备从源码角度来学习Gradle，为什么Gradle支持这样的语法糖，AGP的打包流程是什么样的，依赖关系是如何打入APK中的，等等问题都需要我们从Gradle和AGP的源码角度来学习，所以接下来的博客就结合源码来继续学习Gradle。