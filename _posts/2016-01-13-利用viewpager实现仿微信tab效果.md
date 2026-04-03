---
title: 利用ViewPager实现仿微信Tab效果
date: 2017-09-26 00:28:18+08:00
categories: ["Android基础"]
source_name: "利用ViewPager实现仿微信Tab效果"
jianshu_views: 381
jianshu_url: "https://www.jianshu.com/p/9392a773bd11"
---
学习了利用ViewPaper实现仿微信Tab界面的效果，写一篇博客总结一下，就当做笔记了~

总体实现需要以下几个步骤：

1.编写主体界面（顶部布局+viewpager+底部布局）
![效果](/assets/img/posts/4b0b223e6974453d.webp)
利用ViewPager实现仿微信Tab效果


2.定义PagerAdapter，为Viewpager绑定Adapter。

3.定义触发事件，例如点击tab更改ViewPager,切换ViewPager更改tab。

 接下来总结一下编写中遇到的问题：

一、bottom布局不显示

主体界面是由三个xml文件构成：activity_main.xml,top.xml,bottom.xml

，其中top设置的父布局高度为55dp，bottom设置的父布局高度为55dp。

activity_main中的Viewpager高度一开始设置的为match_parent。这时问题就出现了，这样bottom布局就不会显示。由于Viewpager的高度设为match_parent所以，在top的55dp占完后，其余布局的空间都被Viewpager占据了，所以bottom没有空间显示了。

解决方式：将Viewpager的高度设为0dp，将layout_weight=1；这样就能正常显示了。

解决原因是：LinearLayout的layout_weight的原理是先分配布局，在将剩余空间按比例分配。具体关于Layout_weight属性过两天再写一篇详细博客。

二、关于LayoutInflater的理解。

经常使用LayoutInflater，但一直没有理解这个是干什么的，上网查询了一下，才知道

具体作用：对于一个没有被载入或者想要动态载入的界面，都需要使用LayoutInflater.inflate()来载入；所以初始化一个LayoutInflater对象，初始化时有三种方法：

1. LayoutInflater inflater = getLayoutInflater();//调用Activity的getLayoutInflater() 

2. LayoutInflater inflater = LayoutInflater.from(context);  

3. LayoutInflater inflater =  (LayoutInflater)context.getSystemService

                              (Context.LAYOUT_INFLATER_SERVICE);

查看源码会发现最终调用的都是第三种，而getSystemService()是Android很重要的一个API，它是Activity的一个方法，根据传入的NAME来取得对应的Object，然后转换成相应的服务对象。其中LAYOUT_INFLATER_SERVICE取得xml里定义的view。所以通过inflater.inflate（）来讲三个tab的xml文件转换成view，再传入list<>数据集。

三、对PagerAdapter构造的理解。

定义一个PagerAdapter系统会强制重写两个函数getCount()，isViewFromObject(View arg0, Object arg1)，其中getCount（）是用来定义tab数量所以：

```
public int getCount() {

return list.size();

}
```

而isViewFromObject(View arg0, Object arg1)上网搜了一下大概了解了一下没有理解网上表达的意思。只知道大多是重写方式是：

```
public boolean isViewFromObject(View arg0, Object arg1) {

return arg0 == arg1;

}
```

在此基础上还要重写两个函数。instantiateItem(ViewGroup container, int position)，

destroyItem(ViewGroup container, int position,

Object object)。一个是创建指定位置的页面视图，一个用于移除item时调用。 viewpage一般都会缓冲3个item，即一开始就会调用3次instantiateItem, 当向右滑动，到第3页时，第1页的item会被调用到destroyitem。

所以重写：

```
public void destroyItem(ViewGroup container, int position,

Object object) {

container.removeView(list.get(position));

}

public Object instantiateItem(ViewGroup container, int position) {

View view = list.get(position);

container.addView(view);

return view;

}
```

四、监听事件

此例中有个监听事件：1.底部Layout的点击事件（切换图片），2.ViewPager的滑动监听事件（切换图片）。

至此此例中的要点都分析完成，其他的只需将代码实现即可。

代码奉上：

```
MainActivity.java

package com.example.viewpapertab;

import java.util.ArrayList;

import java.util.List;

import android.app.Activity;

import android.os.Bundle;

import android.support.v4.view.PagerAdapter;

import android.support.v4.view.ViewPager;

import android.support.v4.view.ViewPager.OnPageChangeListener;

import android.view.LayoutInflater;

import android.view.View;

import android.view.View.OnClickListener;

import android.view.ViewGroup;

import android.view.Window;

import android.widget.ImageView;

import android.widget.LinearLayout;

public class MainActivity extends Activity implements OnClickListener {

private LinearLayout l1, l2, l3, l4;

private ImageView pic1, pic2, pic3, pic4;

private ViewPager viewpager;

private PagerAdapter madapter;

private List list = new ArrayList();

@Override

protected void onCreate(Bundle savedInstanceState) {

super.onCreate(savedInstanceState);

requestWindowFeature(Window.FEATURE_NO_TITLE);

setContentView(R.layout.activity_main);

initView();

initEvent();

}

private void initEvent() {

// TODO Auto-generated method stub

l1.setOnClickListener(this);

l2.setOnClickListener(this);

l3.setOnClickListener(this);

l4.setOnClickListener(this);

viewpager.setOnPageChangeListener(new OnPageChangeListener() {

@Override

public void onPageSelected(int arg0) {

// TODO Auto-generated method stub

int currentItem = viewpager.getCurrentItem();

resetImage();

switch (currentItem) {

case 0:

pic1.setImageResource(R.drawable.tab_weixin_pressed);

break;

case 1:

pic2.setImageResource(R.drawable.tab_find_frd_pressed);

break;

case 2:

pic3.setImageResource(R.drawable.tab_address_pressed);

break;

case 3:

pic4.setImageResource(R.drawable.tab_settings_pressed);

break;

}

}

@Override

public void onPageScrolled(int arg0, float arg1, int arg2) {

// TODO Auto-generated method stub

}

@Override

public void onPageScrollStateChanged(int arg0) {

// TODO Auto-generated method stub

}

});

}

private void initView() {

// TODO Auto-generated method stub

l1 = (LinearLayout) findViewById(R.id.lin1);

l2 = (LinearLayout) findViewById(R.id.lin2);

l3 = (LinearLayout) findViewById(R.id.lin3);

l4 = (LinearLayout) findViewById(R.id.lin4);

pic1 = (ImageView) findViewById(R.id.pic1);

pic2 = (ImageView) findViewById(R.id.pic2);

pic3 = (ImageView) findViewById(R.id.pic3);

pic4 = (ImageView) findViewById(R.id.pic4);

viewpager = (ViewPager) findViewById(R.id.viewpager);

LayoutInflater inflater = LayoutInflater.from(this);

View tab1 = inflater.inflate(R.layout.tab1, null);

View tab2 = inflater.inflate(R.layout.tab2, null);

View tab3 = inflater.inflate(R.layout.tab3, null);

View tab4 = inflater.inflate(R.layout.tab4, null);

list.add(tab1);

list.add(tab2);

list.add(tab3);

list.add(tab4);

madapter = new PagerAdapter() {

@Override

public void destroyItem(ViewGroup container, int position,

Object object) {

container.removeView(list.get(position));

}

@Override

public Object instantiateItem(ViewGroup container, int position) {

View view = list.get(position);

container.addView(view);

return view;

}

@Override

public boolean isViewFromObject(View arg0, Object arg1) {

return arg0 == arg1;

}

@Override

public int getCount() {

return list.size();

}

};

viewpager.setAdapter(madapter);

}

@Override

public void onClick(View v) {

// TODO Auto-generated method stub

resetImage();

switch (v.getId()) {

case R.id.lin1:

viewpager.setCurrentItem(0);

pic1.setImageResource(R.drawable.tab_weixin_pressed);

break;

case R.id.lin2:

viewpager.setCurrentItem(1);

pic2.setImageResource(R.drawable.tab_find_frd_pressed);

break;

case R.id.lin3:

viewpager.setCurrentItem(2);

pic3.setImageResource(R.drawable.tab_address_pressed);

break;

case R.id.lin4:

viewpager.setCurrentItem(3);

pic4.setImageResource(R.drawable.tab_settings_pressed);

break;

}

}

private void resetImage() {

// 重置所有图片

pic1.setImageResource(R.drawable.tab_weixin_normal);

pic2.setImageResource(R.drawable.tab_find_frd_normal);

pic3.setImageResource(R.drawable.tab_address_normal);

pic4.setImageResource(R.drawable.tab_settings_normal);

}

}
```

```
activity_main.xml
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">
    <include layout="@layout/top" />
    <android.support.v4.view.ViewPager
        android:id="@+id/viewpager"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1"
        >       
        </android.support.v4.view.ViewPager>
    <include layout="@layout/bottom" />"
</LinearLayout>
```

```
top.xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="55dp"
    android:gravity="center"
    android:background="@drawable/title_bar"
    android:orientation="vertical" >
    <TextView 
        android:layout_height="match_parent"
        android:layout_width="wrap_content"
        android:text="微信"
        android:gravity="center"
        android:textSize="25sp"
        android:textColor="#ffffff"
        android:textStyle="bold"/>
</LinearLayout>
```

bottom.xml


```
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="55dp"
    android:background="@drawable/bottom_bar"
    android:orientation="horizontal" >
    <LinearLayout
        android:id="@+id/lin1"
        android:layout_width="0dp"
        android:layout_height="match_parent"
        android:layout_weight="1"
        android:gravity="center"
        android:orientation="vertical" >
        <ImageView
            android:id="@+id/pic1"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:src="@drawable/tab_weixin_pressed" />
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="微信"
            android:textColor="#ffffff"/>
    </LinearLayout>
    <LinearLayout
        android:id="@+id/lin2"
        android:layout_width="0dp"
        android:layout_height="match_parent"
        android:layout_weight="1"
        android:gravity="center"
        android:orientation="vertical" >
        <ImageView
            android:id="@+id/pic2"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:src="@drawable/tab_find_frd_normal" />
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="朋友"
            android:textColor="#ffffff"/>
    </LinearLayout>
    <LinearLayout
        android:id="@+id/lin3"
        android:layout_width="0dp"
        android:layout_height="match_parent"
        android:layout_weight="1"
        android:gravity="center"
        android:orientation="vertical" >
        <ImageView
            android:id="@+id/pic3"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:src="@drawable/tab_address_normal" />
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="通讯录"
            android:textColor="#ffffff" />
    </LinearLayout>
    <LinearLayout
        android:id="@+id/lin4"
        android:layout_width="0dp"
        android:layout_height="match_parent"
        android:layout_weight="1"
        android:gravity="center"
        android:orientation="vertical" >
        <ImageView
            android:id="@+id/pic4"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:src="@drawable/tab_settings_normal" />
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="设置"
            android:textColor="#ffffff" />
    </LinearLayout>
</LinearLayout>
```

tab1.xml(四个tab界面文件就文字不同，这里就放一个）

```
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:gravity="center"
    android:orientation="vertical" >
   <TextView 
       android:text="One Page"
       android:textStyle="bold"
       android:textSize="25sp"
       android:layout_width="wrap_content"
       android:layout_height="wrap_content"
       />
</LinearLayout>
```

好了，以上就是这次学习的感受，本人接触android不就，发博客当做笔记用于学习巩固，如果有问题，大家可以提出，一起互相学习！
