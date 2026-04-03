---
title: "Android增强现实（一）-AR的三种方式(展示篇)"
date: 2016-03-06 08:00:00 +0800
categories: ["Android自定义View"]
source_name: "Android增强现实（一）-AR的三种方式(展示篇)"
---
>有一段时间没写博客了，事情比较多，博客进度有点跟不上了

>1.[Android增强现实（一）-AR的三种方式(展示篇)](https://www.jianshu.com/p/e6a51f4439df)
>2.[Android增强现实（二）-支持拖拽控制进度和伸缩的VrGifView](https://www.jianshu.com/p/abd1772cb061)
>3.[Android增强现实（三）-3D模型展示器](https://www.jianshu.com/p/f1708d5277ad)

这段时间研究了一段时间Android端增强现实的方式，总体分为两个大类：全景图和3D模型。
于是基于这两种形式，以三种方式来展示增强现实：
1.全景360°GIF，支持拖动，缩放。
2.展示3D模型
3.Google官方展示全景图探究

这篇博客就主要以展示为主吧，放上具体的效果Demo和使用方式，后面会有具体博客用于分析实现方式和技术难点的。
>github地址：[VRShow](https://github.com/sdfdzx/VRShow "VRShow")
求个star，给点鼓励~

**使用方式：**
1.Add it in your root build.gradle at the end of repositories:

	allprojects {
		repositories {
			...
			maven { url 'https://jitpack.io' }
		}
	}
Step 2. Add the dependency

	dependencies {
	       compile 'com.github.sdfdzx:VRShow:v1.0.2'
	}
### 1.全景360°GIF图
大家应该在京东和淘宝上见过这种效果吧：
![京东 ](http://upload-images.jianshu.io/upload_images/7866586-3e60f0d9040c9e28.gif?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

**我的实现效果图：**
![VrGifView](http://upload-images.jianshu.io/upload_images/7866586-ef7c6eb4e2392371.gif?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

**功能：**
>1.支持单指拖拽
>2.支持双指缩放
>3.支持触摸响应速度模式：LOW,NORMAL,FAST

**使用方式：**
 XML and Java
```
<com.study.xuan.gifshow.widget.VrGifView
        android:id="@+id/gif"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:src="@drawable/demo"
        />


public class GifActivity extends AppCompatActivity {
    private VrGifView mGif;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_gif);
        mGif = (VrGifView) findViewById(R.id.gif);
        mGif.setTouch(true);//是否 可触摸
        mGif.setDrag(true);//是否可拖拽
        mGif.setScale(false);//是否可伸缩
        mGif.setMoveMode(VrGifView.MODE_FAST);//触摸响应速度
    }
}
```


### 2.展示3D模型
在京东上见到过这样效果的商品：
![京东3D](http://upload-images.jianshu.io/upload_images/7866586-39948650ce4759f4.gif?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
**我的实现效果图：**

![3D模型](http://upload-images.jianshu.io/upload_images/7866586-d5490c38cdcd32b1.gif?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)


**功能：**
>1.异步读取STL格式的3D文件
>2.支持进度回调
>3.支持单指拖动
>4.支持双指缩放
>5.支持陀螺仪传感器

**使用方式：**
XML and Java
```
<com.study.xuan.stlshow.widget.STLView
        android:id="@+id/stl"
        android:layout_width="match_parent"
        android:layout_height="match_parent"/>


        STLViewBuilder.init(mStl).Assets(this, "bai.stl").build();
        mStl.setTouch(true);
        mStl.setScale(true);
        mStl.setRotate(true);
        mStl.setSensor(true);
		mStl.setOnReadCallBack(new OnReadCallBack() {
            @Override
            public void onStart() {}
            @Override
            public void onReading(int cur, int total) {}
            @Override
            public void onFinish() {}
        });
```

### 3.Google的全景图
官方Demmo地址：[https://github.com/googlevr/gvr-android-sdk](https://github.com/googlevr/gvr-android-sdk)

这篇博客主要展示一下功能吧，下面应该会分三篇博客，分别介绍前两种实现过程中的难点和技术点，和第三种也就是Google官方展示全景图，从源码角度看一下Google官方的实现方式。
