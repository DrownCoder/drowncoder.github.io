最近看到了TaskAffinity和allowTaskReparenting配个使用，就写了个Demo,测试了一下
情景：
应用1（tabflowlayout）：MainActivityA
应用2(autofittextview)：MainActivityB(Main入口)，TestActivity
##### 结果
    >启动应用1
    >MainActivityA点击跳转->TestActivity（应用间的隐式跳转）
    >按下Home键
    >启动应用2（显示的是TestActivity）
    >按下返回键（显示的是MainActivityB）

其中要学习的地方有两点：
#### 1.隐式跳转
对应的action，category，data属性，这里要注意的是category属性
category的匹配原则是：
**1.如果没有写addCategory(),也可以匹配成功**
前提：要在xml中配置"android.intent.category.DEFAULT";
原因：在startActivity和startActivityForResult中会默认添加addCategory()属性

**2.如果写了addCategory()，都必须是在xml中的其中一个相同**

**3.无论写没写addCategory()方法，只要是隐式跳转，都需要在xml中配置"android.intent.category.DEFAULT"**
原因：在startActivity和startActivityForResult中会默认添加addCategory()属性

#### 2.activity栈分析
对应上面的过程，我通过**adb shell dumpsys activity**命令查看当前的activity和activity栈情况

##### >启动应用1
![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-cf908fc9cacbac7b?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
可以看到，这时只有应用1的MainActivity存在
##### >点击跳转到TestActivity
![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-59182c74c8c6f8b2?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-ef43b09666195c3c?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
可以看到，这时应用2的TestActivity存在于应用1的Activity栈中，这时存在两个Activity，分别是TestActivity和MainActivityA,都存在于应用1的默认的Activity栈中。
##### >按下Home键
![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-82b5ef31e993da10?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)


可以看到这时和上面的情况并没有什么实质性变化
##### >启动应用2
![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-68947a33c5040bbd?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-455e890e54baaba5?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

**这时候allowTaskReparenting=true的效果就出来了，本来应该展示的是应用2的Main入口Activity，也就是MainActivityB，但是这时刚才在应用1的Activity栈中的TestActivity就跑到了应用2的Activity栈中，并且位于栈顶，而应用1的Activity栈中只存在了MainAcitivityA**
##### >按下返回键
![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-7a0e257df1ecd875?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-a7f071809e15c7f0?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

**一开始我以为这时按下返回键会直接回到主界面，但是没想到会启动MainActivityB，上一步骤也看到了启动应用2后，虽然TestActivity移动到了栈顶，但其实MainActivityB还是存在于栈中的，作为Main入口，所以按下返回键，就会启动MainActivityB,但是我通过生命周期发现，其实这时MainActivityB才开始从onCreate开始走生命周期**
