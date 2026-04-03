---
title: 利用Fragment实现仿微信Tab效果（Fragment的初步学习）
date: 2017-09-26 00:28:24+08:00
categories: ["Android基础"]
source_name: "利用Fragment实现仿微信Tab效果（Fragment的初步学习）"
jianshu_views: 904
jianshu_url: "https://www.jianshu.com/p/26c3c5769281"
---
  在前一次利用ViewPager实现仿微信Tab效果的后，又学习了利用Fragment实现该效果，刚好是对Fragment的一次学习理解。


效果图就不展示了，和ViewPager的界面类似，唯一的缺点就是，利用单纯的Fragment无法实现像ViewPager一样的左右滑切换。就当做一次对Fragment的理解学习吧。
这个Demo的难点总结：
1.Fragment的理解与使用。
2.FragmentTransaction与Fragment生命周期的关系。
3.FragmentTransaction中不同操作的区别。（此处遇到问题！）


接下来来详细阐述一下以上两点：
一、Fragment的理解使用。
原来一直都是在书上看完了Fragment的使用，只是知道Fragment的是用来在一个Activity中便于实现大量控件与事件的分类处理。利用这次机会刚好初步学习了一下Fragment的使用与理解。
http://blog.csdn.net/lmj623565791/article/details/37970961这篇大神的博客已经很详细的讲解了有关Fragment的理解与使用。看完过后知道了Fragment的基础使用方式两种：
（1）静态的使用Fragment
（2）动态的使用Fragment。
而本例中使用的就是第二种使用方式，利用FragmentTransaction实现动态使用Fragment。一开始还不理解动态的使用的含义，看完那篇博客后，了解到，就是利用FragmentManager在Activity中操作Fragment。
也就是说在Activity中动态的管理Fragment。具体方式步骤如下：
1.定义自己的mFragment继承Fragment（此处有一个要点就是：包名要一致，如果导入的是android.app.Fragment后面导入的都要是app下的包例如android.app.FragmentManager；而如果导入的是android.support.v4.app.Fragment，后面要一致导入v4包，不然会产生错误）。重写onCreateView方法：如下

```
@Override
public View onCreateView(LayoutInflater inflater, ViewGroup container,
		Bundle savedInstanceState) {
	Log.i("Tag", "onCreateView");
	// TODO Auto-generated method stub
	return inflater.inflate(R.layout.tab1, container, false);
}
```
2.获取FragmentManage，利用getFragmentManager()（v4中，getSupportFragmentManager）得到FragmentManage。

```
FragmentManager fm = getFragmentManager();
```
3.开启一个事务FragmentTransaction。

```
FragmentTransaction transaction = fm.beginTransaction();
```
4.调用add(),show(),remove(),replace(),hide()等相关操作实现所需功能。



代码如下：
  MainActivity.java
```
package com.example.fragmenttab;


import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.Fragment;
import android.app.FragmentManager;
import android.app.FragmentTransaction;
import android.os.Bundle;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.Window;
import android.widget.ImageView;
import android.widget.LinearLayout;

public class MainActivity extends Activity implements OnClickListener{
	private LinearLayout l1, l2, l3, l4;
	private ImageView pic1, pic2, pic3, pic4;
	private Fragment f1,f2,f3,f4;
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		requestWindowFeature(Window.FEATURE_NO_TITLE);
		setContentView(R.layout.activity_main);
		initView();
		initEvent();
		setSelect(0);
	}
	private void initEvent() {
		// TODO Auto-generated method stub
		l1.setOnClickListener(this);
		l2.setOnClickListener(this);
		l3.setOnClickListener(this);
		l4.setOnClickListener(this);
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
	}
	private void setSelect(int i){
		FragmentManager fm = getFragmentManager();
		FragmentTransaction transaction = fm.beginTransaction();
		hideFragment(transaction);
		switch (i) {
		case 0:
			if(f1 == null){
				f1 = new OneFragment();
				transaction.add(R.id.content, f1);
			}else{
				transaction.show(f1);
			}
			pic1.setImageResource(R.drawable.tab_weixin_pressed);
			break;
		case 1:
			if(f2 == null){
				f2 = new SecondFragment();
				transaction.add(R.id.content, f2);
			}else{
				transaction.show(f2);
			}
			pic2.setImageResource(R.drawable.tab_find_frd_pressed);
			break;
		case 2:
			if(f3 == null){
				f3 = new ThirdFragment();
				transaction.add(R.id.content, f3);
			}else{
				transaction.show(f3);
			}
			pic3.setImageResource(R.drawable.tab_address_pressed);
			break;
		case 3:
			if(f4== null){
				f4 = new FourthFragment();
				transaction.add(R.id.content, f4);
			}else{
				transaction.show(f4);
			}
			pic4.setImageResource(R.drawable.tab_settings_pressed);
			break;
		}
		transaction.commit();
	}
	private void hideFragment(FragmentTransaction transaction) {
		//隐藏所有Fragment
		if(f1 != null){
			transaction.hide(f1);
		}
		if(f2 != null){
			transaction.hide(f2);
		}
		if(f3 != null){
			transaction.hide(f3);
		}
		if(f4 != null){
			transaction.hide(f4);
		}
	}
	@Override
	public void onClick(View v) {
		resetImage();
		switch (v.getId()) {
		case R.id.lin1:
			setSelect(0);
			break;
		case R.id.lin2:
			setSelect(1);
			break;
		case R.id.lin3:
			setSelect(2);
			break;
		case R.id.lin4:
			setSelect(3);
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
OneFragment.java
```
package com.example.fragmenttab;


import android.app.Activity;
import android.app.Fragment;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

public class OneFragment extends Fragment {
@Override
public View onCreateView(LayoutInflater inflater, ViewGroup container,
		Bundle savedInstanceState) {
	Log.i("Tag", "onCreateView");
	// TODO Auto-generated method stub
	return inflater.inflate(R.layout.tab1, container, false);
}
}
```
activity_main.xml

```
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">
    <include layout="@layout/top" />
    <FrameLayout 
        android:id="@+id/content"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1"></FrameLayout>
    <include layout="@layout/bottom" />
</LinearLayout>
```
其他界面和前一个例子相同。


以上就是这次所有的总结，**这样就结束了吗？NO!NO!NO!**
在这个例子中一个无意的操作引发了一个自己无法解决的问题。
问题如下：
在这个例子中原理就是，每次点击之前都回执行hideFragment（）方法用户将所有的Fragment利用transaction.hide()方法隐藏掉，然后再二次点击时利用show()方法显示**。这些看似很基础，但是我一开始写的时候，不小心将hide()方法写成了remove()方法，这时候问题来了！！！运行效果是第一次点击都是好的，但是第二次点击后界面就为空白了。**
问题原因：
设置断点调试，发现原因很简单，执行remove后，二次点击在这一步：	

```
if(f1 == null){
				f1 = new OneFragment();
				transaction.add(R.id.content, f1);
			}else{
				transaction.show(f1);
			}
```
这时f1不为null，执行show()方法，而f1已经被remove了所以show是空白。
但是看似简单的问题原因，仔细一想，FragmentTransaction的remove方法定义是**从Activity中移除一个Fragment，如果被移除的Fragment没有添加到回退栈（回退栈后面会详细说），这个Fragment实例将会被销毁。**
销毁？对，你没有看错，销毁后不应该为null吗？为什么判断的时候不是null哪？纠结啊，看了Fragment的源码和FragmentTransaction的源码还是无法理解原因，Tag了Fragment的生命周期发现，remove后确实执行了onDetach()方法，也就是说该Fragment已经的确被销毁了，但是判null的时候不是null,纠结啊！！！希望有大神能解决这个问题啊。我自己也在寻找原因，希望下次博客能够发出解决贴吧！
