# 第一章 Activity的生命周期和启动模式
## 1.1.1典型情况下的生命周期分析
1)Activity的生命周期：
onCreate->onRestart->onStart->onResume->onPause->onStop->onDestroy
2)onStart:这时Activity已经可见了，但是还没有出现在前台
3)onResume:这时Activity已经可见了，并且出现在前台开始活动。（这时才真正可见）
4)Activity1—>Activity2，先执行完Activity1的onPause方法再执行Activity的onCreate->onStart->onResume方法，再执行Activity1的onStop方法。（Activity的启动流程源码中需要栈顶的Activity先执行完onPause后再执行跳转Activity的生命周期），所以在Activity的onPause方法中不能执行重量级操作，太耗时导致Activity跳转慢。
**由此联想到Activity的生命周期和View的生命周期的关系，后面分析**
## 1.1.2异常情况下的生命周期分析
### 1资源相关的系统配置发生改变导致Activity被杀死并重新构建（屏幕翻转）
1)当系统配置发生改变后，Activity会被销毁（可以阻止），其onPause、onStop、onDestroy均会被调用，由于是异常情况下终止的，系统会调用onSaveInstanceState来保存当前Activity的状态，执行时机在onStop之前，但和onPause没有既定的时序关系，可能之前可能之后。需要强调的一点，这个方法只会出现在Activity被异常终止的情况下，正常情况下系统不会回调这个方法，当Activity被重新创建后，系统会调用onRestoreInstanceState，并把Activity销毁时onSaveInstanceState方法所保存的Bundle对象作为参数传给onRestoreInstanceState和onCreate方法。因此可以通过onRestoreInstanceState和onCreate方法中的Bundle对象判断Activity是否是被建。OnRestoreInstanceState调用在onStart之后。
2)系统默认会保存Activity的视图结构，在Activity重启时会恢复这些数据。具体某一个View保存了哪些数据可以查看View的onSaveInstanceState和onRestoreInstanceState方法源码。
3)保存和恢复View的层次结构，系统的流程是首先Activity调用onSaveInstanceState保存，然后Activity会委托Window去保存数据，Window在委托顶级容器保存数据。顶层容器是一个ViewGroup，再一一通知子元素保存数据。这里用到了**委托的思想，后面学习设计模式**。
### 2.如何系统配置发生改变后，Activity不被重新创建
1)在AndroidMenifest.xml中配置configChanges属性
2)常用属性
locale:设备的本地位置发生了的改变，一般指切换了系统语言。
orentation:屏幕方向发生了改变。
keyboardHIdden:键盘的可访问性发生了改变，比如用户调出了键盘。
3)这时系统不会调用onSaveInstanceState和onRestoreInstanceState，会调用onConfigurationChanged方法。
## 1.2 Activity的启动模式
### 1.2.1 Activity的LaunchMode
1)四种启动模式
standard:标准模式，每启动一个Activity都会创建一个Activity实例。
singleTop:栈顶复用
singleTask：栈内复用，可以通过TaskAffinity指定任务栈，如果没有该任务栈，则重新创建一个任务栈，再创建一个Activity实例；如果有该任务栈，则看该任务栈中是否有该Activity实例，有，则将其上面的Activity全部移出栈，将该Activity放到栈顶；没有，则创建一个Activity实例，放到栈顶。
singleInstance:单实例模式，Activity单独的位于一个栈中。
2)onNewIntent
复用的Activity会执行onNewIntent，不会执行onCreate,onStart方法，在onResume之前调用。例如ActivityA->ActivityA，则会执行onPause->onNewIntent->onResume
3)TaskAffinity
用于在AndroidMenifest.xml中配合singleTask指定启动栈的栈名。注意taskAffinity属性的值为字符串，且中间必须包含有包名分隔符“.”
4)两种方式来指定Activity的启动模式
1.通过在AndroidMenifest.xml中指定launchMode
2.通过在Intent中通过addFlags()来设置标志位
区别：首先优先级第二种高于第一种，当两种同时存在以第二种为准；第一种无法为Activity指定FLAG_ACTIVITY_CLEAR_TOP，第二种无法为Activity指定singleInstance。
5)TaskAffinity和allowTaskReparenting配合使用，用于应用间Activity的跳转复用。**这里准备写个Demo**
6)查看adb中Activity的命令：adb shell dumpsys activity
### 1.3 IntentFilter的匹配原则
1)隐式调用和显示调用
2)隐式调用，一个过滤列表中的action、category、data可以有多个，只有一个Intent同时匹配action类别、category类别、data类别才算完全匹配，只有完全匹配才可以成功启动目标Activity
3)一个Activity可以有多个intent-filter，一个Intent只要能匹配任何一组intent-filter即科成功启动对应的Activity。
4)action的匹配原则：action是一个字符串，intent中的action和过滤规则中的任何一个相同则算匹配成功。intent中没有指定action则匹配失败。总结：action的匹配要求intent中的action存在且必须和过滤规则中的其中一个action相同。
5)category的匹配原则：如果没有，也可匹配成功，但需要在过滤规则中加上“android.intent.category.DEFAULT”,原因：系统在调用startActivity或者startActivityForResult中会默认给intent加上“android.intent.category.DEFAULT”这个category；如果有，不论几个，都必须是过滤规则中已经定义了的。
6)data的匹配规则：

```
<data 
android:scheme="string"
android:host="string"
android:port="string"
android:path="string"
android:pathPattern="string"
android:pathPrefix="string"
android:mimeTyoe="string"
/>
```

scheme:URI的模式，比如http、file、content等，如果没有指定scheme，则整个URI的其他参数无效，URI也就无效。
Host:URI的主机名，比如www.baidu.com,如果没有指定scheme，则整个URI的其他参数无效，URI也就无效。
Port:URI中的端口号，需要前两个参数指定的时候才有效。
Path、pathPattern、pathPrefix表示路径信息。

需要调用setDataAndType方法设置data
过滤规则可以不写URI，默认值为content和file,所以intent需要在没指定URI的情况下设为content或者file.
